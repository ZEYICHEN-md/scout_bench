# {{TARGET_NAME}} Twitter/X 舆情分析报告

> 分析对象：{{TARGET_DESCRIPTION}}  
> 搜索条件：{{SEARCH_TERMS}}  
> 生成时间：{{GENERATED_AT}}

---

## 一、社区舆论概况

> 如为**单家公司/个人**，表格仅保留一列数据；如为**多家对比**，横向展开为多列。

| 指标 | {{ENTITY_1_NAME}} | {{ENTITY_2_NAME}} | {{ENTITY_3_NAME}} |
|------|------------------|------------------|------------------|
| 有效推文数 | {{E1_VALID_COUNT}} | {{E2_VALID_COUNT}} | {{E3_VALID_COUNT}} |
| 总浏览量 | {{E1_TOTAL_VIEWS}} | {{E2_TOTAL_VIEWS}} | {{E3_TOTAL_VIEWS}} |
| 平均单帖浏览量 | {{E1_AVG_VIEWS}} | {{E2_AVG_VIEWS}} | {{E3_AVG_VIEWS}} |
| 平均 likes | {{E1_AVG_LIKES}} | {{E2_AVG_LIKES}} | {{E3_AVG_LIKES}} |
| 正面 / 负面 / 中性 | {{E1_POS}} / {{E1_NEG}} / {{E1_NEU}} | {{E2_POS}} / {{E2_NEG}} / {{E2_NEU}} | {{E3_POS}} / {{E3_NEG}} / {{E3_NEU}} |
| 正面占比 | {{E1_POS_PCT}}% | {{E2_POS_PCT}}% | {{E3_POS_PCT}}% |
| 负面占比 | {{E1_NEG_PCT}}% | {{E2_NEG_PCT}}% | {{E3_NEG_PCT}}% |
| 中性占比 | {{E1_NEU_PCT}}% | {{E2_NEU_PCT}}% | {{E3_NEU_PCT}}% |
| **好评核心声音** | {{E1_POS_VOICES}} | {{E2_POS_VOICES}} | {{E3_POS_VOICES}} |
| **差评核心声音** | {{E1_NEG_VOICES}} | {{E2_NEG_VOICES}} | {{E3_NEG_VOICES}} |

**好评核心声音格式示例：**
> **数据收集策略领先**（15 条同类观点）- "ahead of the game when it comes to hi quality data collection"<br>
> **家用概念备受期待**（8 条同类观点）- "The Household Robot We've Been Waiting For?"

**差评核心声音格式示例：**
> **对数据收集方式的轻度质疑**（6 条同类观点）@BalboaRegular: "我自私地希望 Neo 是最好的，但我觉得 Sunday Robotics 会因为获取训练数据的方式太轻松，而更快地变得更优秀。Sunday robotics clearly wins on the creepy factor."

**舆论总结：** {{SENTIMENT_SUMMARY}}

---

## 二、意见领袖代表性评论

> **意见领袖定义**：在相关领域具有较高影响力的人物，通常表现为粉丝量较高（通常 ≥10,000，可根据领域调整）、行业知名度高、或该评论获得了显著互动（高点赞/转发）。优先选取观点鲜明、有信息量的 positive/negative 评论。

| # | 意见领袖 | 背景履历 | 粉丝量 | 原文引用 | 观点总结 | 推文链接 | Profile |
|---|---------|---------|--------|---------|---------|---------|---------|
| 1 | {{I1_NAME}} (@{{I1_HANDLE}}) | {{I1_BIO}} | {{I1_FOLLOWERS}} | {{I1_QUOTE}} | {{I1_SUMMARY}} | [链接]({{I1_URL}}) | [Profile]({{I1_PROFILE}}) |
| 2 | {{I2_NAME}} (@{{I2_HANDLE}}) | {{I2_BIO}} | {{I2_FOLLOWERS}} | {{I2_QUOTE}} | {{I2_SUMMARY}} | [链接]({{I2_URL}}) | [Profile]({{I2_PROFILE}}) |
| 3 | {{I3_NAME}} (@{{I3_HANDLE}}) | {{I3_BIO}} | {{I3_FOLLOWERS}} | {{I3_QUOTE}} | {{I3_SUMMARY}} | [链接]({{I3_URL}}) | [Profile]({{I3_PROFILE}}) |

**意见领袖观点总结：** {{INFLUENCER_SUMMARY}}

---

## 数据文件索引

| 文件 | 路径 |
|------|------|
| 原始数据 | `raw/raw_<keyword>_<ts>.json` |
| 清洗后数据 | `cleaned/cleaned_<ts>.json` |
| 情感分析结果 | `analyzed/analyzed_<ts>.json` |
| 核心声音聚类 | `voices/voices_<ts>.json` |
| 本报告 | `report/report_<ts>.md` |
