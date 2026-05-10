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
- `screening.db` — 阶段1检查点（SQLite）
- `investment_analysis.md` — 阶段2投资分析
- `final_report.md` — 完整最终报告

---

## 整体流程

```
启动检查 → 阶段0(数据获取) → 阶段1(筛查) → 阶段2(投资分析) → 阶段3(评分) → 最终报告
   ↓key确认       ↓写入CSV         ↑___________写入检查点 SQLite___________|
```

---

## 速查：当前阶段该做什么

| 阶段 | 关键动作 | 核心命令 / 文件 |
|------|---------|----------------|
| **阶段0** | 爬取榜单 → 生成 `companies.csv` | `agent-browser eval` + `extract_readtheone.js` |
| **阶段1 准备** | 生成 query | `python scripts/build_query.py` → `keywords.json` |
| **阶段1 初始化** | 导入待筛查公司 | `python scripts/screening_db.py import companies.csv` |
| **阶段1 执行** | 批量搜索 → 写入 checkpoint | `python scripts/screening_db.py upsert --company X ...` |
| **阶段1 续跑** | 查看剩余 | `python scripts/screening_db.py list --status PENDING` |
| **阶段2** | 投资分析 | 按 `references/investment_analysis_template.md` 写 `investment_analysis.md` |
| **阶段3** | 评分排名 | 按 `references/vc_scoring.md` 输出 Markdown 表格 |

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

## Agent 行为约束

以下约束优先级高于一切效率或便利性考虑。若与"提速""自动化""写个脚本"等想法冲突，以此约束为准。

1. **严格执行 skill 的阶段和检查点，不自行创建未定义的脚本或流程**
2. **工具失效时先汇报，由用户决定是跳过、替换还是修复**
3. **阶段1 坚持手动逐批分析，每家公司搜完 snippet 后逐条确认 founder 姓名和公司绑定关系**

---

## 阶段0: 数据获取（网页爬取）

> 支持多信源：Pitchbook、ARR 等。完成后输出 `companies.csv`。

### 通用提取脚本

所有 readtheone 榜单页面（Pitchbook / ARR / LinkedIn / Kickstarter 等）DOM 结构一致，使用同一脚本提取：

```bash
cd "$WORKSPACE"
# Windows 环境：绝对路径传 --file 可能解析失败，优先使用 inline eval
agent-browser eval --file "<skill-dir>/scripts/extract_readtheone.js"
```

> `<skill-dir>` 为 `weekly-recommendation` skill 的根目录。首次执行前请确认该路径。
>
> **Windows 注意**：`agent-browser eval --file "C:/Users/..."` 可能触发 `SyntaxError: Unexpected identifier 'C'`。若遇到此问题，改用 inline eval（将脚本内容直接作为参数传入）。

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

- 同一批次建议 **8 家**公司并行搜索
- 所有原始 JSON 保存到 `tavily_results/` 和 `exa_results/`

---

## 阶段1: 华人创始人筛查

**agent 直接逐批执行**，每批约 8 家公司。

> **防偷懒硬性规则**（agent 必须遵守）：
> 1. **执行前必须先列出 batch 清单**：每批搜索前，先向用户报告"本批处理 X 家公司：A, B, C, D, E"
> 2. **每批执行后必须确认写入 checkpoint**：搜索完成后，逐家确认 `screening_db.py upsert` 已写入，不能漏写
> 3. **禁止跳过任何 PENDING 公司**：未查询确认前，不得假设"剩余都是 NOT_CHINESE"或"这批不用搜了"
> 4. **阶段1结束前必须查询 PENDING 数量**：`list --status PENDING` 结果为零才能进入阶段2
> 5. **进度汇报**：每完成 20-25 家公司，向用户汇报一次当前进度（CONFIRMED / NOT_CHINESE / UNCLEAR / PENDING 各多少家）
> 6. **上下文管理：逐批释放**：
>    - 原始搜索 JSON 已保存到 `tavily_results/` 和 `exa_results/`，磁盘是持久存储
>    - SQLite checkpoint 已保存了所有判定结论，不需要在上下文中重复缓存
>    - **分析完一批、写入 checkpoint 后，即可丢弃该批的原始 snippet 上下文**，需要回溯时从文件系统和数据库读取
>    - 永远只保留"当前 batch 的搜索结果 + 已写入 checkpoint 的统计摘要"在上下文中

