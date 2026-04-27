# 输出格式规范

> 本文件规范 `sector-prospector` 的所有输出文件格式，确保与 `weekly-recommendation` 管线的无缝衔接。

---

## 1. sector_map.json

Phase 1 赛道解构的输出。

```json
{
  "sector_theme": "AI Agent基础设施",
  "analysis_summary": "一句话总结赛道现状和挖掘重点",
  "sub_sectors": [
    {
      "name": "Agent Runtime/Sandbox",
      "rationale": "为什么这是一个独立的子赛道，一句话",
      "key_concepts": ["sandbox", "runtime", "execution environment", "isolated agent"],
      "search_queries": [
        "agent sandbox startup",
        "AI agent runtime company",
        "sandbox for LLM agents"
      ],
      "batch": 1
    }
  ],
  "timestamp": "2026-04-22T10:00:00Z"
}
```

**字段说明**：
- `sector_theme`：用户输入的赛道主题
- `analysis_summary`：agent 对赛道整体态势的简短判断（30-50字），帮助用户快速理解赛道结构
- `sub_sectors`：子赛道数组，3-6 个元素
  - `name`：子赛道名称，应简洁具体（如 "Agent Runtime/Sandbox" 优于 "Infrastructure"）
  - `rationale`：该子赛道独立的理由
  - `key_concepts`：3-5 个技术名词/产品概念，粒度要细
  - `search_queries`：Phase 2 的初始 query 列表，agent 会基于此扩展
  - `batch`：挖掘批次，`1` = 第一批（高优先级），`2` = 第二批（剩余子赛道）
- `timestamp`：生成时间戳

---

## 2. raw_prospects.json

Phase 2 深度挖掘的中间输出。

```json
{
  "sector_theme": "AI Agent基础设施",
  "sub_sector": "Agent Runtime/Sandbox",
  "prospects": [
    {
      "company_name": "Virtue AI",
      "website": "https://virtueai.com",
      "funding_stage": "Seed",
      "founders": "John Doe, Jane Smith",
      "differentiation": "提供隔离执行环境让 LLM Agent 安全运行外部代码",
      "confidence": "high",
      "hit_queries": [
        "code execution sandbox startup",
        "ex-Google code sandbox startup"
      ],
      "source_query": "code execution sandbox startup",
      "source_engine": "tavily",
      "source_url": "https://techcrunch.com/...",
      "founder_name_signal": "high",
      "founder_name_signal_basis": "姓氏 Wang 匹配拼音，全名 Wei Wang 符合拼音结构",
      "discovered_at": "2026-04-22T10:15:00Z"
    }
  ],
  "timestamp": "2026-04-22T10:20:00Z"
}
```

**字段说明**：
- `company_name`：公司名，优先使用官方品牌名
- `website`：官网 URL，如无法确认则留空
- `funding_stage`：融资阶段线索，如 "Seed" / "Series A" / "Pre-seed" / "unknown"
- `founders`：创始人姓名，如有多个用逗号分隔
- `differentiation`：一句话差异化亮点（1-2句话）
- `confidence`：信息可信度，`high` / `medium` / `low`
  - `high`：2+ 个独立 query 命中；或有融资/创始人/官网信息
  - `medium`：1 个 query 命中，但有详细描述
  - `low`：仅名字出现，无其他信息
- `hit_queries`：命中该公司的所有独立 query 列表（用于可信度判定和审计）
- `source_query`：首次发现该公司的搜索 query
- `source_engine`：`tavily` 或 `exa`
- `source_url`：来源文章 URL（如有）
- `founder_name_signal`：创始人姓名拼音信号，`"high"` / `"medium"` / `"none"`，详见 `references/discovery_strategies.md`
- `founder_name_signal_basis`：信号判定依据，如 `"姓氏 Wang 匹配拼音，全名 Wei Wang 符合拼音结构"`
- `discovered_at`：发现时间戳

**注意**：`raw_prospects.json` 是**按子赛道分文件**存储的，还是**单一全局文件**，由 agent 根据文件大小决定。如果子赛道较多，建议分文件：`raw_prospects_{sub_sector_slug}.json`。

---

## 3. companies.csv

Phase 3 最终输出，**必须严格兼容 weekly-recommendation 的 companies.csv 格式**。

```csv
company_name,rank,score,reason,source,track,note
VirtueAI,,,提供隔离执行环境让LLM Agent安全运行外部代码,Tavily:agent sandbox startup,Agent Runtime/Sandbox,
RuntimeLab,,,开源Agent运行时框架支持多语言工具调用,Exa:agent runtime github,Agent Runtime/Sandbox,
```

**字段映射规则**：

