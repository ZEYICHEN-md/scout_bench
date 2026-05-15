# sector-prospector

赛道标的深度挖掘工具。从任意赛道主题出发，通过多轮垂直搜索发现早期、尚未被大众媒体广泛曝光的项目，输出可直接对接 `weekly-recommendation` 管线进行华人创始人筛查的 `companies.csv`。

---

## 为什么需要这个工具

传统搜索的问题：在 Google 搜"AI Agent startup"，前 3 页全是 OpenAI、Anthropic、Manus 等已经被反复报道的公司。真正的早期项目——可能刚刚完成种子轮、可能还在 GitHub 上只有几百颗星、可能是某个大厂工程师的 side project——淹没在信息噪声中。

**sector-prospector 的核心能力**：
- 从具体赛道出发，通过"锚点直接搜索 -> 反向扩散 -> 维度补充"三阶段渐进式挖掘
- Tavily + Exa 双引擎互补：Tavily 找融资新闻，Exa 挖语义深度
- 自动过滤 public hype，保留真正早期的信号
- 输出直接兼容 weekly-recommendation 的 CSV 格式

---

## 核心工作流

```
Phase 0: 信息采集（Intent Capture）
  - 判断赛道粒度：太宽泛则引导拆分，够具体则确认
  - 采集用户已知线索：关键概念、参考公司、信号来源、投资逻辑
  - 输出：user_inputs.json

Phase 1: 赛道解构（Sector Decomposition）
  - 在已确认的赛道上再细分 3-6 个子方向
  - 每个子方向配 3-5 个技术关键词
  - 输出：sector_map.json

Phase 2: 深度挖掘（Deep Prospecting）
  - 对每个子赛道执行多轮垂直搜索（Anchor & Expand）
  - Round 1: 锚点直接搜索
  - Round 2: 反向扩散（从已知项目找竞品/投资者/创始人）
  - Round 3: 维度补充
  - 输出：raw_prospects.json + 原始搜索 JSON

Phase 3: 聚合与初筛（Aggregation & Screening）
  - 全局去重、Public Hype 过滤、公司信息确认
  - 生成 companies.csv（兼容 weekly-recommendation）
  - 生成 prospects_report.md（投资人扫描报告，中文）
```

---

## 用户输入指南

**不需要结构化输入，自然语言描述即可。** Agent 会自动从 prompt 中提取所有可用信息。

### 可以包含的信息

| 信息类型 | 说明 | 示例表达 |
|---------|------|---------|
| **赛道主题**（必须） | 你想挖掘的方向 | "智能体沙箱"、"机器人灵巧手" |
| **参考公司** | 已知的一个锚点项目 | "类似 e2b 的项目"、"对标 Daytona" |
| **关键概念** | 你关注的技术名词 | "WASM runtime"、"浏览器自动化" |
| **信号来源** | 你偏好的创业信号 | "PhD 创业项目"、"大厂离职创业" |
| **投资逻辑** | 你看好这个方向的理由 | "看好 LLM 代码执行的安全隔离需求" |
| **排除方向** | 不想看的子方向 | "不做浏览器自动化"、"排除已上市云厂商" |

### 输入示例

**最简输入**（只给赛道）：
> "帮我挖一下智能体沙箱的项目"

**丰富输入**（附带参考公司和概念）：
> "找一下类似 e2b 的项目，就是给 AI Agent 做代码执行沙箱的，关注开源转商业和大厂离职创业的信号"

**宽泛输入**（agent 自动处理）：
> "帮我看看 AI Agent 领域有什么值得投的早期项目"

### 不需要做的

- 不需要提供结构化 JSON 或表格
- 不需要确认子赛道拆分（全自动）
- 不需要补充额外信息（未提及的字段 agent 自动留空）
- 不需要说"请执行 Phase 0 然后 Phase 1"——直接描述需求即可

---

## 案例：智能体沙箱赛道挖掘

以下用"智能体沙箱 / Agent Sandbox"作为案例，展示每个 Phase 的具体操作和中间产物。

### Phase 0: 信息采集

**用户输入**：
> "帮我挖一下智能体沙箱的项目，关于 AI Agent 训练、AI Agent 运行环境这些"

**Agent 判断粒度**：
- "智能体沙箱"包含具体技术名词（sandbox、runtime）-> **合适，不拆分**
- 从 prompt 直接提取信息，不过度推断：
  - `sector_theme`: "智能体沙箱"（**不**上升到"AI Agent 基础设施"）
  - `key_concepts`: ["sandbox", "agent training", "agent runtime"]

**输出**：[`user_inputs.json`](examples/user_inputs.json)

---

### Phase 1: 赛道解构

**搜索策略**：query 保持与"智能体沙箱"同等粒度

```bash
tvly search "agent sandbox product types approaches" --json --max-results 10 --depth basic --time-range year
tvly search "agent sandbox different implementations" --json --max-results 10 --depth basic --time-range year
mcporter call 'exa-full.web_search_exa(query: "agent sandbox technical approaches architectures", numResults: 10, type: "auto")'
```

