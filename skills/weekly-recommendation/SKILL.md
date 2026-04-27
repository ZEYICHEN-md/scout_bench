---
name: weekly-recommendation
description: |
  创业投资尽调与华人创始人筛查管线。当用户提到「周度推荐」「工作流周度推荐」「挖一下这周工作流的项目」时，务必使用本 skill。
  支持从网页爬取公司列表、批量筛查创始人背景、生成投资分析与 VC 评分排名。
  自动处理断点续跑和批量并行。

---

## 环境配置（首次使用）

### 1. API Keys

**启动时自动加载**。agent 在开始任何搜索前，依次检查以下 `.env` 文件：

```
<skill-dir>/.env
<skill-dir>/../skill_test/.env
<当前工作目录>/.env
~/.env
```

支持多组 key 轮换（在 `.env` 中配置主号 + `*_SECONDARY`）：

```env
TAVILY_API_KEY=tvly-dev-xxxx
TAVILY_API_KEY_SECONDARY=tvly-dev-yyyy
EXA_API_KEY=64bfe768-xxxx
EXA_API_KEY_SECONDARY=27d98e7c-xxxx
```

**轮换策略**：每连续 **5 次请求**后自动切换到同一服务商的备用 key。

**确认流程**：加载后向用户报告检测到的 keys，请求确认：

```
检测到以下 API Keys：
  - Tavily: tvly-dev-xxxx（主号）+ tvly-dev-yyyy（备用）
  - Exa: 64bfe768-xxxx（主号）+ 27d98e7c-xxxx（备用）
轮换策略：每5次请求切换
是否使用上述 keys 开始筛查？[Y/n]
```

**未检测到 key 时**：暂停并向用户请求 key，不继续执行搜索。

### 2. LinkedIn 登录态

**配置方式**（只需一次）：

```bash
agent-browser --session-name linkedin --headed open https://www.linkedin.com/login
# ...在弹出窗口中完成登录...
agent-browser --session-name linkedin close
```

**启动前预检查**：agent 先验证 session 是否有效（详见 `references/screening_rules.md`）。若 session 无效，跳过弱信号验证，将相关公司标记为 `UNCLEAR`，不阻塞流程。

---

## 工作目录结构

**创建工作目录**（agent 直接执行，并记住该路径）：

```bash
export WORKSPACE="screening_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$WORKSPACE"
echo "$WORKSPACE"
```

> **重要**：Claude 的 Bash 工具每次调用都是独立 shell。后续**每一次 Bash 调用**都必须以 `cd "$WORKSPACE"` 开头，确保所有文件（`tavily_results/`、`exa_results/`、`companies.csv` 等）都写入正确目录。

**目录规范**：
- `tavily_results/` — 阶段1/2 所有 Tavily 搜索原始 JSON
- `exa_results/` — 阶段1/2 所有 Exa 搜索原始 JSON
- `companies.csv` — 阶段0原始数据
- `scrape_state.json` — 阶段0断点续爬状态
- `chinese_screening_checkpoint.csv` — 阶段1检查点
- `investment_analysis.md` — 阶段2投资分析
- `final_report.md` — 完整最终报告

---

## 整体流程

```
启动检查 → 阶段0(数据获取) → 阶段1(筛查) → 阶段2(投资分析) → 阶段3(评分) → 最终报告
   ↓key确认       ↓写入CSV         ↑___________写入检查点CSV___________|
```

---

## 启动检查清单

agent 在开始筛查前必须逐项确认：

```
□ CLI 工具：tvly（tavily-cli）已安装且在 PATH 中（含 `tvly extract` 子命令）
□ CLI 工具：mcporter（Exa MCP）已安装且可调用
□ CLI 工具：agent-browser 已安装且在 PATH 中
□ API Keys：已加载 Tavily key（含备用）
□ API Keys：已加载 Exa key（含备用）
□ LinkedIn：session 有效（不在登录页），或已标记为无效
□ 工作目录：已创建并后续 Bash 调用均会 cd 进入
□ 用户已确认开始（Y/n）
```

> 若某项工具缺失，agent 报告问题并请求用户安装或提供替代方案，不盲目继续。

