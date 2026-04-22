---
name: sector-prospector
description: |
  赛道标的深度挖掘与早期项目发现工具。当用户提到「赛道挖掘」「sector tracking」「deal sourcing」「找某个赛道的项目」「挖掘赛道标的」「early stage discovery」「某个领域的创业公司」「某某方向有什么值得投的」「帮我看看某某赛道」时，务必使用本skill。
  支持从任意赛道主题出发，通过多轮垂直搜索解构子赛道、挖掘尚未被public hype的早期项目，输出可直接对接weekly-recommendation管线进行华人创始人筛查的companies.csv。
  自动处理断点续跑和批量并行搜索。

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

**确认流程**：加载后向用户报告检测到的 keys，请求确认。未检测到 key 时暂停并向用户请求，不继续执行搜索。

---

### 2. 工作目录

**创建工作目录**（agent 直接执行，并记住该路径）：

```bash
export WORKSPACE="prospecting_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$WORKSPACE"
echo "$WORKSPACE"
```

> **重要**：Claude 的 Bash 工具每次调用都是独立 shell。后续**每一次 Bash 调用**都必须以 `cd "$WORKSPACE"` 开头，确保所有文件写入正确目录。

**目录规范**：
- `user_inputs.json` — Phase 0 用户输入的基石信息
- `sector_map.json` — Phase 1 赛道解构结果
- `prospector_checkpoint.json` — 断点续跑状态
- `tavily_results/` — Phase 2 所有 Tavily 搜索原始 JSON
- `exa_results/` — Phase 2 所有 Exa 搜索原始 JSON
- `raw_prospects.json` — Phase 2 挖掘出的原始项目列表
- `companies.csv` — Phase 3 最终输出（兼容 weekly-recommendation）
- `prospector_notes.json` — Phase 3 每个项目的挖掘路径和来源 query
- `prospects_report.md` — Phase 3 投资人扫描报告（中文）

---

## 整体流程

```
启动检查 -> Phase 0(信息采集) -> Phase 1(赛道解构) -> Phase 2(深度挖掘) -> Phase 3(聚合初筛)
   | key确认       | user_inputs.json    | sector_map.json   | __________checkpoint_________|
```

---

## 启动检查清单

agent 在开始挖掘前必须逐项确认：

- [ ] CLI 工具：`tvly` 已安装且在 PATH 中
- [ ] CLI 工具：`mcporter` 已安装且可调用
- [ ] API Keys：已加载 Tavily key（含备用）
- [ ] API Keys：已加载 Exa key（含备用）
- [ ] 工作目录：已创建并后续 Bash 调用均会 `cd` 进入
- [ ] 用户已确认开始（Y/n）
- [ ] 用户已提供赛道主题
- [ ] Phase 0 信息采集已完成（或用户选择跳过）

若某项工具缺失，agent 报告问题并请求用户安装或提供替代方案，不盲目继续。

---

## Phase 0: 信息采集（Intent Capture）

**目标**：在正式搜索前，确定一个**足够具体的赛道起点**，并收集用户的投资视角和已有线索。

### 核心原则：从具体出发

本 skill 的设计假设是：**初始赛道越具体，挖掘质量越深**。我们不试图一次性挖掘"整个 AI 行业"，而是聚焦一个可操作的细分方向。

**赛道粒度判断标准**：

| 粒度 | 例子 | 评价 |
|------|------|------|
| 太宽泛 | "AI"、"人工智能"、"大模型" | 搜索query过宽，只能返回头部公司 |
| 偏宽泛 | "AI Agent基础设施" | 可以尝试，但建议进一步拆分 |
| 合适 | "智能体沙箱"、"Agent Runtime"、"机器人灵巧手" | 具体技术名词，query精准 |
| 很具体 | "基于WASM的LLM执行环境"、"端到端自动驾驶感知" | 直接开搜，无需再拆 |

**快速判断规则**：
- 如果 `sector_theme` 是**单个品类词**（AI、机器人、大模型、SaaS）-> **太宽泛**
- 如果 `sector_theme` 包含**具体技术名词**（sandbox、runtime、WASM、perception、RLHF）-> **合适**
- 如果**不确定**，执行一次快速验证搜索：`tvly search "{theme} startup seed funding" --json --max-results 5 --depth basic`，如果前5条结果全是头部大厂 -> **太宽泛**

### 赛道引导与拆分（赛道过大时）

