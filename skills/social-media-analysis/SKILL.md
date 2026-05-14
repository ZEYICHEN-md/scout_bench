---
name: social-media-analysis
description: >
  使用 Apify 爬取 Twitter/X 和 Reddit 数据并进行情感分析与统计报告生成。
  当用户需要抓取 Twitter/X 推文、Reddit 帖子与评论、分析社媒情感倾向、
  生成社媒数据报告、或者提到"推特数据"、"Twitter爬虫"、"X平台数据"、
  "推文分析"、"Reddit舆情"、"Reddit评论"、"社媒监控"、"舆情分析"时，
  务必使用此 skill。
  支持自然语言输入和平台高级搜索语法，自动过滤 mock 数据，
  并发调用 DeepSeek API 进行精准情感分析（识别反讽、欲扬先抑等复杂表达），
  最终输出结构化统计报告和 Markdown 文档。
---

# Twitter/X & Reddit 社媒舆情分析 Skill

## 依赖

- `.env` 文件包含 `APIFY_TOKEN` 和 `DEEPSEEK_API_KEY`
- Node.js 20+（用于运行 bundled 脚本）
- Bundled 脚本：
  - `scripts/run_actor.js` — 执行 Apify actor 爬取（通用于 Twitter/X 和 Reddit）
  - `scripts/sentiment_analysis.js` — 批量 DeepSeek 情感分析
  - `scripts/cluster_voices.js` — 主题聚类并提取好差评核心声音代表
  - `references/report_template.md` — Twitter/X 报告 Markdown 模板
  - `references/reddit_report_template.md` — Reddit 报告 Markdown 模板
  - `references/sentiment_prompt.md` — 情感分析详细 prompt（供脚本内置参考）

---

## 平台一：Twitter/X

### Twitter/X 核心 Actor

**主 Actor：** `kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest`
- 价格：$0.00025/条
- 支持完整 Twitter 高级搜索语法
- 支持 `from:`、`since_time:`、`until_time:`、`filter:replies` 等

**Fallback 机制：**
- 如果主 Actor 返回 404/actor-not-found，或连续 3 次运行失败 → 尝试备选 Actor：`microworlds/twitter-x-scraper`
- 如果所有 Actor 都不可用 → 向用户报告"当前 Twitter 爬取服务暂不可用，建议稍后重试或手动提供推文数据"

### Twitter/X 输入解析

用户输入可能是以下三种形式之一：

**形式 A - 自然语言：**
> "搜一下马斯克对 Kimi 和 Qwen 的评价"

解析为：
```json
{
  "searchTerms": ["from:elonmusk Kimi", "from:elonmusk Qwen"],
  "queryType": "Top",
  "maxItems": 200
}
```

**形式 B - Twitter 高级搜索语法：**
> "from:elonmusk since_time:1735689600 until_time:1743465600 AI"

直接使用，不做转换。

**形式 C - 混合：**
> "查 @elonmusk 2025年1月到3月关于中国AI的所有推文，包括转发和回复"

解析为多个搜索词组合：
```json
{
  "searchTerms": [
    "from:elonmusk since_time:1735689600 until_time:1743465600 China AI",
    "from:elonmusk since_time:1735689600 until_time:1743465600 Chinese AI"
  ],
  "queryType": "Latest",
  "maxItems": 500
}
```

**形式 D - 公司/人物全面舆情搜索（自动多维度）：**
> "搜索关于 Exa 这家公司的评价"
> "看看大家对 Sam Altman 怎么看"

当用户搜索**公司/品牌/人物**且**没有使用高级搜索语法**时，自动生成多维度搜索组合，覆盖全部舆论声量。

**Handle 获取规则：**
- 用户直接提供 `@handle`（如 `@elonmusk`、`@ExaAILabs`）→ 直接提取使用
- 用户只提供名称（如"Exa"、"Sam Altman"、"月之暗面"）→ **先用 web search 查找其官方 Twitter/X handle**，确认后再生成搜索词
- 常见大公司且无歧义（如 OpenAI→@OpenAI、Tesla→@Tesla）可直接使用，但仍建议快速验证