---

## 阶段0: 数据获取（网页爬取）

> 支持多信源：Pitchbook、ARR 等。完成后输出 `companies.csv`。

### 通用提取脚本

所有 readtheone 榜单页面（Pitchbook / ARR / LinkedIn / Kickstarter 等）DOM 结构一致，使用同一脚本提取：

```bash
cd "$WORKSPACE"
agent-browser eval --file "<skill-dir>/scripts/extract_readtheone.js"
```

> `<skill-dir>` 为 `weekly-recommendation` skill 的根目录。首次执行前请确认该路径。

### 支持信源

| 信源 | 目标页面 |
|------|----------|
| **Pitchbook** | `https://trends.readtheone.com/projects?page=1&source=Pitchbook&track=&chinese=` |
| **ARR** | `https://trends.readtheone.com/projects?page=1&source=arr&track=&chinese=true` |
| **LinkedIn 大厂华人离职员工** | `https://trends.readtheone.com/projects?source=Linkedin%E5%A4%A7%E5%8E%82%E5%8D%8E%E4%BA%BA%E7%A6%BB%E8%81%8C%E5%91%98%E5%B7%A5&track=&chinese=true` |
| **Kickstarter** | `https://trends.readtheone.com/projects?source=kickstarter&track=&chinese=true` |

> **详细规则**（提取脚本、各信源特殊处理、监控机制、去重写入规范）见 `references/data_source_rules.md`。
>
> 要点速览：
> - ARR 信源中过度曝光/水上项目标记为 `SKIP_PUBLIC_HYPE`，不进入阶段1
> - LinkedIn 信源为**监控型**，对比历史快照，有新增才进入后续分析
> - Kickstarter 信源**仅爬第一页**，仅当评分 ≥ 9、众筹额 > $1M 且为 AI 原生产品时才进入阶段1，其余标记 `SKIP_KICKSTARTER_FILTER`
> - agent 人工过滤非真实公司名（如 `AI视频广告平台` 等描述性条目）
> - 多信源合并后按 `company_name` 去重，`source` 列合并（如 `Pitchbook|ARR`）

---

## 搜索工具调用规范

### Tavily

**首选**：`tvly search "{query}" --json --max-results 5 --depth basic`

**备选**（curl）：

```bash
curl -s -X POST https://api.tavily.com/search \
  -H "Content-Type: application/json" \
  -d "{\"api_key\":\"$TAVILY_API_KEY\",\"query\":\"{query}\",\"max_results\":5,\"search_depth\":\"basic\",\"include_answer\":true}"
```

### Exa

**首选**：`mcporter call 'exa.web_search_exa(query: "{query}", numResults: 5)'`

**备选**（curl）：

```bash
curl -s -X POST https://api.exa.ai/search \
  -H "Content-Type: application/json" \
  -H "x-api-key: $EXA_API_KEY" \
  -d "{\"query\":\"{query}\",\"numResults\":5,\"useAutoprompt\":true,\"type\":\"auto\"}"
```

### 限速与错误处理

| 场景 | 处理方式 |
|------|----------|
| 429/503 | 等 15 秒重试；同 key 连续 3 次失败后切换备用 key |
| 401/403 | 立即切换 key |
| 所有 key 均失败 | 标记 `UNCLEAR`，`error: "all_keys_rate_limited"` |
| 单家公司搜索失败 | 记录 `error`，`status` 保持 `PENDING`，不阻塞整批 |

### 并发

- 同一批次建议 **5 家**公司并行搜索
- 所有原始 JSON 保存到 `tavily_results/` 和 `exa_results/`

---

## 阶段1: 华人创始人筛查

**agent 直接逐批执行**，每批约 5 家公司：

