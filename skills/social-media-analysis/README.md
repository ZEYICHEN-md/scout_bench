# social-media-analysis

Twitter/X & Reddit 社媒舆情分析 Skill。支持双平台数据采集、情感分析、主题聚类与结构化报告生成。

## 功能

### 平台支持
- **Twitter/X**：使用 Apify `kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest` Actor 爬取推文（$0.00025/条），备选 `microworlds/twitter-x-scraper`
- **Reddit**：使用 Apify `automation-lab/reddit-scraper` Actor 抓取帖子与评论（跨 subreddit 全局搜索）

### 输入解析
- 支持**自然语言输入**自动解析为平台搜索参数
- 支持**Twitter 高级搜索语法**（`from:`、`since_time:`、`until_time:`、`filter:replies` 等）直接使用
- **公司/人物全面舆情搜索**：未使用高级语法时，自动生成多维度搜索组合（关键词 + 官方账号 + 回复 + 转发 + 引用），覆盖完整舆论声量
- 自动通过 web search 查找公司/人物的官方 Twitter/X handle

### 数据清洗
- **Twitter/X**：自动过滤 `mock_tweet` 虚假数据，按推文 `id` 去重
- **Reddit**：过滤 `[deleted]`/`[removed]` 内容和作者，按帖子/评论 `id` 去重
- 统一字段标准化，输出通用格式供下游分析使用

### 情感分析
- 并发调用 **DeepSeek API** 进行三分类情感分析（positive / negative / neutral）
- 识别反讽、欲扬先抑、欲抑先扬、英文社媒俚语等复杂表达
- API 返回的 `sarcastic` 自动映射为 `negative`，确保统计口径统一
- 输出置信度（0-1）、核心观点提炼（`key_phrase`）与分析理由
- 支持断点续传、流式保存、429 退避重试、动态并发调整

### 核心声音聚类
- 按情感极性（positive / negative）分别对 `key_phrase` 进行主题聚类
- 每极性最多取 50 条高置信度（`confidence >= 0.7`）记录参与聚类
- 聚类后按互动量选取代表，优先选包含目标关键词、Reddit 优先顶层评论
- 各情感分类输出 3-5 条代表，确保主题多元化
- 聚类失败自动退化为"按互动量取 Top 5"兜底

### 统计报告
- 情感分布统计（总样本数、各极性数量及占比）
- **Twitter/X 独有**：意见领袖代表性评论分层筛选（P0-P3 优先级，行业地位优先于粉丝量）
- **Reddit 独有**：subreddit 社区分布统计（帖子数、评论数、平均 score、主要情感倾向）
- 舆论总结段落（整体情感倾向、近期焦点事件、正/负面传播热点）
- 输出结构化 Markdown 报告（基于模板占位符机制）

## 项目结构

```
skills/social-media-analysis/
├── scripts/
│   ├── run_actor.js              # 执行 Apify actor 爬取（通用于 Twitter/X 和 Reddit）
│   ├── sentiment_analysis.js     # 批量 DeepSeek 情感分析
│   └── cluster_voices.js         # 主题聚类并提取好差评核心声音代表
├── references/
│   ├── report_template.md        # Twitter/X 报告 Markdown 模板
│   ├── reddit_report_template.md # Reddit 报告 Markdown 模板
│   └── sentiment_prompt.md       # 情感分析详细 prompt
├── README.md
└── SKILL.md
```

## 输出目录结构

**Twitter/X：**
```
twitter_scrape_YYYY-MM-DD_HH-MM-SS/
├── raw/
│   └── raw_twitter_<keyword>_<ts>.json
├── cleaned/
│   └── cleaned_<ts>.json
├── analyzed/
│   └── analyzed_<ts>.json
└── report/
    └── report_<ts>.md
```

**Reddit：**
```
reddit_scrape_YYYY-MM-DD_HH-MM-SS/
├── raw/
│   └── raw_reddit_<keyword>_<ts>.json
├── cleaned/
│   └── cleaned_<ts>.json
├── analyzed/
│   └── analyzed_<ts>.json
└── report/
    └── report_<ts>.md
```

## 依赖

- `.env` 文件包含 `APIFY_TOKEN` 和 `DEEPSEEK_API_KEY`
- Node.js 20+

## 测试

- 输入解析测试：7/7 通过
- 情感分析准确性测试：10/10 通过（100%）
- 端到端全流程测试：通过