**示例（Exa）：**
1. 用户说"搜索关于 Exa"
2. Web search 确认官方 handle 为 `@ExaAILabs`
3. 生成多维度搜索组合：

```json
{
  "searchTerms": [
    "Exa",
    "from:ExaAILabs",
    "Exa filter:replies",
    "Exa filter:nativeretweets",
    "Exa filter:quote"
  ],
  "queryType": "Top",
  "maxItems": 200
}
```

**多维度说明：**
| 搜索词 | 覆盖内容 |
|--------|---------|
| `Exa` | 所有提及该公司的推文（路人、KOL、媒体） |
| `from:ExaAILabs` | 公司官方账号的发声 |
| `Exa filter:replies` | 用户对公司推文的直接评论 |
| `Exa filter:nativeretweets` | 传播行为 |
| `Exa filter:quote` | 带评论的转发（观点最鲜明） |

Step 4 清洗时会按 `id` 自动去重，合并结果为完整舆论画像。

**触发"全面搜索"的条件：**
- 用户提到"关于 X 公司/这家品牌/这个人"等泛指表述
- 用户**没有**使用 `from:`、`filter:`、`since_time:` 等高级语法
- 用户**没有**明确限定只看某个维度（如"只看官方推文"）

**Twitter/X 输入解析规则：**
- 如果用户提到"最近N条"，设 `queryType: "Latest"`，`maxItems: N`
- 如果用户提到"最热门的"，设 `queryType: "Top"`
- 如果用户提到"回复/评论"，追加 `filter:replies`
- 如果用户提到"转发"，追加 `filter:nativeretweets`
- 如果用户提到"引用"，追加 `filter:quote`
- 时间范围：尝试解析自然语言时间（如 "2025年以来" 转为 `since_time`），失败则问用户

### Twitter/X 运行爬取

使用 bundled 脚本执行爬取：

```bash
node --env-file=.env scripts/run_actor.js \
  --actor "kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest" \
  --input '<JSON_INPUT>' \
  --output <文件名>.json \
  --format json
```

**并行策略：**
- 单个搜索词：直接运行
- 多个搜索词（>3个）：分批并行，每批最多 3 个
- 每个搜索词保存为独立 JSON 文件，命名格式 `raw_twitter_<keyword>_<timestamp>.json`

### Twitter/X 数据清洗

**Step 1：过滤 Mock 数据**

读取结果后，**立即过滤**：

```javascript
const realTweets = rawData.filter(r => r.type !== "mock_tweet" && r.id !== -1);
```

**Mock 数据特征：**
- `type: "mock_tweet"`
- `id: -1`
- text 包含 "From KaitoEasyAPI, a reminder..."

如果过滤后数据为空，向用户报告"该搜索条件下未找到真实推文"。

**Step 2：去重与标准化**

- **去重：** 按 `id` 去重（同一推文可能在多个搜索词中出现）
- **排序：** 默认按 `createdAt` 时间倒序
- **字段标准化：** 统一字段名，提取关键信息：
  - `id`, `url`, `text`, `createdAt`
  - `author.name`, `author.userName`, `author.followers`
  - `retweetCount`, `replyCount`, `likeCount`, `viewCount`, `quoteCount`
  - `isReply`, `inReplyToId`, `conversationId`
  - `entities.user_mentions`

---

## 平台二：Reddit

### Reddit 核心 Actor

**主 Actor：** `automation-lab/reddit-scraper`
- 支持 `searchQuery` 全局关键词搜索（跨 subreddit）
- 支持抓取帖子下的评论（`includeComments`、`maxCommentsPerPost`、`commentDepth`）
- 支持时间过滤（`timeFilter`: hour/day/week/month/year/all）和排序（`sort`: relevance/hot/new/top/rising）
- 输出 schema 完整，包含 `score`、`upvoteRatio`、`numComments`、`subreddit`、`permalink`、`depth` 等