1. **搜索创始团队**：对每家公司同时发起 Tavily + Exa 搜索

   **Query 构造规范**：
   - 从 `companies.csv` 的 `reason` 字段提取 **1-3 个最独特的功能/技术关键词**
   - **去掉泛词**：AI、赋能、智能、平台、工具、系统、解决方案
   - **保留核心词**：具体功能、技术栈、产品形态、目标领域
   - Query 格式：`{company_name} {keyword1} {keyword2} {search_target}`
   - Phase 1 的 `{search_target}` 每家公司轮换使用：`founder`、`CEO`、`CTO`、`founding team`、`funding`
     - `funding` 同时帮助判断公司阶段和融资背景，Phase 2 复用结果

   **示例**：
   | 公司 | reason | 提取关键词 | query |
   |------|--------|-----------|-------|
   | Patlytics | AI 赋能的知识产权工作流增强工具 | IP workflow | `Patlytics IP workflow founder` |
   | Patlytics | AI 赋能的知识产权工作流增强工具 | IP workflow | `Patlytics IP workflow funding` |
   | Mastra | 用于构建自主 AI 代理和工作流的开源 TS 框架 | TypeScript agent framework | `Mastra TypeScript agent framework CEO` |
   | neuroClues | 通过追踪眼球数据流畅感知、诊断神经病变的智能相机 | eye tracking neurology | `neuroClues eye tracking neurology co-founder` |

2. **提取 founder 姓名 + 识别中文姓名**：依据 `references/screening_rules.md` 判定强/弱信号
   - 从 Step 1 的 Tavily/Exa snippet 中提取 founder 姓名，同步确认 snippet 中已把该名字和公司绑定（如 "CEO at Patlytics"）
   - 判定中文姓名强/弱信号
   - `founder_verification_layer` 默认记为 `L0_search_snippet`
   - 仅当 Step 1 完全无 founder 信息时，才补充搜索 Crunchbase/LinkedIn（记为 `L1_supplement`）
3. **官网验证（Phase 1.5）**：依据 `references/entity_verification.md` 执行
   - 用 `tvly extract` 批量抓取候选 URL，验证可达性，区分真官网与聚合站
4. **写入检查点**：立即追加写入 `chinese_screening_checkpoint.csv`

**实体验证触发条件**：
- 强信号公司：官网验证（founder 已隐含在 Step 1 中）
- 弱信号公司：官网验证（同上）
- NOT_CHINESE 公司：不验证

**断点续跑**：读取已有 checkpoint，跳过 `CONFIRMED` / `NOT_CHINESE`，只处理 `PENDING` / `UNCLEAR`。

**Checkpoint CSV 新增字段**（追加到现有列后）：

| 列名 | 类型 | 含义 | 示例 |
|------|------|------|------|
| `verified_website` | string | 验证通过的官网 URL，空表未通过 | `https://patlytics.ai` |
| `website_verification_status` | enum | `verified` / `aggregator_only` / `unreachable` / `not_attempted` | `verified` |
| `founder_verification_layer` | enum | `L0_search_snippet` / `L1_supplement` / `failed` | `L0_search_snippet` |
| `evidence_quote` | string | ≤200 字的证据原文（含 founder + company 同框） | `"Paul Lee, CEO at Patlytics, was previously at..."` |
| `evidence_url` | string | evidence_quote 的来源 URL | `https://www.linkedin.com/in/paul-lee-patlytics` |

---

## 阶段2: 投资分析

**仅对 `CONFIRMED` 状态的公司执行。**

agent 按 `references/investment_analysis_template.md` 模板撰写：

1. **优先复用**阶段1的搜索 JSON
2. **缺口补充搜索**（标准信源必须覆盖 `references/vc_scoring.md` 所需的全部五个维度）：

   **Query 构造**：沿用 Phase 1 格式 `{company_name} {keyword1} {keyword2} {search_target}`，每次只加 1-2 个词。

   | 维度 | 搜索目标 |
   |------|---------|
   | **Team** | `background`、`LinkedIn`、`education`、`previous exit` |
   | **Market** | `TAM`、`competition`、`market size` |
   | **Moat** | `patent`、`technology`、`open source` |
   | **Traction** | 按阶段判断：早期用 `product`、`launch`、`breakthrough`；有收入信号用 `revenue`、`ARR` |
   | **CapEff** | `funding`、`valuation`（优先复用 Phase 1 的 funding 搜索结果） |

   agent 根据 Phase 1 已获取的融资/产品信息判断公司阶段，选择对应的 Traction 搜索词。

