# weekly-recommendation

每周对工作流筛选出的项目进行华人创始人筛查与投资分析的自动化管线。面向创投尽调场景，从多信源爬取早期项目列表，批量验证创始人华裔背景，输出结构化投资分析与 VC 评分排名。

---

## 覆盖信源

| 信源 | 定位 | 特殊处理 |
|------|------|----------|
| **Pitchbook** | 主信源 | 全部进入筛查 |
| **ARR** | 主信源 | 已过度曝光/成熟项目标记 `SKIP_PUBLIC_HYPE`，跳过深度分析 |
| **LinkedIn 大厂华人离职员工** | 监控型 | 保存快照并比对历史，仅当有新公司时才进入后续分析 |
| **Kickstarter** | 补充型 | 仅取第一页；仅评分 ≥ 9、众筹额 > $1M 且为 AI 原生产品才进入分析，其余标记 `SKIP_KICKSTARTER_FILTER` |

---

## 输出结果怎么看

运行结束后在工作目录生成以下文件：

| 文件 | 说明 |
|------|------|
| `companies.csv` | 阶段0原始数据，含去重后的公司名、榜单评分、赛道、来源、过滤标记等 |
| `scrape_state.json` | 阶段0断点续爬状态（按信源隔离） |
| `linkedin_hires_snapshot.json` | LinkedIn 信源快照，用于下一轮变动比对 |
| `screening.db` | 阶段1 SQLite 检查点，记录每家公司的筛查状态、创始人信息、官网验证结果等 |
| `keywords.json` | 阶段1前置准备生成，包含每家公司 `founder` + `funding` 的搜索 query |
| `investment_analysis.md` | 阶段2投资分析正文。标准公司用深度 Verdict 结构；Kickstarter 项目用简版众筹追踪模板 |
| `final_report.md` | 完整最终报告，包含执行摘要、筛查结果摘要、VC 评分排名表、`investment_analysis.md` 全文 |
| `tavily_results/` | 阶段1/2 所有 Tavily 搜索原始 JSON |
| `exa_results/` | 阶段1/2 所有 Exa 搜索原始 JSON |

**VC 评分排名表**（位于 `final_report.md`）包含五维度分数：Team、Market、Moat、Traction、CapEff，以及总分和 Tier 评级。
- `OVERSEAS_CHINESE`：正常评分进入排名表
- `UNCLEAR`：进入表格但不打分，仅做信息摘要
- `DOMESTIC_CHINESE`：不进入排名表，仅在报告末尾列出名称 + tagline + 创始人
- `NOT_CHINESE`：仅统计数量，不进入表格
- Kickstarter 项目不纳入 VC 评分排名表

---

## 工作流设计

整个流程分为 4 个阶段：

```
启动检查 → 阶段0(数据获取) → 阶段1(筛查) → 阶段2(投资分析) → 阶段3(评分) → 最终报告
   ↓key确认       ↓写入CSV         ↑___________写入检查点 SQLite___________|
```

### 阶段0：数据获取
- 使用 `agent-browser` 爬取 readtheone 榜单页面
- 应用各信源过滤规则（SKIP_PUBLIC_HYPE、SKIP_KICKSTARTER_FILTER、LinkedIn 快照比对）
- 去重后写入 `companies.csv`

### 阶段1：华人创始人筛查
- **前置准备**：运行 `scripts/build_query.py` 生成 `keywords.json`，包含每家公司阶段1所需的 `founder` + `funding` query
- 每批约 **8 家公司**，agent 从 `keywords.json` 读取当前 batch 的 query，执行 Tavily + Exa 搜索
- 按 `references/screening_rules.md` 判断强/弱信号，同步判定 `company_type`（`OVERSEAS_CHINESE` / `DOMESTIC_CHINESE`）
- 弱信号触发 LinkedIn 个人页面验证
- 使用 `scripts/screening_db.py` 写入 SQLite checkpoint，支持断点续跑

### 阶段2：投资分析
- 仅对 `CONFIRMED` 公司执行
- 优先复用阶段1已保存的搜索 JSON，按需补充缺口搜索
- 标准公司覆盖 Team / Market / Moat / Traction / CapEff 五个维度
- Kickstarter 项目使用简版模板追踪
- 追加写入 `investment_analysis.md`

### 阶段3：VC 评分排序
- 基于 `investment_analysis.md` 和已有搜索 JSON 直接评分
- 不发起任何新搜索
- 输出 Markdown 排名表格并组装 `final_report.md`

---

## 核心亮点

- **信源差异化处理**：不同信源有各自准入/过滤规则，避免用同一套逻辑处理成熟度完全不同的项目
- **本土 vs 海外华人区分**：筛查阶段同步判定 `OVERSEAS_CHINESE`（进入深度分析）与 `DOMESTIC_CHINESE`（仅列名单），避免对纯国内项目做无效尽调
- **批量防偷懒机制**：每批 8 家公司、逐批释放上下文、强制进度汇报、PENDING 清零检查，防止 agent 在 100+ 家公司时跳过筛查
- **断点续跑**：阶段0和阶段1均支持 checkpoint（SQLite + JSON 文件），中断后可无缝恢复
- **多 key 自动轮换**：Tavily 和 Exa 均支持主号 + 备用 key，遇到 401/403 立即切换
- **全页 LinkedIn 扫描**：弱信号创始人验证时采用整页关键词扫描，确保 Languages、Education 等信息不被遗漏
- **Agent 灵活驱动**：agent 直接读取 checkpoint 和搜索 JSON 完成分析与报告组装

---

## 使用的工具

| 工具 | 用途 |
|------|------|
| [`tvly`](https://cli.tavily.com) (tavily-cli) | 网络搜索，获取创始团队、融资、产品等信息 |
| [`mcporter`](https://mcp.exa.ai) (Exa MCP) | 神经网络搜索，补充 Tavily 的信息缺口 |
| [`agent-browser`](https://github.com/anthropics/agent-browser) | 网页爬取（readtheone 榜单）、LinkedIn 个人页面验证 |

---

## 参考文档

- `references/data_source_rules.md` — 阶段0多信源规则、提取脚本、过滤逻辑
- `references/screening_rules.md` — 强/弱信号判定、LinkedIn 验证标准、状态转移
- `references/vc_scoring.md` — 五维度权重、评分细则、评级定义
- `references/investment_analysis_template.md` — 投资分析格式模板（含标准 Verdict + Kickstarter 简版）
