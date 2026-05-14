# {{TARGET_NAME}} Reddit 舆情分析报告

> 分析对象：{{TARGET_DESCRIPTION}}
> 搜索条件：{{SEARCH_TERMS}}
> 生成时间：{{GENERATED_AT}}

---

## 一、社区舆论概况

> 如为**单家公司/个人**，表格仅保留一列数据；如为**多家对比**，横向展开为多列。

| 指标 | {{ENTITY_1_NAME}} | {{ENTITY_2_NAME}} | {{ENTITY_3_NAME}} |
|------|------------------|------------------|------------------|
| 有效帖子+评论数 | {{E1_VALID_COUNT}} | {{E2_VALID_COUNT}} | {{E3_VALID_COUNT}} |
| 覆盖 subreddits | {{E1_TOTAL_SUBREDDITS}} | {{E2_TOTAL_SUBREDDITS}} | {{E3_TOTAL_SUBREDDITS}} |
| 平均 score | {{E1_AVG_SCORE}} | {{E2_AVG_SCORE}} | {{E3_AVG_SCORE}} |
| 平均 upvoteRatio | {{E1_AVG_UPVOTE_RATIO}} | {{E2_AVG_UPVOTE_RATIO}} | {{E3_AVG_UPVOTE_RATIO}} |
| 正面 / 负面 / 中性 | {{E1_POS}} / {{E1_NEG}} / {{E1_NEU}} | {{E2_POS}} / {{E2_NEG}} / {{E2_NEU}} | {{E3_POS}} / {{E3_NEG}} / {{E3_NEU}} |
| 正面占比 | {{E1_POS_PCT}}% | {{E2_POS_PCT}}% | {{E3_POS_PCT}}% |
| 负面占比 | {{E1_NEG_PCT}}% | {{E2_NEG_PCT}}% | {{E3_NEG_PCT}}% |
| 中性占比 | {{E1_NEU_PCT}}% | {{E2_NEU_PCT}}% | {{E3_NEU_PCT}}% |
| **好评核心声音** | {{E1_POS_VOICES}} | {{E2_POS_VOICES}} | {{E3_POS_VOICES}} |
| **差评核心声音** | {{E1_NEG_VOICES}} | {{E2_NEG_VOICES}} | {{E3_NEG_VOICES}} |

**好评核心声音格式示例：**
> **数据收集策略领先**（15 条同类观点）- "ahead of the game when it comes to hi quality data collection"（r/technology, score: 45）<br>
> **家用概念备受期待**（8 条同类观点）- "The Household Robot We've Been Waiting For?"（r/gadgets, score: 32）

**差评核心声音格式示例：**
> **对数据收集方式的轻度质疑**（6 条同类观点）- "I selfishly hope Neo is the best, but I feel Sunday Robotics will get better faster because of how easy it is to get training data."（r/robotics, score: 28）

**舆论总结：** {{SENTIMENT_SUMMARY}}

---

## 二、讨论社区分布

> 哪些 subreddit 在讨论该话题，各社区的情感倾向和互动情况。

| Subreddit | 帖子数 | 评论数 | 平均 Score | 主要情感倾向 |
|-----------|--------|--------|------------|--------------|
| r/{{S1_NAME}} | {{S1_POSTS}} | {{S1_COMMENTS}} | {{S1_AVG_SCORE}} | {{S1_SENTIMENT}} |
| r/{{S2_NAME}} | {{S2_POSTS}} | {{S2_COMMENTS}} | {{S2_AVG_SCORE}} | {{S2_SENTIMENT}} |
| r/{{S3_NAME}} | {{S3_POSTS}} | {{S3_COMMENTS}} | {{S3_AVG_SCORE}} | {{S3_SENTIMENT}} |

---

## 三、数据文件索引

| 文件 | 路径 |
|------|------|
| 原始数据 | `raw/raw_reddit_<keyword>_<ts>.json` |
| 清洗后数据 | `cleaned/cleaned_<ts>.json` |
| 情感分析结果 | `analyzed/analyzed_<ts>.json` |
| 核心声音聚类 | `voices/voices_<ts>.json` |
| 本报告 | `report/report_<ts>.md` |