3. 追加写入 `investment_analysis.md`（Kickstarter 项目采用简版追踪模板，不参与五维评分）

> **阶段3 不再发起任何新搜索**，所有评分依据必须在阶段2收集完毕。

---

## 阶段3: VC 评分排序

**CONFIRMED 公司正常评分；UNCLEAR 公司进入表格但不打分**；NOT_CHINESE 不进入排名表。（Kickstarter 项目不纳入 VC 评分排名表，仅在 `investment_analysis.md` 中保留简版追踪。）

agent **直接基于** `investment_analysis.md` 和阶段1/2已保存的搜索 JSON 进行评分/汇总，**不发起额外搜索**。依据 `references/vc_scoring.md` 输出 Markdown 表格。

### 表格结构

```markdown
| 排名 | 公司 | 总分 | Team | Market | Moat | Traction | CapEff | 评级 | 状态 | 已知信息摘要 |
|------|------|------|------|--------|------|----------|--------|------|------|-------------|
| 1 | Spirit AI | 8.25 | 9.0 | 9.0 | 8.0 | 7.0 | 7.0 | S | CONFIRMED | - |
| - | Patlytics | - | - | - | - | - | - | - | UNCLEAR | 创始人 Paul Lee / Arthur Jen（弱信号，待 LinkedIn 验证）|
```

**UNCLEAR 公司处理**：
- 分数和评级列全部填 `-`
- "已知信息摘要"列基于阶段1搜索结果，用一句话总结：tagline + 创始人姓名/背景线索 + 信息缺口
- 不占用排名序号，列在 CONFIRMED 公司之后

---

## 执行入口

当用户要求「筛查华人创始人」「周度推荐」「Pitchbook 工作流」时：

1. **启动检查**：确认 CLI 工具、API keys、LinkedIn session、工作目录
2. **阶段0**：爬取或读取 `companies.csv`
3. **阶段1**：批量搜索并判定华人创始人身份，写入 checkpoint
4. **阶段2**：对 CONFIRMED 公司撰写投资分析
5. **阶段3**：生成 VC 评分排名
6. **最终报告**：组装 `final_report.md`
   - 执行摘要
   - 筛查结果摘要
   - VC 评分排名表格（不含 Kickstarter 简版项目）
   - `investment_analysis.md` 全文（含标准深度分析 + Kickstarter 简版追踪）

> 最终报告由 agent 直接组装，不存在 `report_builder.py`。

---

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| 单家公司搜索失败 | 记录 `error` 字段，`status` 保持 `PENDING`，不阻塞整批 |
| API 限速（429/503）| 等 15 秒重试；同 key 连续 3 次失败后切换备用 key |
| API 401/403 | 立即切换 key（可能是 key 被撤销） |
| 所有 key 均失败 | 标记该公司为 `UNCLEAR`，`error: "all_keys_rate_limited"` |
| 无法确认华人身份 | `status` 设为 `UNCLEAR` |
| LinkedIn session 无效 | 跳过验证，标记 `UNCLEAR`，`error: "linkedin_session_invalid"` |
| 批量执行中断 | 下次运行时从检查点 CSV 读取状态，自动跳过已完成 |
| 实体验证全部失败 | 标 `UNCLEAR`，`error: entity_verification_failed`，不进 Phase 2 |
| `tvly extract` 全部失败 | 标 `UNCLEAR`，`error: tvly_extract_failed`，fallback 到 search snippet only |

---

## 参考文档

| 文件 | 说明 |
|------|------|
| `references/data_source_rules.md` | 阶段0多信源规则：提取脚本、ARR/SKIP_PUBLIC_HYPE、LinkedIn 监控机制 |
| `references/screening_rules.md` | 强/弱信号、排除规则、领英验证标准、状态转移 |
| `references/vc_scoring.md` | 五维度权重、评分细则、评级定义 |
| `references/investment_analysis_template.md` | 投资分析格式模板：公司介绍、Verdict 结构、信号标签 |
| `references/entity_verification.md` | 实体验证规则：官网识别、创始人验证 |