**Fallback 机制：**
- 如果主 Actor 返回 404/actor-not-found，或连续 3 次运行失败 → 在 Apify Store 搜索其他 `reddit scraper` actor（如 `prodiger/reddit-scraper`，与 automation-lab  schema 兼容）
- 所有 Reddit actor 都不可用 → 向用户报告"当前 Reddit 爬取服务暂不可用，建议稍后重试"

**为什么不使用 Reddit 官方 API（PRAW）：**
- 需要 OAuth App 注册和 token 维护， setup 成本高
- 速率限制严格（60 请求/分钟），大规模采集极慢
- 无法高效进行全局跨 subreddit 关键词搜索
- Apify actor 直接读取 Reddit 公开 JSON 端点，已处理好分页、限流和反爬

### Reddit 输入解析

**形式 A - 自然语言：**
> "搜一下 Reddit 上关于 Kimi 的评价"
> "看看 r/LocalLLaMA 怎么评价 Qwen"

解析为：
```json
{
  "searchQuery": "Kimi",
  "searchSubreddit": "",
  "sort": "relevance",
  "timeFilter": "month",
  "maxPostsPerSource": 200,
  "includeComments": true,
  "maxCommentsPerPost": 50,
  "commentDepth": 3
}
```

**形式 B - 指定 subreddit：**
> "r/LocalLLaMA 对 Exa 的看法"

解析为：
```json
{
  "searchQuery": "Exa",
  "searchSubreddit": "LocalLLaMA",
  "includeComments": true,
  "maxPostsPerSource": 200
}
```

**形式 C - 公司/人物全面舆情搜索（Reddit 版）：**
当用户搜索**公司/品牌/人物**且没有限定 subreddit 时，生成多个搜索组合：

```json
{
  "searchQueries": ["Exa", "Exa AI", "Exa search engine"],
  "sort": "relevance",
  "timeFilter": "month",
  "maxPostsPerSource": 100,
  "includeComments": true,
  "maxCommentsPerPost": 50,
  "commentDepth": 3
}
```

**Reddit 输入解析规则：**
- 如果用户提到"最近N条" → `sort: "new"`，`maxPostsPerSource: N`
- 如果用户提到"最热门的" → `sort: "top"`，`timeFilter: "week"` 或 `"month"`
- 如果用户提到"评论/回复" → `includeComments: true`
- 如果用户指定 subreddit（`r/xxx`）→ 提取到 `searchSubreddit`
  - **注意**：`searchSubreddit` 参数在部分 subreddit 上可能返回 0 条（实测 r/webdev 有此问题）。如发生这种情况，改用**无 `searchSubreddit` 的 broad search**，然后在清洗阶段根据 `subreddit` 字段过滤出目标社区的内容
- 时间范围：映射为 `timeFilter`（hour/day/week/month/year/all），失败则问用户
- **默认** `includeComments: true`（Reddit 评论是舆论的重要组成部分）
- **默认** `maxCommentsPerPost: 50`，`commentDepth: 3`（防止热门帖子评论爆炸）

### Reddit 运行爬取

使用 bundled 脚本执行爬取：

```bash
node --env-file=.env scripts/run_actor.js \
  --actor "automation-lab/reddit-scraper" \
  --input '<JSON_INPUT>' \
  --output <文件名>.json \
  --format json
```

**并行策略：**
- 单个搜索词：直接运行
- 多个搜索词（>3个）：分批并行，每批最多 3 个
- 每个搜索词保存为独立 JSON 文件，命名格式 `raw_reddit_<keyword>_<timestamp>.json`

### Reddit 数据清洗

**Step 1：过滤无效数据**

```javascript
const validItems = rawData.filter(r =>
  r.author !== "[deleted]" &&
  r.author !== "[removed]" &&
  r.selfText !== "[deleted]" &&
  r.selfText !== "[removed]" &&
  r.body !== "[deleted]" &&
  r.body !== "[removed]"
);
```

如果过滤后数据为空，向用户报告"该搜索条件下未找到有效 Reddit 内容"。

**Step 2：去重与标准化**