当用户输入被判定为"太宽泛"或"偏宽泛"时，agent 自动执行全景扫描，从真实市场信号中提取结构化线索并聚类成 3-6 个子赛道选项，然后**自动选择最相关、信号最强的 1-2 个子赛道**作为挖掘起点，直接进入 Phase 1。

**自动选择标准**：
- 融资信号最强（近期集中获得种子轮的方向优先）
- 与用户初始 prompt 语义最接近
- 技术差异化最明确（不与其他子赛道高度重叠）

**详细流程**见 `references/phase0_sector_splitting.md`。

**核心原则**：不要凭知识库硬编选项，而是通过搜索从真实市场信号中**提取结构化线索，再聚类成选项**。

### 自动信息采集（赛道已经够具体时）

agent 直接从用户 prompt 中提取所有可用信息，**不主动询问**，不中断流程：
- `key_concepts`：从 prompt 中的技术名词自动提取
- `reference_companies`：从"类似 XX""对标 YY"等表达中识别
- `signal_sources`、`investment_thesis`、`excluded_areas`：如 prompt 中未提及，留空即可

将采集结果写入 `$WORKSPACE/user_inputs.json`，立即进入 Phase 1。

### 可采集的信息项

| 字段 | 说明 | 示例 |
|------|------|------|
| `sector_theme` | 赛道主题（必须，必须够具体） | "智能体沙箱"、"Agent Sandbox" |
| `key_concepts` | 用户已知的关键概念/技术名词 | `["code sandbox", "browser sandbox", "WASM runtime"]` |
| `reference_companies` | 参考公司/对标项目 | `["e2b", "Daytona", "Multica"]` |
| `signal_sources` | 用户关注的信号来源方向 | "PhD创业项目"、"大厂离职创业"、"开源转商业" |
| `investment_thesis` | 投资逻辑/角度 | "看好LLM代码执行的安全隔离需求" |
| `excluded_areas` | 不想看的子方向 | `["只做静态分析不做动态执行", "已上市云厂商的沙箱服务"]` |
| `preferred_dimensions` | 偏好的分类维度 | "技术实现方式"、"应用场景" |

### 采集方式

**从用户初始 prompt 中直接提取，不做过度推断**。

将采集结果写入 `$WORKSPACE/user_inputs.json`。

详见 `references/output_schema.md` 中的 user_inputs 结构。

---

## Phase 1: 赛道解构（Sector Decomposition）

**目标**：在一个**已经具体的赛道**上，进一步往下拆分出 3-6 个更细的子方向，每个子方向配 3-5 个技术关键词，为 Phase 2 的多轮垂直搜索提供精确的导航。

### 核心原则：在具体之上再细分

Phase 0 已经确保赛道起点够具体（如"智能体沙箱"）。Phase 1 的任务不是"从 AI 行业拆到 Agent Infra"，而是"从智能体沙箱拆到代码沙箱、浏览器沙箱、安全隔离等更细的切口"。

**示例对比**：

| 错误做法 | 正确做法 |
|-----------|-----------|
| 用户说"智能体沙箱" -> 拆成"Agent Runtime/Sandbox / Orchestration / Memory"（把 sandbox 上升到整个 infra 层） | 用户说"智能体沙箱" -> 拆成"代码执行沙箱 / 浏览器沙箱 / 文件系统隔离 / WASM Runtime / 安全策略层"（在 sandbox 内部再细分） |

### 搜索策略

搜索 query **必须保持与 `sector_theme` 同等粒度**，不能再上升到更宽泛的词。

**搜索模板**：

```bash
# 全景搜索（并行发起）
tvly search "{赛道} product types approaches" --json --max-results 10 --depth basic
tvly search "{赛道} different implementations" --json --max-results 10 --depth basic
mcporter call 'exa.web_search_exa(query: "{赛道} technical approaches architectures", numResults: 10)'

# 趋势与空白搜索
tvly search "{赛道} emerging approaches new methods" --json --max-results 8 --depth basic
tvly search "{赛道} underserved use cases" --json --max-results 8 --depth basic

# 学术/开源信号（可选）
tvly search "{赛道} open source implementations github" --json --max-results 5 --depth basic
tvly search "{赛道} research prototype commercialization" --json --max-results 5 --depth basic
```

### 子赛道生成逻辑

从搜索结果中识别"在同一个具体赛道内，有哪些不同的实现方式/应用场景/技术路线"。