**从搜索结果中识别细分方向**：

| 子赛道 | 识别依据 |
|--------|---------|
| 代码执行沙箱 | 多篇文章提到 e2b、Daytona，核心是让 LLM 安全运行 Python/JS |
| 浏览器沙箱 | 提到 headless browser、web agent 操作网页 |
| WASM 轻量级沙箱 | 提到 WebAssembly、毫秒级启动，适合高频调用 |
| 安全策略层 | 提到 permission control、behavior audit，企业刚需 |

**输出**：[`sector_map.json`](examples/sector_map.json)

```json
{
  "sector_theme": "智能体沙箱 / Agent Sandbox",
  "sub_sectors": [
    {
      "name": "代码执行沙箱 / Code Sandbox",
      "key_concepts": ["code execution", "Python sandbox", "JS sandbox", "REPL"]
    },
    {
      "name": "浏览器沙箱 / Browser Sandbox",
      "key_concepts": ["browser automation", "headless browser", "web agent"]
    },
    {
      "name": "WASM轻量级沙箱 / WASM Runtime",
      "key_concepts": ["WebAssembly", "WASM runtime", "lightweight sandbox"]
    },
    {
      "name": "安全策略与隔离 / Security Policy Layer",
      "key_concepts": ["sandbox policy", "permission control", "behavior audit"]
    }
  ]
}
```

**关键**：sector_map 由 agent 全自动生成并直接使用，不中断用户确认。所有子赛道最终都会被挖掘，按信号强度优先调度。

---

### Phase 2: 深度挖掘

以"代码执行沙箱"子赛道为例，展示 Anchor & Expand 三阶段。

**Round 1: 锚点直接搜索**

如果用户提供了参考公司（如 e2b）：

```bash
# Tavily + Exa 双引擎并行
# Tavily（偏新闻融资）
tvly search "e2b alternatives competitor" --json --max-results 10 --depth basic --time-range year > tavily_results/code_sandbox_r1_e2b.json

# Exa（偏语义深度）
mcporter call 'exa-full.web_search_exa(query: "e2b similar products different approach", numResults: 10, type: "auto")' > exa_results/code_sandbox_r1_e2b.json
```

如果用户没有提供参考公司，用技术概念搜索：

```bash
tvly search "code execution sandbox startup" --json --max-results 10 --depth basic --time-range year
mcporter call 'exa-full.web_search_exa(query: "Python sandbox for LLM agents", numResults: 10, type: "auto")'
```

**Round 2: 反向扩散**

从 Round 1 发现的项目（如 Daytona、CodeSandbox、Modal）反向搜索：

```bash
# 找竞争对手
tvly search "Daytona competitors alternatives" --json --max-results 10 --depth basic --time-range year
mcporter call 'exa-full.web_search_exa(query: "companies like Modal Labs code execution", numResults: 10, type: "auto")'

# 找投资者的其他 portfolio
tvly search "Daytona funding investor portfolio" --json --max-results 10 --depth basic --time-range year

# 找创始人背景
tvly search "Daytona founders ex-Google ex-OpenAI" --json --max-results 10 --depth basic --time-range year
```

**Round 3: 维度补充**

```bash
# 查缺补漏：学术/开源信号
tvly search "code sandbox open source github trending" --json --max-results 10 --depth basic --time-range year
tvly search "ex-Google ex-OpenAI code sandbox startup founded" --json --max-results 10 --depth basic --time-range year
```

**信息提取示例**：

从 Tavily 结果中发现 **Daytona**：
```json
{
  "company_name": "Daytona",
  "website": "https://daytona.io",
  "funding_stage": "Series A ($24M)",
  "founders": "Ivan Burazin",
  "differentiation": "开源开发环境管理器，支持多语言、多基础设施的代码执行沙箱",
  "source_query": "code execution sandbox startup",
  "source_engine": "tavily",
  "sub_sector": "代码执行沙箱 / Code Sandbox"
}
```

从 Exa 结果中发现 **Metoro**（不那么热门但技术扎实）：
```json
{
  "company_name": "Metoro",
  "website": "https://metoro.io",
  "funding_stage": "unknown",
  "differentiation": "为 AI Agent 提供安全的生产环境代码执行能力",
  "source_query": "AI agent code execution sandbox",
  "source_engine": "exa",
  "sub_sector": "代码执行沙箱 / Code Sandbox"
}
```

**融资信息时效性校验**：

发现 Modal 时，某篇文章写"Series A+"。执行验证搜索：
```bash
tvly search "Modal funding series valuation 2025 2026" --json --max-results 3 --depth basic --time-range year
```
发现实际已是 **$87M Series B**，更新信息并标注 `信息已更新`。

---

### Phase 3: 聚合与初筛

**1. 全局去重**