- **去重：** 按 `id` 去重
- **排序：** 默认按 `createdAt` 时间倒序（或按 `score` 倒序，若用户要求"最热门"）
- **字段标准化：** 统一为通用格式，供情感分析脚本使用：

```json
{
  "id": "t3_xxx 或 t1_xxx",
  "platform": "reddit",
  "type": "post" | "comment",
  "text": "帖子：title + selfText；评论：body",
  "url": "https://reddit.com/permalink",
  "createdAt": "2026-01-15T10:00:00Z",
  "author": "username",
  "subreddit": "technology",
  "score": 42,
  "upvoteRatio": 0.87,
  "numComments": 15,
  "depth": 0,
  "isSubmitter": false
}
```

**文本构造规则：**
- **Post:** `text = title + "\n\n" + (selfText || "")`。如果是链接帖（非 self），在 text 末尾追加 `[Link: url]`。
- **Comment:** `text = body`
- 空 body（`[deleted]`、`[removed]`）已在 Step 1 过滤

---

## 共享：情感分析（DeepSeek API）

使用 bundled 脚本 `scripts/sentiment_analysis.js` 执行批量分析。该脚本对 Twitter/X 和 Reddit 数据通用，只需输入标准化后的 JSON 文件。

```bash
node --env-file=.env scripts/sentiment_analysis.js \
  --input cleaned/cleaned_<ts>.json \
  --output analyzed/analyzed_<ts>.json \
  --concurrency 10 \
  --timeout 30000
```

脚本内置 prompt 已覆盖常见复杂表达识别。如需更详细的分析标准，参考 `references/sentiment_prompt.md`。

**输出格式（JSON，每条记录附加字段）：**
```json
{
  "sentiment": "positive" | "negative" | "neutral",
  "confidence": 0.0-1.0,
  "key_phrase": "提取核心观点的一句话（原文引用或精炼总结）",
  "reasoning": "分析理由，说明为什么是这个情感倾向"
}
```

**情感分类说明：**
- `positive`：明确赞扬、认可、支持
- `negative`：明确批评、质疑、反对、反讽/阴阳怪气
- `neutral`：客观陈述、无明显情感倾向、纯信息分享
- 脚本会自动将 API 返回的 `"sarcastic"` 映射为 `"negative"`，确保统计口径统一。

**脚本特性：**
- **断点续传**：如果输出文件已存在，自动加载并跳过已分析的记录
- **流式保存**：每分析完 10 条自动持久化进度，中途崩溃不会丢失全部结果
- **429 退避重试**：遇到 DeepSeek 配额限制时自动指数退避（最多重试 3 次）
- **动态并发调整**：根据实时失败率自动降低并发数（失败率>20%降速，>40%进一步降速）
- **错误项二次重试**：全部完成后，用最低并发对失败项再做一次重试

**失败处理：**
- 单条分析失败：标记为 `sentiment: "error"`，继续处理其他
- 批量失败率 > 30%：脚本自动降速重试（并发数减半）

---

## 共享：核心声音聚类

使用 bundled 脚本 `scripts/cluster_voices.js` 将情感分析结果按主题聚类，提取好差评核心声音代表。

```bash
node --env-file=.env scripts/cluster_voices.js \
  --input analyzed/analyzed_<ts>.json \
  --output voices/voices_<ts>.json
```

**脚本可靠性设计：**
- 聚类输入使用 `key_phrase`（已提炼的精简观点），而非原始长文本，降低 LLM 理解难度
- 每极性最多取 50 条高置信度（`confidence >= 0.7`）记录参与聚类
- `temperature: 0` + `response_format: {type: "json_object"}` 保证输出稳定
- HTTP 错误自动重试 3 次（指数退避）
- 返回结果经过严格 schema 校验；校验失败时触发一次自我纠错（把错误信息回传 LLM 要求修正）
- **硬兜底**：若聚类/纠错全部失败，自动退化为"按互动量取 Top 5"，确保报告生成不中断

**输出格式（JSON）：**
```json
{
  "positive": [
    {
      "theme": "API 性能优异",
      "representative": { /* 完整记录对象 */ },
      "cluster_size": 15,
      "avg_confidence": 0.88
    }
  ],
  "negative": [...]
}
```