**前置准备（阶段1开始前执行一次）**：

运行 `scripts/build_query.py` 生成 `keywords.json`：
```bash
python <skill-dir>/scripts/build_query.py
```

- `keywords.json` 包含每家公司阶段1所需的全部 query（`founder` + `funding`）
- agent **不**在上下文中缓存所有 query，而是按 batch 从 `keywords.json` 读取当前 8 家公司的 query，用完即弃
- 通用名消歧的 keyword 由 `build_query.py` 从 `reason` 字段自动提取，agent 无需在脑中构造 200 条 query

1. **搜索创始团队**：对每家公司同时发起 Tavily + Exa 搜索

   **Query 读取与构造规范（两层策略）**：

   **默认策略**：从 `keywords.json` 读取当前 batch 的 query，格式如下：
   - 基础格式：`{company_name} AI {search_target}`
   - 若公司名为**通用/常见词**（如 Qura, Scale, Apex），自动追加 `reason` 中提取的 **1-2 个核心英文关键词** 消歧：
     `{company_name} AI {keyword} {search_target}`
   - `{search_target}` 阶段1只搜两个：`founder`、`funding`
   - `funding` 同时帮助判断公司阶段和融资背景，Phase 2 复用结果
   - CEO/CTO 等细分职位信息在阶段2如需补充再搜

   **精细策略（Override）**：当默认策略搜索结果出现混淆（如搜到同名大品牌、结果不相关），agent 从 `reason` 字段手动提取 **1-3 个最独特的功能/技术关键词** override：
   - **去掉泛词**：AI、赋能、智能、平台、工具、系统、解决方案
   - **保留核心词**：具体功能、技术栈、产品形态、目标领域
   - Override 格式：`{company_name} {keyword1} {keyword2} {search_target}`

2. **提取 founder 姓名 + 识别中文姓名 + 判定公司类型**：依据 `references/screening_rules.md` 执行
   - **逐条分析 snippet**：每家公司的 Tavily + Exa 结果必须逐条过一遍，不能扫一眼就跳过。在搜索结果中明确标出哪条 snippet 提到了 founder 姓名及职位，同步确认 snippet 中已把该名字和公司绑定
   - 判定中文姓名强/弱信号
   - **同步判定 company_type**：从同一批 snippet 中抓取公司名语言和搜索结果语言，区分 `OVERSEAS_CHINESE` / `DOMESTIC_CHINESE`，判定理由必须写入 `evidence_quote`
   - `founder_verification_layer` 默认记为 `L0_search_snippet`
   - 仅当 Step 1 完全无 founder 信息时，才补充搜索 Crunchbase/LinkedIn（记为 `L1_supplement`）
3. **官网验证（Phase 1.5）**：依据 `references/entity_verification.md` 执行
   - 用 `tvly extract` 批量抓取候选 URL，验证可达性，区分真官网与聚合站
4. **写入检查点**：使用 `scripts/screening_db.py` 写入 SQLite，避免手工追加 CSV 的编码/格式错误。
   ```bash
   python <skill-dir>/scripts/screening_db.py upsert \
     --company "Patlytics" --status "CONFIRMED" --company_type "OVERSEAS_CHINESE" \
     --founder_name "Wilson Wang" --evidence_quote "Wilson Wang, CEO at Patlytics" \
     --verified_website "https://patlytics.ai"
   ```

**阶段1初始化**：
阶段0完成后，一次性将 `companies.csv` 导入 SQLite：
```bash
python <skill-dir>/scripts/screening_db.py import companies.csv
```

**实体验证触发条件**：
- 强信号公司：官网验证（founder 已隐含在 Step 1 中）
- 弱信号公司：官网验证（同上）
- NOT_CHINESE 公司：不验证

**断点续跑**：查询 SQLite 只处理未完成项。
```bash
python <skill-dir>/scripts/screening_db.py list --status PENDING
python <skill-dir>/scripts/screening_db.py list --status UNCLEAR
```
agent 运行时自动跳过 `CONFIRMED`（OVERSEAS/DOMESTIC）/ `NOT_CHINESE`。

