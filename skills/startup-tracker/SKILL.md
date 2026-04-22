---
name: startup-tracker
description: |
  Monitor startups for weekly signals — funding rounds, product launches, partnerships, leadership hires,
  and other notable developments — across news, websites, and social media.
  监控初创公司动态——融资轮次、产品发布、合作伙伴、高管招聘等新闻和社交媒体信号。
  Designed for VC investors, analysts, or researchers tracking early-stage companies.

  **ACTIVELY use this skill whenever the user mentions:**
  "run startup tracker", "check startup updates", "monitor companies", "追踪公司动态",
  "/startup-tracker", "startup weekly", "监控公司", "startup监控", "startup weekly",
  generating startup monitoring reports, "追踪新创公司", "监控新创", or anything similar.

  If the user's request involves tracking, monitoring, or reporting on multiple companies'
  recent activity, this skill should be used immediately — don't wait to be asked twice.
---

# Startup Tracker — 执行指南

## 架构概览

```
Agent (你) — 编排 4 个数据源 + 去重 + 报告生成
├── ① 新闻搜索:  tracker.py → Tavily CLI
├── ② 网站监控:  tracker.py → Crawl4AI / Firecrawl
├── ③ Twitter:   Agent → Apify Actor (多 Actor 自动降级)
├── ④ LinkedIn:  Agent → Apify Actor
└── 合并去重 → state/new_items.json → Markdown 报告
```

关键设计决策：`tracker.py` 只处理新闻和网站（①②）；社交媒体（③④）由 Agent 直接调用 Apify Actor 完成，以便实现**多 Actor 轮询降级**——主 Actor 失败时自动尝试备选。

---

## 技术栈与环境

| 组件 | 用途 | 安装 | 必须 |
|------|------|------|------|
| `tavily-python` | 新闻/融资搜索 | `pip install tavily-python` + API key | 是 |
| `crawl4ai` | 网站变更检测 | `pip install crawl4ai`（首次需下载 ~100MB 模型） | 推荐 |
| `firecrawl` | 网站监控备选（云端API） | 仅 API key，注册 https://www.firecrawl.dev | 推荐 |
| `@apify/mcpc` | 运行 Apify Actor | `npm install -g @apify/mcpc` | 社交媒体 |

**网站监控选型**：
- Crawl4AI：免费、本地运行、无次数限制，但首次启动慢；**长期运行首选**
- Firecrawl：云端运行、安装即走，一次性免费额度用完需要付费

**网站监控注意**：
- 默认仅监控 `website` 字段指定的首页 URL，但首页变更频率低
- **强烈建议在 `monitor_urls` 中同时加入 `/blog` 和 `/news` 页面 URL**，否则可能遗漏大部分产品公告和融资新闻
- `monitor_urls` 需用户手动提供，因为 AI 自动查找博客/新闻页的准确率不稳定

**API Keys 优先级**（从高到低）：
1. 命令行参数（`--tavily-key`, `--apify-key`）
2. `.env` 环境变量（`TAVILY_API_KEY`, `APIFY_TOKEN`）
3. `config.json` → `api_keys` 字段

**Crawl4AI 首次运行注意**：首次只会建立网站基线 hash，不会产生变更告警。变更检测从第二次运行开始。

---

## 配置文件详解

### config.json 示例