报告生成阶段直接读取 `voices.json`，不再手动挑选代表。

---

## 共享：统计分析与报告

### 情感分布统计（通用）

- 总样本数、正面 / 负面 / 中性 数量及占比

### 好差评核心声音提取规则

**核心改进：先聚类主题，再选代表，防止"高赞但孤立"淹没"低赞但反复提及"的声音。**

**步骤 1：聚类（LLM，由 `cluster_voices.js` 自动完成）**
- 将同一情感分类（positive / negative）的所有记录，按 `key_phrase` 聚类为若干主题簇
- 聚类标准：多条记录表达的是**同一类问题/同一类赞美**，即归为一簇
- 例：50 条都在说"免费 tier 休眠限制太坑"（各只有 2-3 赞）→ 聚为一个高权重簇
- 例：1 条抖机灵的 joke 得了 200 赞 → 单独一簇

**步骤 2：选代表（由 `cluster_voices.js` 自动完成）**
- 在每个主题簇内，选取 `confidence > 0.7` 且互动最高（Twitter: `likeCount`，Reddit: `score`）的一条作为代表
- 优先选 `depth: 0` 的 Reddit 评论（顶层评论可见度最高）
- 数量：各情感分类总共 3-5 条代表，**优先覆盖不同主题簇**（确保多元化），而非同一主题的多个变体

**步骤 3：输出格式（报告撰写时）**
- 每条代表必须附：原文引用、作者、链接、（Reddit 加 subreddit）
- 小标题 = 该主题簇的核心结论（如"免费 tier 休眠限制是最大痛点"）
- 数据来源：`voices/voices_<ts>.json`

### 舆论总结（必须生成）

在表格下方生成一段 2-4 句话的总结，要求：
- 点明整体情感倾向（偏正面/负面/中性）
- 指出近期最大舆论焦点事件（如某次合作、产品发布）
- 提及获得较多正面/负面传播的具体事件或产品特性
- 语言简洁，避免堆砌数据

**示例（Twitter/X）：**
> Exa 在 Twitter/X 上的整体舆论偏正面，正面情感占比超过半数（56.6%）。近期最大舆论焦点是 Exa 与 Google 达成合作伙伴关系（Grounding With Exa 接入 Gemini 模型），该事件同时引发了赞誉与质疑。此外，Exa 与 Coinbase 的合作、技术亮点（如 Highlights 模型减少 96% tokens）也获得了较多正面传播。

**示例（Reddit）：**
> Exa 在 Reddit 上的讨论主要集中在 r/technology 和 r/LocalLLaMA，整体情感偏中性略带正面（正面 42%，负面 31%）。用户最关注的是 Exa 的实时搜索 API 性能， praised 其比传统 RAG 更准确；负面声音则集中在定价策略和文档不完整上。

### 讨论社区分布（Reddit 独有）

在 Reddit 报告中，增加 subreddit 分布表格：

| Subreddit | 帖子数 | 评论数 | 平均 Score | 主要情感倾向 |
|-----------|--------|--------|------------|--------------|
| r/technology | 5 | 23 | 45 | 偏正面 |
| r/LocalLLaMA | 3 | 12 | 28 | 偏负面 |

### 意见领袖代表性评论（Twitter/X 独有）

**注意：Reddit 报告不包含此 section。**

**Twitter/X 意见领袖分层筛选（按优先级降序）：**

意见领袖的核心标准是**行业地位/专业声望优先于粉丝量**。

| 优先级 | 判定标准 | 说明 |
|--------|----------|------|
| **P0** | 行业公认大佬、核心贡献者、知名项目作者 | 如目标公司的核心工程师、该领域开源项目 maintainer、技术书籍作者。粉丝量可低于 10K，但专业含金量极高 |
| **P1** | 高粉丝量（≥10K）+ 领域相关 | 知名开发者、技术 KOL、科技媒体账号。粉丝量是门槛，但必须与讨论领域相关 |
| **P2** | 高互动（高 quote/转发，引发广泛讨论） | 某条 tweet 被大量引用、转发或引发 thread 讨论，说明观点具有传播价值 |
| **P3** | 履历亮眼但粉丝一般（2K-10K） | 大厂工程师、知名创业公司成员、会议 speaker。通过 bio 或近期推文可推断其领域身份 |