| CSV 字段 | 来源 | 说明 |
|----------|------|------|
| `company_name` | `raw_prospects.company_name` | 保持原始大小写，去除多余空格 |
| `rank` | 留空 | sector-prospector 不做排名 |
| `score` | 留空 | sector-prospector 不做评分 |
| `reason` | `raw_prospects.differentiation` | 差异化亮点，1-2句话，去除逗号（或确保CSV转义正确） |
| `source` | 合成 | 格式：`{Engine}:{source_query}`，如 `Tavily:agent sandbox startup` |
| `track` | `raw_prospects.sub_sector` | 子赛道名称 |
| `note` | 留空 / `CHECK_HYPE` / `CHINESE_FOUNDER_SIGNAL_HIGH` / `CHINESE_FOUNDER_SIGNAL_MEDIUM` | 通常留空。若疑似 public hype 但决定保留，标注 `CHECK_HYPE`；若识别到华人创始人信号，标注 `CHINESE_FOUNDER_SIGNAL_HIGH` 或 `CHINESE_FOUNDER_SIGNAL_MEDIUM`，便于 weekly-recommendation 优先筛查 |

**CSV 转义规则**：
- 如果 `reason` 中包含逗号，用双引号包裹该字段
- 如果 `reason` 中包含双引号，用两个双引号转义

**目标数量**：
- 理想情况下，每个子赛道贡献 **8-15 个**项目
- 总项目数目标：**40-60 个**
- 经 public hype 过滤后，最终保留 **30-50 个**

---

## 4. prospector_notes.json

Phase 3 辅助输出，记录每个项目的完整挖掘路径，便于用户审计和追溯。

```json
{
  "sector_theme": "AI Agent基础设施",
  "total_prospects": 52,
  "total_after_filter": 47,
  "excluded_count": 5,
  "companies": [
    {
      "company_name": "Virtue AI",
      "track": "Agent Runtime/Sandbox",
      "discovery_path": [
        {
          "phase": "concept_search",
          "query": "agent sandbox startup company founded",
          "engine": "tavily",
          "url": "https://techcrunch.com/...",
          "timestamp": "2026-04-22T10:15:00Z"
        },
        {
          "phase": "cross_validation",
          "query": "Virtue AI competitors",
          "engine": "exa",
          "url": "https://...",
          "timestamp": "2026-04-22T10:25:00Z"
        }
      ],
      "excluded": false
    },
    {
      "company_name": "OpenAI",
      "track": "Agent Runtime/Sandbox",
      "discovery_path": [
        {
          "phase": "concept_search",
          "query": "agent sandbox startup",
          "engine": "tavily",
          "timestamp": "2026-04-22T10:15:00Z"
        }
      ],
      "excluded": true,
      "exclusion_reason": "public_hype: 估值$80B+，家喻户晓"
    }
  ],
  "timestamp": "2026-04-22T11:00:00Z"
}
```

**字段说明**：
- `total_prospects`：Phase 2 挖掘出的原始项目总数（含重复）
- `total_after_filter`：Phase 3 去重+过滤后的最终数量
- `excluded_count`：被 public hype 过滤排除的数量
- `companies`：每个项目的详细记录
  - `discovery_path`：挖掘路径数组，记录每次搜索的 query、引擎、URL、时间戳
  - `excluded`：是否被排除
  - `exclusion_reason`：排除原因（如被排除）

---

## 5. prospector_checkpoint.json

断点续跑状态文件。

```json
{
  "sector_theme": "AI Agent基础设施",
  "phase": "prospecting",
  "completed_sub_sectors": ["Agent Runtime/Sandbox"],
  "current_sub_sector": "Agent Orchestration",
  "completed_keywords": ["orchestration", "workflow"],
  "remaining_keywords": ["multi-agent"],
  "timestamp": "2026-04-22T10:30:00Z"
}
```

**断点续跑逻辑**：
1. 启动时检查 `$WORKSPACE/prospector_checkpoint.json`
2. 如果存在，读取 `completed_sub_sectors` 和 `current_sub_sector`
3. 跳过 `completed_sub_sectors` 中的所有子赛道
4. 从 `current_sub_sector` 的 `remaining_keywords` 开始继续
5. 如果不存在 checkpoint，从 Phase 1 开始

---

## 与 weekly-recommendation 的衔接

`companies.csv` 生成后，用户可直接将其作为 `weekly-recommendation` Phase 0 的输出，进入 Phase 1 华人创始人筛查。

**衔接点**：
- `companies.csv` 格式完全一致
- `source` 字段记录了挖掘来源，有助于 Phase 1 的搜索策略优化
- `track` 字段（子赛道）可作为 weekly-recommendation 最终报告中的分类维度
- `note` 字段留空，weekly-recommendation 可根据需要追加 `SKIP_PUBLIC_HYPE` 等标记

**建议工作流**：
```
sector-prospector → companies.csv → weekly-recommendation Phase 1-3 → final_report.md
```