> 完整字段定义见 `references/screening_rules.md` → "Checkpoint 字段定义"。
| `updated_at` | TIMESTAMP | 最后更新时间 | — |

---

## 阶段2: 投资分析

**仅对 `CONFIRMED` 且 `company_type = OVERSEAS_CHINESE` 的公司执行。**

`DOMESTIC_CHINESE` 公司不进入 Phase 2，仅在最终报告"本土华人公司名单"中列出。

**语言要求**：所有投资分析、评分表格、最终报告必须使用**中文**撰写（公司名、人名、引用原文可保留英文）。

agent 按 `references/investment_analysis_template.md` 模板撰写。以下为**强制 checklist**，agent 必须逐条落实：

### 投资分析写作 checklist

按 `references/investment_analysis_template.md` 模板撰写，每家 CONFIRMED 公司必须包含 8 个模块（公司标题 → 一句话描述 → 官网+亮点 → Trigger → 基本信息表格 → 公司介绍 → Verdict → 创始团队）。

**写法红线**：
- 不写"根据公开信息""数据显示"等废话开头，直接进数据
- 用具体数字和名字，不用"很多""不错"等模糊词
- Verdict 表格的「核心依据」列用 `•` 分点，`<br>` 换行，每维度 2-4 条
- 总评部分（5 句左右），包含核心优势、核心风险、退出预期

### 信息缺口补充搜索

**优先复用**阶段1的搜索 JSON。缺口补充搜索必须覆盖 `references/vc_scoring.md` 所需的全部五个维度：

**Query 构造**：沿用 Phase 1 格式 `{company_name} {keyword1} {keyword2} {search_target}`，每次只加 1-2 个词。

| 维度 | 搜索目标 |
|------|---------|
| **Team** | `background`、`LinkedIn`、`education`、`previous exit`。若阶段1未明确 CEO/CTO 信息，补充搜索 `CEO`、`CTO` |
| **Market** | `TAM`、`competition`、`market size` |
| **Moat** | `patent`、`technology`、`open source` |
| **Traction** | 按阶段判断：早期用 `product`、`launch`、`breakthrough`；有收入信号用 `revenue`、`ARR` |
| **CapEff** | `funding`、`valuation`（优先复用 Phase 1 的 funding 搜索结果） |

agent 根据 Phase 1 已获取的融资/产品信息判断公司阶段，选择对应的 Traction 搜索词。

### 输出

- 标准信源公司：按上述 8 模块写入 `investment_analysis.md`
- Kickstarter 项目：采用简版追踪模板，不参与五维评分

> **阶段3 不再发起任何新搜索**，所有评分依据必须在阶段2收集完毕。

---

## 阶段3: VC 评分排序

**语言要求**：评分表格、执行摘要、排名说明必须使用**中文**（公司名、人名、引用原文可保留英文）。

**OVERSEAS_CHINESE 公司正常评分；UNCLEAR 公司进入表格但不打分**；DOMESTIC_CHINESE 和 NOT_CHINESE 不进入排名表。（Kickstarter 项目不纳入 VC 评分排名表，仅在 `investment_analysis.md` 中保留简版追踪。）

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
   - 筛查结果摘要（含 NOT_CHINESE 数量和 DOMESTIC_CHINESE 数量）
   - VC 评分排名表格（仅 OVERSEAS_CHINESE + UNCLEAR；不含 Kickstarter 简版项目）
   - 本土华人公司名单（DOMESTIC_CHINESE）：列出名称 + tagline + 创始人，不评分不分析
   - `investment_analysis.md` 全文（仅含 OVERSEAS_CHINESE 标准深度分析 + Kickstarter 简版追踪）

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
| 批量执行中断 | 下次运行时从 SQLite checkpoint 查询状态，自动跳过已完成 |
| 实体验证全部失败 | 标 `UNCLEAR`，`error: entity_verification_failed`，不进 Phase 2 |
| `agent-browser eval` JSON 二次字符串化 | `json.load()` 返回字符串而非对象时，做二次解析兼容：`if isinstance(data, str): data = json.loads(data)` |
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