**进一步筛选：**
- 优先 sentiment 为 **positive 或 negative**（排除 neutral），观点鲜明、有信息量
- 必须提取：原文引用、推文链接、作者用户名、粉丝量、profile 链接、简要履历背景、**观点总结**（一句话概括核心立场）
- 如 bio 不足，可通过其近期推文推断领域身份
- 数量：3-5 条，**优先覆盖不同优先级层级**（不要全选 P1 网红）

---

## 输出与导出

### 对话框输出

1. 执行摘要（2-3 句话）
2. 核心统计表格（markdown）
3. 好差评核心声音
4. 讨论社区分布（Reddit 独有）
5. 意见领袖代表性评论（Twitter/X 独有，如有）

### 文件保存

**Twitter/X 目录结构：**
```
<project-root>/
└── twitter_scrape_YYYY-MM-DD_HH-MM-SS/
    ├── raw/
    │   ├── raw_twitter_<keyword1>_<ts>.json
    │   └── raw_twitter_<keyword2>_<ts>.json
    ├── cleaned/
    │   └── cleaned_<ts>.json
    ├── analyzed/
    │   └── analyzed_<ts>.json
    └── report/
        └── report_<ts>.md
```

**Reddit 目录结构：**
```
<project-root>/
└── reddit_scrape_YYYY-MM-DD_HH-MM-SS/
    ├── raw/
    │   ├── raw_reddit_<keyword1>_<ts>.json
    │   └── raw_reddit_<keyword2>_<ts>.json
    ├── cleaned/
    │   └── cleaned_<ts>.json
    ├── analyzed/
    │   └── analyzed_<ts>.json
    └── report/
        └── report_<ts>.md
```

**报告模板选择：**
- Twitter/X → 参考 `references/report_template.md`
- Reddit → 参考 `references/reddit_report_template.md`

两个模板均使用 `{{PLACEHOLDER}}` 占位符机制。Claude 读取模板后，用实际统计数据替换占位符，生成最终 Markdown 文件。

---

## 边界情况处理

### Twitter/X
- **Actor 失效/不可用**：主 Actor 返回 404/actor-not-found 或连续 3 次失败 → 尝试备选 Actor `microworlds/twitter-x-scraper`；所有 Actor 都不可用 → 报告"当前 Twitter 爬取服务暂不可用"
- **搜索结果为空**：报告"未找到符合条件的真实推文"
- **全部结果为 mock**：报告"该 actor 未返回真实数据，可能搜索条件过于严格或目标账号无公开内容"

### Reddit
- **Actor 失效/不可用**：主 Actor `automation-lab/reddit-scraper` 失败 → 尝试 Apify Store 中其他 `reddit scraper` actor；所有都不可用 → 报告"当前 Reddit 爬取服务暂不可用"
- **搜索结果为空**：报告"未找到符合条件的 Reddit 内容"
- **全部为 `[deleted]`/`[removed]`**：报告"该关键词下的内容已被大量删除，建议更换关键词或搜索更具体的子版块"
- **评论数量爆炸**：单条热门帖子可能有数千评论。默认 `maxCommentsPerPost: 50`、`commentDepth: 3`。如用户需要更多，建议分批处理或提高限制

### 通用
- **情感分析 API 余额不足（429）**：脚本自动指数退避重试（最多 3 次）；如仍失败，报告已分析样本数，剩余未分析数据保存在 `cleaned/` 中，提示用户充值后重新运行即可断点续传
- **情感分析脚本中断/崩溃**：重新运行同一命令，脚本自动检测已有输出文件并从断点续传
- **数据量过大（>1000条）**：建议用户缩小时间范围、增加关键词精度，或分批处理

## 脚本引用

情感分析专用 prompt 见 `references/sentiment_prompt.md`