```json
{
  "companies": [
    {
      "name": "公司名",
      "website": "https://...",
      "monitor_urls": ["https://...", "https://.../blog", "https://.../news"],
      "x_handle": "Twitter 用户名（不含 @）",
      "linkedin_url": "https://www.linkedin.com/company/...",
      "priority": "high",
      "exclude_keywords": []
    }
  ],
  "data_sources": {"news": "tavily", "website": "crawl4ai", "twitter": true, "linkedin": true},
  "website_monitor": {"engine": "crawl4ai", "max_content_chars": 2000, "use_article_signature": true},
  "monitor_interval_days": 14,
  "tavily": {
    "search_days_back": 7,
    "max_results_per_company": 15,
    "search_query": "funding OR raised OR acquired OR acquisition OR merger OR IPO OR partnership OR launch OR expansion OR investment OR product OR hiring or series",
    "major_keywords": ["funding","raises","raised","million","acquired","acquisition","IPO","series A","series B","series C","seed round","partnership","launch","shut down","layoff","appointed CEO","appointed CTO"]
  },
  "apify": {
    "twitter_actor_id": "kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest",
    "twitter_actor_fallbacks": [
      "parseforge/x-com-scraper",
      "logical_scrapers/x-twitter-user-profile-tweets-scraper"
    ],
    "linkedin_actor_id": "supreme_coder/linkedin-post",
    "linkedin_actor_fallbacks": [
      "apify/linkedin-post-scraper"
    ],
    "max_tweets_per_run": 15,
    "max_linkedin_posts_per_run": 15,
    "poll_interval_sec": 5,
    "max_poll_sec": 120
  },
  "api_keys": {"tavily": "tvly-...", "apify": "apify_api_...", "firecrawl": ""}
}
```

**配置路径**：`config.json` 和 `tracker.py` 都在 skill 目录下。`state/new_items.json` 存储运行结果。

---

## 首次配置（config.json 不存在时）

当用户首次使用时，Agent 需引导完成以下配置。

**为什么需要手动提供链接**：
1. AI 领域同名公司极多（叫 "Nova AI" 的可能有十几家），自动搜索容易张冠李戴
2. AI 自动查找博客/新闻页的准确率不稳定，手动提供可确保监控的是正确公司

**Step 1：获取公司列表**
向用户询问要监控的公司，至少需要公司名和官网。可选：Twitter handle、LinkedIn URL。用自然的对话语气，例如"先跟我说说你想监控哪些公司？"

**Step 2：验证链接**
用 WebSearch 验证每个公司的官网、Twitter、LinkedIn 链接是否正确可访问，展示给用户确认。确认后再继续。

**Step 3：配置 API Keys**
- Tavily API（必需）：注册 https://tavily.com，免费 1000 次/月
- Apify Token（社交媒体需要）：注册 https://console.apify.com/account/integrations
- 将 key 写入 skill 目录下的 `.env` 文件

**中国大陆用户注意**：访问 `api.apify.com` 可能受限，需使用代理或 VPN。

**Step 4：确认并生成 config.json**
将整理好的配置展示给用户确认，然后保存。

**Step 5：运行首次监控**
按下方执行流程运行。如果 0 条动态，用轻松语气解释原因（公司太早期/监控窗口短/静默期都属正常）。

**主动询问**：是否需要设置定时运行。告知用户 skill 本身无内置定时功能，可通过 cron/OpenClaw/CI 等外部调度定期触发。

---

## 运行监控：5 步执行流程

### Phase 0：前置检查
确认 config.json 存在且列表非空，Tavily API Key 和 Apify Token 有效，Node.js 和 `@apify/mcpc` 已安装。

### Phase 1：新闻搜索 + 网站监控

运行 `tracker.py`（在 skill 目录下执行 `python tracker.py`）。结果自动写入 `state/new_items.json`。

**可选参数**：`python tracker.py --days N` 可单次覆盖搜索天数，不修改配置文件。默认 14 天，常用值：1（日报）、7（周报）、14、30（月报）。

### Phase 2：Twitter/X 监控（Agent 执行）

**核心策略：多 Actor 自动降级**。X 反爬机制强，单个 Actor 经常失效。Agent 必须按以下优先级依次尝试，直到某个 Actor 返回有效结果（非空数组）或全部失败。

**Actor 优先级队列**（从 `config.json` 的 `apify.twitter_actor_id` 和 `apify.twitter_actor_fallbacks` 读取）：

1. **主 Actor**: `kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest`
2. **备选 1**: `parseforge/x-com-scraper`
3. **备选 2**: `logical_scrapers/x-twitter-user-profile-tweets-scraper`

**Agent 执行逻辑（对每家公司）**：

```
for actor_id in [主 Actor, 备选 1, 备选 2]:
    调用 Actor
    如果返回非空数组 → 使用该结果，跳出循环
    如果返回空数组或失败 → 记录原因，继续下一个 Actor
如果全部失败 → 记录警告，该公司 Twitter 数据源标记为跳过
```