按 `company_name` 不区分大小写去重。 Daytona 在"代码执行沙箱"和"安全策略层"都出现 -> 合并 track 为 `"代码执行沙箱, 安全策略层"`。

**2. Public Hype 过滤**

- OpenAI、Anthropic、xAI -> **硬性排除**（估值 $1B+，家喻户晓）
- Modal（$87M Series B）-> **软性标记**：保留在 CSV 中，note 标注 `"非早期，Series B+，已过种子窗口"`
- Daytona（Series A，$24M）-> **保留**（仍处于早期窗口）

**3. 公司信息确认搜索**

对每个保留的公司：
```bash
tvly search "Daytona funding founders overview" --json --max-results 5 --depth basic --time-range year
```

确认创始人背景、最新融资、产品形态，修正 Phase 2 中可能过时的信息。

**4. 亮点关键词提取**

从确认搜索结果中提取公司自身特点：

| 公司 | 亮点关键词 |
|------|-----------|
| Daytona | `开源`, `多语言支持`, `BYOC`, `开发环境即代码` |
| Metoro | `生产级安全`, `AI Agent 专用`, `动态权限控制` |

**5. 生成输出文件**

- [`companies.csv`](examples/companies.csv) — 直接兼容 weekly-recommendation
- [`prospector_notes.json`](examples/prospector_notes.json) — 挖掘路径审计
- [`prospects_report.md`](examples/prospects_report.md) — 投资人扫描报告（中文，按推荐度排序）

---

## 文件结构

```
sector-prospector/
├── SKILL.md                          # 核心 skill 文件（< 400 行，流程骨架）
├── README.md                         # 本文档（案例说明）
├── references/
│   ├── discovery_strategies.md       # Phase 2 搜索策略（Anchor & Expand）
│   ├── public_hype_filter.md         # Public hype 过滤规则
│   ├── output_schema.md              # 所有输出文件的格式规范
│   ├── phase0_sector_splitting.md    # 赛道过大时的拆分方法论
│   ├── search_engine_strategy.md     # 双引擎策略、CLI 规范、错误处理
│   └── report_generation.md          # Phase 3 评分规则和报告格式
└── evals/
    └── evals.json                    # 测试用例
```

---

## 与 weekly-recommendation 的衔接

```
sector-prospector
    |
    v
companies.csv  ---->  weekly-recommendation Phase 1-3
    |                      |
    |                      v
    |               final_report.md（华人创始人筛查 + 投资分析）
    |
    v
prospects_report.md（初筛报告，按推荐度排序）
```

- `companies.csv` 格式与 weekly-recommendation 完全一致
- `source` 字段记录挖掘来源，帮助 Phase 1 优化搜索策略
- `track` 字段（子赛道）可作为最终报告的分类维度

---

## 使用示例

```
用户：帮我挖一下智能体沙箱的项目，关于 AI Agent 训练、AI Agent 运行环境这些

Agent（全自动流程）：
1. 从 prompt 自动提取赛道主题和关键概念
2. Phase 0：判断赛道粒度，够具体则直接进入 Phase 1；过宽则自动扫描并选择子赛道
3. Phase 1：自动解构赛道，生成 sector_map.json
4. Phase 2：逐个子赛道执行多轮垂直搜索（Anchor & Expand）
5. Phase 3：全局去重、Public Hype 过滤、生成 companies.csv + prospects_report.md
6. 汇报：共发现 47 个项目，S 档 3 个、A 档 12 个...
```

---

## 关键设计决策

**1. 为什么从具体出发，而不是从宽泛主题拆分？**

"AI Agent"可以拆成 Runtime、Orchestration、Memory、Tooling 等 10+ 方向，但每个方向深挖需要 50+ 次搜索。从"智能体沙箱"出发，只需在 sandbox 内部细分（代码沙箱/浏览器沙箱/WASM 沙箱），搜索更聚焦，结果质量更高。

**2. 为什么用 Tavily + Exa 双引擎？**

- Tavily 像 TechCrunch：适合找融资新闻、产品发布
- Exa 像语义雷达：适合挖不那么"热门"但技术扎实的早期项目
- 双引擎在 Round 1/2 并行，最大化覆盖；Round 3 单引擎即可，节省成本

**3. 为什么 Public Hype 用"软性标记"而非"硬性排除"？**

- sector-prospector 的定位是**信息发现和收集**，不是投资决策
- Series B+ 公司在非常小众的赛道或近期有重大技术突破时，仍可能有投资价值
- 最终判断交给 weekly-recommendation 的完整分析流程

**4. 为什么 Phase 1 完成后不中断用户确认？**

sector-prospector 的定位是**高效发现和信息收集**，而非替用户做投资决策。所有子赛道最终都会被挖掘，按信号强度优先调度。如果用户事后发现某个子方向不相关，可在输出报告中忽略该部分，而不是在挖掘中途打断流程。全自动执行减少摩擦，提升挖掘效率。