**常见的细分维度**（在一个具体赛道内）：

| 维度 | 例子（以"智能体沙箱"为例） |
|------|---------------------------|
| 技术实现方式 | Container-based / VM-based / WASM-based / Process-based |
| 应用场景 | 代码执行 / 浏览器自动化 / 文件操作 / API 调用 |
| 安全层级 | 完全隔离 / 半隔离 / 策略控制 / 审计监控 |
| 部署形态 | 云端托管 / 本地运行 / 边缘部署 / 嵌入式 |
| 目标用户 | 开发者工具 / 企业安全 / 终端消费者 |

**用户输入的影响**：

| 用户输入 | 对Phase 1的影响 |
|----------|----------------|
| `key_concepts` | 直接映射到子赛道 |
| `reference_companies` | 分析其技术实现方式，作为子赛道划分的参考 |
| `preferred_dimensions` | 优先使用该维度拆分 |
| `excluded_areas` | 直接排除 |
| `investment_thesis` | 影响子赛道排序 |

### 输出格式

将分析结果写入 `$WORKSPACE/sector_map.json`。

**约束**：
- 子赛道数量控制在 **3-6 个**，每个子赛道是同一具体赛道内的不同细分方向。
- 每个子赛道的 `key_concepts` 应包含 **3-5 个** 技术名词，粒度比 `sector_theme` 更细。
- `search_queries` 必须保持赛道粒度，不能上升到更宽泛的词。

详见 `references/output_schema.md` 中的 sector_map 结构。

---

## Phase 2: 深度挖掘（Deep Prospecting）

**目标**：基于 sector_map，对每个子赛道执行多轮垂直搜索，尽可能发现早期、未被曝光的项目。

### 读取 Checkpoint

如果 `$WORKSPACE/prospector_checkpoint.json` 存在，读取已完成和进行中的子赛道，跳过已完成的。

### 搜索引擎策略

**双引擎分层使用**：

| 环节 | 引擎策略 | 原因 |
|------|---------|------|
| Phase 1 赛道解构 | 单引擎（Tavily 为主） | 目的是理解赛道结构，不需要交叉验证 |
| Phase 2 Round 1 锚点直接搜索 | **必须双引擎并行** | 发现项目的核心轮次，Tavily 偏新闻融资、Exa 偏语义深度，互补覆盖 |
| Phase 2 Round 2 反向扩散 | **必须双引擎并行** | 从已知项目找竞品/投资者/创始人，需要最大覆盖 |
| Phase 2 Round 3 维度补充 | 单引擎即可（Tavily） | 查缺补漏，如果 Round 1/2 已发现足够项目，快速扫一遍即可 |

**详细 CLI 调用规范、错误处理、并发控制**见 `references/search_engine_strategy.md`。

### 搜索执行流程

读取 `references/discovery_strategies.md` 中的 Anchor & Expand 模型，对每个子赛道执行多轮搜索。

**用户输入的影响**：

| 用户输入 | 对Phase 2的影响 |
|----------|----------------|
| `reference_companies` | 立即触发组合 E（交叉验证）：搜索竞争对手、同类项目、投资者的其他 portfolio |
| `signal_sources` | 优先执行对应的搜索组合 |
| `key_concepts` | 这些概念在 Phase 2 中作为核心搜索词，不需要从零推导 |
| `investment_thesis` | 影响搜索的重点方向 |

### 信息提取

从搜索结果中识别潜在项目，提取以下字段：

```json
{
  "company_name": "公司名（优先使用官方品牌名）",
  "website": "官网URL",
  "funding_stage": "融资阶段线索",
  "founders": "创始人姓名",
  "differentiation": "一句话差异化亮点",
  "source_query": "发现该公司的搜索query",
  "source_engine": "tavily 或 exa",
  "sub_sector": "所属子赛道"
}
```

**融资信息时效性校验**：

搜索结果中的融资信息可能过时。当提取到融资信息时：

1. **执行验证搜索**：
   ```bash
   tvly search "{company_name} funding series valuation 2025 2026" --json --max-results 3 --depth basic
   ```

2. **信息可信度标注**：
   - 验证结果与之前矛盾 -> 以最新结果为准，标注 `信息已更新`
   - 融资信息来自 1 年以上前的文章且无法验证 -> 标注 `融资信息可能过时，待确认`
   - 无法确认任何融资信息 -> 标注 `融资信息待确认`