**调用方式**（使用 apify-ultimate-scraper skill 或直接 MCP）：

```bash
export APIFY_TOKEN=<token>
node --env-file=.env <apify-skill-dir>/reference/scripts/run_actor.js \
  --actor "<actor_id>" \
  --input '<input_json>' \
  --timeout 120
```

**不同 Actor 的输入参数差异**：

| Actor | 用户名字段 | 数量字段 | 示例输入 |
|-------|-----------|---------|---------|
| `kaitoeasyapi/...` | `usernames` (数组) | `maxItems` | `{"usernames": ["<handle>"], "maxItems": 15}` |
| `parseforge/...` | `usernames` (数组) | `maxItems` | `{"usernames": ["<handle>"], "maxItems": 15}` |
| `logical_scrapers/...` | `username` (数组) | `maxTweets` | `{"username": ["<handle>"], "maxTweets": 15}` |

- `usernames` / `username` 都是**数组**，元素不含 `@`
- 如果某个 Actor 在 Apify Console 中显示持续失败，可将其从 `twitter_actor_fallbacks` 中移除

**输出字段归一化**（不同 Actor 返回的字段名不同，统一映射到以下字段）：
- 唯一标识：`id` / `tweetId` → `id`
- 内容：`text` / `fullText` / `content` → `text`
- 链接：`url` / `tweetLink` / `twitterUrl` → `url`
- 发布时间：`createdAt` / `date` / `timestamp` → `createdAt`
- 互动量：`likeCount` / `likes` / `favoriteCount` → `likes`; `retweetCount` / `retweets` → `retweets`
- 是否转发：`isRetweet` / `retweeted` → `isRetweet`

### Phase 3：LinkedIn 监控（Agent 执行）

**核心策略：多 Actor 自动降级**。LinkedIn 反爬和登录墙更严，同样需要备选 Actor。

**Actor 优先级队列**：

1. **主 Actor**: `supreme_coder/linkedin-post`
2. **备选**: `apify/linkedin-post-scraper`

**Agent 执行逻辑**：与 Twitter 相同，逐个尝试直到有结果或全部失败。

```bash
export APIFY_TOKEN=<token>
node --env-file=.env <apify-skill-dir>/reference/scripts/run_actor.js \
  --actor "<actor_id>" \
  --input '{"urls": ["<linkedin_url>"], "limit": 15}' \
  --timeout 120
```

- 使用 `urls`（不是 `startUrls`），是字符串数组
- **输出字段归一化**：`urn`/`id`/`shareUrn` → `id`；`text`/`content`/`postText` → `text`；`timeSincePosted`/`postedAt`/`postedAtISO` → `timeSincePosted`（相对时间如 "3w" 需用 `tracker.py` 中的 `relative_time_to_date()` 转为 YYYY-MM-DD）；`numLikes`/`likes` → `likes`; `numShares`/`shares` → `shares`

** stdout 解析**：Actor 结果在 stdout 中，取最后一行以 `[` 开头的完整 JSON 数组。

### Phase 4：统一去重与合并（Agent 执行）

`tracker.py` 已完成 Phase 1（新闻+网站），结果已写入 `state/new_items.json` 的 `items` 数组。Agent 需要将 Phase 2（Twitter）和 Phase 3（LinkedIn）的结果追加合并到同一文件中。

每条动态统一格式：

```json
{
  "items": [{
    "company": "公司名", "source": "tavily|crawl4ai|apify_twitter|apify_linkedin",
    "title": "标题", "url": "链接", "snippet": "摘要(前300字符)",
    "published_date": "YYYY-MM-DD", "importance": "MAJOR|NORMAL"
  }],
  "run_timestamp": "ISO-8601",
  "summary": {"total": N, "by_company": {}, "by_source": {}, "by_importance": {}}
}
```

**去重规则**：
1. URL 去重：相同 URL 只保留一次
2. 内容去重：同一天同一公司标题相似度 > 80% 合并为一条
3. 跨源优先级：同一事件多源出现时，保留信息最丰富的（MAJOR > NORMAL），标题后标注合并标签如 `[Tavily + Twitter]`

### Phase 5：生成报告

