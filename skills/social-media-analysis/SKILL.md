---
name: social-media-analysis
description: >
  使用 Apify 爬取 Twitter/X 数据并进行情感分析与统计报告生成。
  当用户需要抓取 Twitter/X 推文、分析推文情感倾向、生成社媒数据报告、
  或者提到"推特数据"、"Twitter爬虫"、"X平台数据"、"推文分析"、
  "社媒监控"、"舆情分析"时，务必使用此 skill。
  支持自然语言输入和 Twitter 高级搜索语法，自动过滤 mock 数据，
  并发调用 DeepSeek API 进行精准情感分析（识别反讽、欲扬先抑等复杂表达），
  最终输出结构化统计报告和 Markdown 文档。
---

# Twitter/X 数据爬取与情感分析 Skill

## 依赖

- `.env` 文件包含 `APIFY_TOKEN` 和 `DEEPSEEK_API_KEY`
- Node.js 20+（用于运行 Apify actor 脚本）
- `run_actor.js` 脚本路径：`${CLAUDE_PLUGIN_ROOT}/reference/scripts/run_actor.js`

## 核心 Actor

固定使用 `kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest`
- 价格：$0.00025/条
- 支持完整 Twitter 高级搜索语法
- 支持 `from:`、`since_time:`、`until_time:`、`filter:replies` 等

## Workflow

### Step 1: 解析用户输入

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

**输入解析规则：**
- 如果用户提到"最近N条"，设 `queryType: "Latest"`，`maxItems: N`
- 如果用户提到"最热门的"，设 `queryType: "Top"`
- 如果用户提到"回复/评论"，追加 `filter:replies`
- 如果用户提到"转发"，追加 `filter:nativeretweets`
- 如果用户提到"引用"，追加 `filter:quote`
- 时间范围：尝试解析自然语言时间（如 "2025年以来" 转为 `since_time`），失败则问用户

### Step 2: 运行爬取

使用 `run_actor.js` 脚本执行爬取：

```bash
node --env-file=.env ${CLAUDE_PLUGIN_ROOT}/reference/scripts/run_actor.js \
  --actor "kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest" \
  --input '<JSON_INPUT>' \
  --output <文件名>.json \
  --format json
```

**并行策略：**
- 单个搜索词：直接运行
- 多个搜索词（>3个）：分批并行，每批最多 3 个
- 每个搜索词保存为独立 JSON 文件，命名格式 `raw_<keyword>_<timestamp>.json`

### Step 3: 过滤 Mock 数据

读取结果后，**立即过滤**：

```javascript
const realTweets = rawData.filter(r => r.type !== "mock_tweet" && r.id !== -1);
```

**Mock 数据特征：**
- `type: "mock_tweet"`
- `id: -1`
- text 包含 "From KaitoEasyAPI, a reminder..."

如果过滤后数据为空，向用户报告"该搜索条件下未找到真实推文"。

### Step 4: 数据清洗与合并

**去重：** 按 `id` 去重（同一推文可能在多个搜索词中出现）
**排序：** 默认按 `createdAt` 时间倒序
**字段标准化：** 统一字段名，提取关键信息：
- id, url, text, createdAt
- author.name, author.userName, author.followers
- retweetCount, replyCount, likeCount, viewCount, quoteCount
- isReply, inReplyToId, conversationId
- entities.user_mentions

### Step 5: 情感分析（DeepSeek API）

**并发配置：** 默认 10 条并行，单条超时 30 秒。

**API 调用：**
```
POST https://api.deepseek.com/chat/completions
Headers: Authorization: Bearer $DEEPSEEK_API_KEY
Body: {
  "model": "deepseek-chat",
  "messages": [
    {"role": "system", "content": <SENTIMENT_PROMPT>},
    {"role": "user", "content": tweetText}
  ],
  "temperature": 0.3
}
```

**输出格式要求（JSON）：**
```json
{
  "sentiment": "positive" | "negative" | "neutral",
  "confidence": 0.0-1.0,
  "key_phrase": "提取这条推文表达核心观点的一句话（原文引用或精炼总结）",
  "reasoning": "分析理由，说明为什么是这个情感倾向"
}
```

**情感分类说明：**
- `positive`：明确赞扬、认可、支持
- `negative`：明确批评、质疑、反对
- `neutral`：客观陈述、无明显情感倾向、纯信息分享

**需要识别的复杂表达（参考 `references/sentiment_prompt.md`）：**
- 欲扬先抑：先提缺点再转折到优点 → positive
- 欲抑先扬：先夸表面再揭露实质问题 → negative
- 反讽/阴阳怪气：字面夸奖但实际批评 → negative
- 夸张表达：需结合语境判断正负
- emoji 仅作辅助判断，不单独决定情感
- 引用转发以评论内容情感为准

**失败处理：**
- 单条分析失败：标记为 `sentiment: "error"`，继续处理其他
- 批量失败率 > 30%：降速重试（并发数减半）

### Step 6: 统计分析

**基础统计：**
- 总样本数
- 按情感分类：positive / negative / neutral 数量及占比
- 按时间分布：月度/周度发文趋势
- 互动量统计：平均点赞、转发、评论数；Top 10 高互动推文

**好差评分析表（核心输出）：**

| 维度 | 内容 |
|------|------|
| 样本数 | N |
| 正面 / 负面 / 中性 | N1 / N2 / N3 |
| 正面占比 | X% |
| 负面占比 | X% |
| 中性占比 | X% |
| **好评核心声音** | 提炼核心观点 + 代表性原话（附链接） |
| **差评核心声音** | 提炼核心观点 + 代表性原话（附链接） |

**核心声音提取规则：**
- 从各情感分类中，选取 `confidence > 0.7` 且 `likeCount` 最高的 3-5 条
- 先对同类观点进行 LLM 聚类，提炼出核心观点概括，再附上最具代表性的原话
- 必须附原文链接

### Step 7: 输出与导出

**对话框输出：**
1. 执行摘要（2-3 句话）
2. 核心统计表格（markdown）
3. 高互动推文 Top 5
4. 好差评分析表格

**文件保存：**

目录结构：
```
<project-root>/
└── twitter_scrape_YYYY-MM-DD_HH-MM-SS/
    ├── raw/                          # 原始数据
    │   ├── raw_<keyword1>_<ts>.json
    │   └── raw_<keyword2>_<ts>.json
    ├── cleaned/                      # 清洗后数据（去重+过滤mock）
    │   └── cleaned_<ts>.json
    ├── analyzed/                     # 情感分析后数据
    │   └── analyzed_<ts>.json
    └── report/                       # 报告
        └── report_<ts>.md
```

**报告 Markdown 结构：**
```markdown
# Twitter/X 数据爬取与情感分析报告

## 执行摘要
## 搜索条件
## 样本概况
## 情感分布统计
## 高互动推文 Top 10
## 好评核心声音
## 差评核心声音
## 时间趋势分析
## 原始数据文件索引
```

## 边界情况处理

- **搜索结果为空**：报告"未找到符合条件的真实推文"，不运行情感分析
- **全部结果为 mock**：报告"该 actor 未返回真实数据，可能搜索条件过于严格或目标账号无公开内容"
- **情感分析 API 余额不足**：报告已分析样本数，剩余未分析数据保存在 `cleaned/` 中，提示用户充值后继续
- **推文数量过大（>1000条）**：建议用户缩小时间范围或增加关键词精度，或分批处理

## 脚本引用

情感分析专用 prompt 见 `references/sentiment_prompt.md`