3. **不因为信息过时而排除公司** — sector-prospector 的定位是信息发现，不是投资决策。

**去重**：同一子赛道内，按 `company_name` 去重（不区分大小写）。

**写入**：每完成一个子赛道，将结果追加写入 `$WORKSPACE/raw_prospects.json`，并更新 `prospector_checkpoint.json`。

---

## Phase 3: 聚合与初筛（Aggregation & Screening）

**目标**：去重、过滤 public hype、按格式输出可直接对接 weekly-recommendation 的 companies.csv 和中文报告。

### 步骤

1. **全局去重**
   - 读取 `raw_prospects.json`
   - 按 `company_name` 全局去重（不区分大小写）
   - 若同一公司出现在多个子赛道，合并 `sub_sector` 为逗号分隔列表

2. **Public Hype 过滤**
   - 依据 `references/public_hype_filter.md` 的规则，排除已过度曝光的项目
   - 对不确定的公司，用搜索验证

3. **公司信息确认搜索**
   - 对每个保留的公司，执行一次定向确认搜索
   - 验证并修正融资信息，补充创始人背景
   - 详见 `references/report_generation.md`

4. **亮点关键词提取**
   - 必须是公司自身的技术/产品特点，而非搜索锚点词
   - 详见 `references/report_generation.md`

5. **生成 companies.csv**
   - 格式严格兼容 weekly-recommendation
   - 详见 `references/output_schema.md`

6. **生成 prospector_notes.json**
   - 记录每个项目的完整挖掘路径
   - 详见 `references/output_schema.md`

7. **生成 prospects_report.md（投资人扫描报告）**
   - 按推荐度排序，全文中文
   - 详见 `references/report_generation.md`

---

## 执行入口

当用户要求「挖掘赛道」「找某个方向的项目」「sector deal sourcing」「某某赛道的早期公司」时：

1. **启动检查**：确认 CLI 工具、API keys、工作目录
2. **Phase 0**：自动采集用户输入（从 prompt 提取，不主动询问），自动判断赛道粒度，如过宽则自动扫描并选择子赛道，产出 `user_inputs.json`
3. **Phase 1**：结合用户输入执行赛道解构，产出 `sector_map.json`，直接进入 Phase 2
4. **Phase 2**：基于 sector_map 和用户输入，逐个子赛道执行深度挖掘，保存原始 JSON 和 checkpoint
5. **Phase 3**：全局去重、Public Hype 过滤、生成 `companies.csv`、`prospector_notes.json`、`prospects_report.md`
6. **汇报**：向用户汇报挖掘结果摘要（公司总数、各子赛道分布、Top 5 项目），并告知文件路径

> **关键**：Phase 0 自动提取用户 prompt 中的投资视角和已有线索；Phase 1 完成后不中断流程，直接进入 Phase 2。整个挖掘过程从用户给出 prompt 到产出报告全自动完成，无需中途确认。

---

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| 单条 query 搜索失败 | 记录 error，继续处理其他 query |
| API 限速（429/503）| 指数退避：15s -> 30s -> 60s；同 key 连续 3 次失败后切换备用 key |
| API 401/403 | 立即切换 key |
| 搜索超时（无响应 >30s）| 终止当前 query，标记超时，继续下一批 |
| 所有 key 均失败 | 暂停当前子赛道，记录 checkpoint，向用户报告 |
| 用户未提供赛道主题 | 询问用户想挖掘哪个赛道 |
| 挖掘结果为空 | 检查 query 是否过窄，向用户建议扩大或调整赛道主题 |

---

## 参考文档

| 文件 | 说明 |
|------|------|
| `references/discovery_strategies.md` | Phase 2 的 Anchor & Expand 搜索模型、6 大搜索组合策略 |
| `references/public_hype_filter.md` | Public hype 过滤规则：已上市、融资额、估值阈值、常见独角兽名单 |
| `references/output_schema.md` | 所有输出文件的格式规范（JSON 结构、CSV 格式、checkpoint 结构） |
| `references/phase0_sector_splitting.md` | 赛道过大时的拆分方法论：全景扫描 -> 提取线索 -> 聚类 -> 用户选择 |
| `references/search_engine_strategy.md` | 双引擎使用策略、CLI 调用规范、限速与错误处理、并发控制 |
| `references/report_generation.md` | Phase 3 的评分规则、报告格式、亮点关键词提取规范 |