读取 `state/new_items.json` 生成报告。

**交互语气**：展示报告时开头用"这周帮你跑了下监控，情况如下～"这类自然开场。MAJOR 逐条详细展示，NORMAL 整合为摘要。语气亲切自然，像和朋友分享发现，别用冰冷机械的汇报口吻。

报告同时做两件事：
1. 保存完整 MD 文件到 `<skill>/reports/report_YYYY-MM-DD.md`
2. 在对话中向用户展示精要摘要

---

## Agent 过滤与分类指南

### 直接过滤（不呈现）
- 常规招聘帖（无具体职位/人数信息）
- 产品推广广告、节日祝福、日常社交
- 纯转发（isRetweet=true 且无评论）
- 会议出席预告

### MAJOR 级别（逐条展示，附加"值得关注"）
- 核心人事变动：CEO/CTO/VP 级入职或离职
- 重大产品发布：GA、重大功能更新
- 融资公告、战略合作、数据里程碑、媒体采访

### NORMAL 级别（整合为 1-2 段自然语言"本周信号摘要"）
- 博客文章、技术分享、具体 JD 的招聘帖、产品迭代、一般社交媒体帖子

同一公司所有 NORMAL 内容**必须整合为一段自然语言摘要**，禁止逐条罗列。

---

## 报告模板

```markdown
# Startup Tracker — 信号报告
**报告日期**: YYYY-MM-DD | **监控公司**: N 家 | **数据源**: Tavily | Crawl4AI | Apify Twitter | Apify LinkedIn | **时间范围**: 过去 N 天

## 总览
| 公司 | 重要动态 | 常规动态 | 关键信号 |
...

## [公司A名称]
- **官网**: ... | **Twitter**: ... | **LinkedIn**: ...

### 🔴 重要动态
#### 1. [Tavily] 融资标题
- **发布日期**: YYYY-MM-DD | **来源**: TechCrunch
- **链接**: [查看详情](URL)
- **摘要**: 2-3 句总结
- **值得关注**: 为什么这件事重要（1 行）

### ⚪ 本周信号摘要
> 将本周所有 NORMAL 级别内容整合为 1-2 段自然语言摘要。

## 无动态公司
（过去 N 天内无可见信号的公司）
```

**硬性规则**：
1. MAJOR 动态必须逐条 + "值得关注"
2. NORMAL 必须整合为一段摘要，禁止罗列
3. 某数据源被跳过时报告开头注明
4. 全部无动态时注明"本周期无可见信号——可能原因：监控公司为早期阶段/监控窗口较短/公司处于静默期"

---

## 管理配置（对话式命令）

| 指令 | 操作 |
|------|------|
| "添加公司" | 搜索公司信息 → 确认 → 更新 config.json |
| "删除/修改公司" | 列出当前公司 → 选择 → 更新 |
| "查看当前配置" | 展示 config.json |
| "更新 API Key" | 获取新 key → 写入 .env |
| "切换数据源" | 启用/禁用 → 更新 data_sources |
| "修改监控周期" | 指定天数（1/3/7/14/30）→ 更新 |
| "查看状态" | 运行 `python tracker.py --validate` |
| "重置历史" | 清空 `state/` 目录 |

---

## 故障排除

| 问题 | 解决 |
|------|------|
| Tavily Key 无效 | 重新获取 key，写入 .env |
| Apify 运行失败 | 检查 token 和 `mcpc` 是否全局安装 |
| Actor 超时 | 检查 [Apify Console](https://console.apify.com/actors/runs/)，或增加 `--timeout` |
| Crawl4AI 未安装 | `pip install crawl4ai`，或跳过（仅网站监控不可用） |
| SSL 失败（中国大陆） | api.apify.com 可能受限，使用代理/VPN |

## 设计原则
1. 所有配置通过对话完成，无需手动编辑文件
2. 混合数据源：Python 脚本处理新闻/网站，Agent 直接调用 Apify Actor 处理社交媒体（Twitter 支持多 Actor 自动降级）
3. 渐进式启用：先跑基础功能，社交按需开启
4. 通过 `state/` 目录持久化已处理项，避免重复报告
5. 每个配置步骤都向用户确认
