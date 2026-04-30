---
name: exa-company-miner
description: >
  面向VC投资人的公司发现与尽调工具。基于 Exa Websets 提供的 AI 驱动搜索和智能信息验证能力，
  通过自然语言描述你关注的赛道、筛选条件和投资偏好，
  自动完成多轮搜索、信息交叉验证和信号识别，输出结构化的候选公司分析报告。
  当你需要：挖掘某赛道初创公司、创建投资标的名单、持续监控赛道机会、
  或对目标公司做投资前快速尽调时使用。
  工作流：对话确认需求 → Websets 建候选名单 → 搜索补充信号数据 → 输出投资分析简报。
  支持华人创始人限定（可选）、自定义筛选条件、持续监控。
---

# Exa Company Miner — VC 投资端公司挖掘

## 定位

本 Skill 面向**投资机构和独立投资人**，帮助你在看新赛道或扫描已知赛道时，快速找到值得深入调研的标的公司。

基于 **Exa Websets** 构建 — Exa 旗下的 AI 驱动语义搜索平台，可通过自然语言创建公司名单，并利用 AI 逐条验证匹配度和抽结构化信息，搜索质量远超普通关键词搜索。

你要做的就是用自然语言描述你想挖的方向。Skill 会自动完成搜索、验证、分析全流程。

## 为什么用 Exa Websets

Exa Websets 提供业内最强的语义搜索 + AI 级逐条验证能力，能理解"华人创始人""有 VC 背书的早期初创公司"这类复杂条件并自动匹配验证，搜索质量、精度和速度远超传统关键词搜索或手动筛选。

## 环境配置

本 Skill 使用 **Exa 两大服务**，共用同一个 API Key：

- **Exa Websets MCP**：用于 Step 2/3 批量发现候选公司 + AI 验证 + 富化
- **Exa Search MCP**：用于 Step 4 针对单家公司补充深度信息

两种方式（MCP / Python SDK）共用同一个 API Key，底层能力完全一致：

- **Mode A — MCP（推荐）**：工具直接暴露给 Agent 调用，在 Claude Code / Cursor / VS Code 等支持 MCP 的环境中开箱即用
- **Mode B — Python SDK**：通过 `pip install exa-py` 安装，代码调用 `exa.websets` 接口

### 第 0 步：自动检测

按以下顺序检测，需同时满足 **Websets MCP** 和 **Search MCP** 才算就绪：

1. **检测 Websets MCP**
   - 检查当前环境中是否有 `create_webset`、`list_websets` 等工具
   - 有 → Websets MCP 可用
   - 没有 → 检查是否已安装 `claude` CLI（`claude --version`），有的话进入第 3 步自动配置
   - 没有 CLI → 继续检测 Mode B（Python SDK）

2. **检测 Exa Search MCP**
   - 检查当前环境中是否有 `web_search_exa`、`company_research_exa` 等工具
   - 有 → Search MCP 可用
   - 没有 → 检查是否已安装 `mcporter`（`mcporter list exa`），有的话进入第 3 步自动配置
   - 没有 mcporter → 提示用户需安装

3. **检测 Mode B（Python SDK，备选）**
   - 检查 `python3 -c "import exa_py"` 是否成功
   - 检查环境变量 `EXA_API_KEY` 是否已设置
   - 都满足 → Mode B 可用，进入工作流（但 Step 4 仍需 Search MCP）
   - SDK 已安装但 Key 未设置 → 进入第 1 步获取 Key
   - SDK 未安装 → 引导用户安装
### 第 1 步：向用户请求配置

如果检测未通过，发送：

> **⚠️ 检测到未配置 Exa Websets**
>
> 这是此 Skill 的核心引擎，让我能用 AI 级语义搜索和智能验证帮你挖掘公司、生成分析报告。
>
> **配置只需两步（约 2 分钟）：**
> 1. 前往 **[dashboard.exa.ai/api-keys](https://dashboard.exa.ai/api-keys)** 登录（支持 Google/GitHub），创建并复制 API Key
> 2. 把 Key 发给我，我来完成其余安装
>
> 是否现在配置？（回复「是」或「跳过」即可）

**等待用户回复：**
- 肯定词（是/配/ok/好/行）→ 进入第 2 步
- 否定词（跳过/不用/算了）→ 提示无法使用 Websets，但 Exa 其他搜索功能仍可用
- 其他 → 理解为肯定

### 第 2 步：获取 API Key

> 请前往 **[dashboard.exa.ai/api-keys](https://dashboard.exa.ai/api-keys)** 登录并复制 API Key，直接粘贴给我。

收到 Key 后，**优先尝试 Mode A，失败自动降级到 Mode B。**

### 第 3 步：自动安装（按模式路由）

#### Mode A — MCP 方式（推荐）

MCP 方式零代码量，工具直接暴露给 Agent，开箱即用。

本 Step 需配置 **两个 MCP 服务**：

##### 3-A. Exa Websets MCP（Step 2/3 批量挖掘公司）

**Claude Code**（有终端执行能力）直接执行：
```bash
claude mcp add --transport http websets "https://websetsmcp.exa.ai/mcp?exaApiKey=用户的KEY"
```

**VS Code / Windsurf / 其他支持 MCP 的客户端**，指导在 MCP 配置中添加：
```json
{
  "url": "https://websetsmcp.exa.ai/mcp?exaApiKey=用户的KEY"
}
```

**Claude Desktop**，指导编辑配置文件（macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`；Windows: `%APPDATA%\Claude\claude_desktop_config.json`），添加：
```json
{
  "mcpServers": {
    "websets": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://websetsmcp.exa.ai/mcp?exaApiKey=用户的KEY"]
    }
  }
}
```

##### 3-B. Exa Search MCP（Step 4 单家公司补充信息）

**方式 1 — mcporter（推荐，无需 API Key）**

先安装 mcporter，然后：
```bash
mcporter config add exa https://mcp.exa.ai/mcp
```

验证：
```bash
mcporter list exa
```

配置完成后可用工具：`web_search_exa`、`company_research_exa`、`get_code_context_exa`。

高级工具（可选，支持更丰富的过滤和深度搜索）：
```bash
mcporter config add exa-full "https://mcp.exa.ai/mcp?tools=web_search_exa,web_search_advanced_exa,get_code_context_exa,deep_search_exa,crawling_exa,company_research_exa,people_search_exa,deep_researcher_start,deep_researcher_check"
```

**方式 2 — 原生 MCP 配置**

如果不使用 mcporter，可直接在 MCP 客户端中添加：
```json
{
  "url": "https://mcp.exa.ai/mcp"
}
```

或通过 npx remote：
```json
{
  "mcpServers": {
    "exa-search": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.exa.ai/mcp"]
    }
  }
}
```

> 两个 MCP 配置完成后，大多需要**重启客户端**才能生效。

#### Mode B — Python SDK

如果用户更倾向代码调用，或 MCP 方式不可用：

```bash
pip install exa-py
```

设置环境变量：
```bash
export EXA_API_KEY="用户的KEY"        # macOS/Linux
$env:EXA_API_KEY="用户的KEY"          # Windows PowerShell
```

验证：
```python
from exa_py import Exa
exa = Exa()  # 自动读取 EXA_API_KEY
print("Exa SDK ready")
```

### 验证和反馈

> **✅ Exa 配置完成**
>
> - **Websets MCP**：可用（工具：`create_webset`、`list_websets`、`create_search` 等）
> - **Search MCP**：可用（工具：`web_search_exa`、`company_research_exa` 等）
>
> 可以开始挖掘。

遇到问题时：
- Websets 免费额度用完后需升级到 [Websets Pro Plan](https://exa.ai/pricing)
- Search MCP（mcporter 方式）无需额外 API Key，免费可用
- 官方文档：[exa.ai/docs](https://exa.ai/docs/)

## 工作流总览

```
1. 对话确认赛道方向和筛选条件
2. Websets 搜索创建候选名单（持久化 state.json）
3. 追加搜索扩大覆盖（追加到 state.json）
4. 补充信息搜索（追加到 state.json）
5. 触发信号识别（写入 state.json）
6. 输出分析报告（.md 文件）
7. 信源校验与引用
```

### 流程稳定性 — 中间状态持久化

Websets 是异步系统，整个工作流可能持续数分钟到十几分钟。**必须在每步完成后把结果写入本地 JSON 文件**，以防会话中断或超时。

**目录结构**：
```
exa_mining_output/
  {赛道名}_{日期}/        ← 每轮挖掘一个独立目录
    config.json           ← Step 1 确认的筛选条件
    state.json            ← 工作流状态（每步更新）
    final_report.md       ← Step 6 输出
```

**state.json 结构**：
```json
{
  "step": "step2",                         // 当前进行到第几步
  "step_status": "running",                // running / done / error
  "webset_id": "ws_abc123",
  "webset_dashboard_url": "https://...",
  "companies_found": 12,
  "companies": [...],                      // 已发现公司的结构化数据
  "error": null,                           // 如有错误则记录
  "last_updated": "2026-04-05T10:30:00Z"
}
```

**持久化时机**：
| 时刻 | 写入内容 |
|------|---------|
| Step 1 确认后 | config.json：赛道、筛选条件、搜索关键词 |
| 创建 Webset 后立即 | state.json：webset_id、dashboard_url、step="step2" |
| wait_until_idle 完成后 | state.json + companies 数组、step_status="done" |
| 每轮追加搜索完成后 | state.json：companies 追加新条目 |
| Step 4 补充搜索完成后 | state.json：每家公司追加搜索结果 |
| Step 5 信号识别完成后 | state.json：每家公司追加 signals 和 priority |

**恢复策略**：
- 如果用户重新发起请求，或会话中断后重启，**先检查 `exa_mining_output/{赛道名}_{日期}/state.json` 是否存在**。
- 如果存在且 step_status 是 `done` → 告知用户上次已完成，展示结果。
- 如果存在且 step_status 是 `running` → 告知用户上次在哪个步骤中断，从该步恢复。
- 如果不存在 → 从头开始。

---

## Step 1: 对话确认需求

### 1.1 引导用户提供 Prompt 模板

如果用户只是泛泛地说"帮我挖一下公司"或没有明确赛道，主动引导并提供 prompt 模板：

> "你可以按照以下格式告诉我你想挖的方向，或者直接描述你的需求：
>
> **Prompt 模板参考：**
>
> ```
> 赛道方向：[你用自然语言描述你在看的领域，比如 AI 代码安全、具身智能]
> 公司阶段：[早期到成长期 / 只看早期 / 不限 — 不说则默认早期到成长期]
> 华人限定：[是 / 否 — 不说则默认是]
> VC 背书：[是 / 否 — 不说则默认是]
> 其他要求：[可选，比如只看欧洲公司、必须有大厂背景、排除 SaaS 等等]
> ```
>
> 你也可以直接用一句话描述，比如：
> - `'帮我挖一下 AI Agent Security 赛道的华人创业公司，重点关注快到了下一轮融资窗口的'`
> - `'我在看具身智能方向，不限制创始人背景，早期到成长期都看'`
> - `'帮我找 AI 医疗影像赛道有知名 VC 投资的公司，创始人不限'`
>
> 请告诉我你的需求，我会帮你拆解搜索策略。"

**如果用户描述得足够清楚（赛道明确），直接进入 1.3 确认筛选条件。**
**如果用户一句话就说了赛道（如"AI Agent 支付"），不要重复问赛道，直接进入 1.2 拆关键词 → 1.3 确认筛选条件。**
**如果用户完全没说赛道，才引导填写 prompt 模板。**

### 1.2 收集赛道方向

将用户的自然语言赛道描述转成多条**英文搜索变体**（所有搜索使用英文关键词）：

例如用户说"AI Agent Security"，拆成：
- "AI agent security"
- "LLM security"
- "AI safety infrastructure"

输出给用户的结果使用中文。

### 1.3 确认筛选条件

**如果用户在 prompt 模板中已明确选择了所有条件，可以跳过确认直接汇总。** 否则，**通过对话确认以下筛选条件**：

> "请确认以下筛选条件，你可以选择默认值或自定义：
>
> **1. 华人创始人限定**：是否只看华人创始人/华人团队的公司？（默认：是，支持华裔、大陆、港澳台、双重国籍）
>    - A. 是，只看华人团队 — 默认
>    - B. 不限创始人背景
>
> **2. 公司阶段**：你关注哪个阶段的公司？（默认：早期到成长期都覆盖）
>    - A. 早期到成长期（Pre-seed 到 Series C）— 默认
>    - B. 只看早期（Pre-seed / Seed / Pre-A / A-round）
>    - C. 不限阶段
>    - D. 自定义：___________
>
> **3. VC 背书**：是否只看有知名 VC/加速器投资的公司？（默认：是，质量更高）
>    - A. 是，只看被知名 VC/知名加速器背书的 — 默认，如 a16z、Sequoia、benchmark、YC 等
>    - B. 不限，也包括 bootstrapped 或天使轮机会
>
> **4. 其他要求**（可选）：有没有其他额外筛选条件、关注维度、排除项或偏好？
>    比如：特定地域偏好、排除某些类型、关注开源项目、关注特定技术领域、必须有大厂背景等。
>    没有的话留空即可。"

等待用户回复。根据用户的回复，灵活调整搜索策略和 criteria。

### 1.4 什么是华人？（仅在选择"华人限定"时适用）

**采用并集策略，宁可多筛几家，不可漏掉一家。** 只要以下**任一条件**成立，就将该公司纳入候选：

1. 创始人姓名为中文拼音（如 Zhang, Li, Wang, Chen, Liu, Yang 等）
2. 页面提到 "Chinese", "Chinese-American", "ethnic Chinese", "华人" 等
3. 创始人教育背景提到中国大陆高校（清华/北大/浙大/中科大/复旦/上交等）
4. 创始人前工作经历在中国大厂（Baidu, Alibaba, Tencent, ByteDance, 字节跳动, Xiaomi, Huawei 等）
5. LinkedIn 页面显示创始人中文名
6. 公司团队页面提到华人团队或华人创始人

条件满足**任一**即可纳入候选。遇到不确定的标注 `"likely"` 或 `"uncertain"` 但依然保留。

### 1.5 确认完成后

汇总筛选条件，向用户展示：

> "好的，搜索条件已确认：
> - **赛道**：[赛道名]
> - **英文搜索词**：[关键词列表]
> - **公司阶段**：[用户选择]
> - **华人限定**：[是/否]
> - **VC 背书**：[是/否]
> - **其他要求**：[用户指定的附加条件，如无则显示无]
>
> 现在开始搜索。"

## Step 2: Websets 搜索创建候选名单

### 2.1 保存配置

首先将 Step 1.5 确认的结果写入 `config.json`：

```json
{
  "track": "AI Agent Security",
  "search_queries": ["AI agent security", "LLM security", "AI safety infrastructure"],
  "stage": "early to growth",
  "chinese_founder": true,
  "vc_backed": true,
  "additional": ""
}
```

### 2.2 创建 Webset

根据当前可用模式选择对应方式：

#### Mode A — MCP 工具调用

使用 `create_webset` 工具，参数：

- **entityType**: `"company"`
- **criteria**: 动态组装，基于 Step 1 确认的条件
- **enrichments**: 仅保留基础字段（见下方）

组装逻辑：

```
criteria:
  - "[赛道关键词]"                                          ← 赛道描述（必须）
  - "[公司阶段条件]"                                        ← 根据用户选择
  - "founder or co-founder of Chinese or ethnic Chinese descent"  ← 仅华人限定=是时
  - "backed or invested by a well-known or top-tier venture capital firm or startup accelerator such as Sequoia, a16z, Y Combinator, benchmark, General Catalyst, or similar professional VC/accelerator"  ← 仅 VC 背书=是时
  - "[用户附加条件]"                                        ← 用户要求的其他条件，如有
```

**示例 — 早期到成长期 + 华人 + VC 背书**：

```
criteria:
  - "company building AI agent security, LLM security, or AI safety products"
  - "startup or growth-stage company spanning Pre-seed to Series C"
  - "founder or co-founder of Chinese or ethnic Chinese descent"
  - "backed or invested by a well-known or top-tier venture capital firm or startup accelerator such as Sequoia, a16z, Y Combinator, benchmark, General Catalyst, or similar professional VC/accelerator"
```

**示例 — 成长期 + 不限背景（未选华人 + 未选 VC 背书）**：

```
criteria:
  - "company building embodied AI or humanoid robot products"
  - "startup or growth-stage company spanning Pre-seed to Series C"
```

Enrichments（基础字段，不超 10 个以保证准确率）：

```
Company name (text)
Company website URL (url)
Founder/CEO name (text)
Is the founder or co-founder of Chinese or ethnic Chinese descent? Answer: Yes/No/Uncertain with brief explanation and source (text)
Latest funding stage (Pre-seed, Seed, Series A, Series B, Unknown) (options)
Total funding raised if available (number)
Company headquarters location (city, country) (text)
Founding year or approximate founding date (date)
Company description - what do they build and who are their customers? (text)
```

> 富化字段只保留基础信息（公司名/官网/创始人/背景/融资/总部/年份），因为字段越多准确率越低。其他信息（创始人前经历、论文、合作增长指标等）由后续 Step 4 针对性补充。

#### Mode B — Python SDK 调用

```python
from exa_py import Exa
from exa_py.websets.types import CreateWebsetParameters, CreateEnrichmentParameters
import json

exa = Exa()  # 自动读取 EXA_API_KEY

webset = exa.websets.create(
    params=CreateWebsetParameters(
        search={
            "query": "AI company building agent security and LLM safety products",
            "count": 50,
            "criteria": [
                {"description": "startup or growth-stage company spanning Pre-seed to Series C"},
                {"description": "founder or co-founder of Chinese or ethnic Chinese descent"},
                {"description": "backed or invested by a well-known venture capital firm or accelerator"}
            ],
            "entity": {"type": "company"}
        },
        enrichments=[
            CreateEnrichmentParameters(description="Company name", format="text"),
            CreateEnrichmentParameters(description="Company website URL", format="url"),
            CreateEnrichmentParameters(description="Founder/CEO name", format="text"),
            CreateEnrichmentParameters(description="Is the founder or co-founder of Chinese or ethnic Chinese descent? Yes/No/Uncertain with brief explanation", format="text"),
            CreateEnrichmentParameters(description="Latest funding stage", format="options", options=[
                {"label": "Pre-seed"}, {"label": "Seed"}, {"label": "Pre-A"},
                {"label": "Series A"}, {"label": "Series B"}, {"label": "Series C"}, {"label": "Unknown"}
            ]),
            CreateEnrichmentParameters(description="Total funding raised in USD", format="number"),
            CreateEnrichmentParameters(description="Company headquarters location (city, country)", format="text"),
            CreateEnrichmentParameters(description="Founding year", format="date"),
            CreateEnrichmentParameters(description="Company description - what they build and who are their customers", format="text"),
        ]
    )
)

print(f"Webset ID: {webset.id}")
print(f"Dashboard: {webset.dashboard_url}")
```

### 2.3 等待搜索完成

**Websets 是异步系统**，创建或追加搜索后状态为 `running`，必须等待变为 `idle` 后才能获取完整结果。

**Mode A（MCP）**：
- 调用 `get_webset(webset_id)` 轮询 status 字段，每 5 秒一次，直到 status 变为 `"idle"`
- 设置合理超时（如 5 分钟），超时则向用户报告进度

**Mode B（SDK）**：
```python
webset = exa.websets.wait_until_idle(webset.id, timeout=600, poll_interval=5)
```

**超时处理**：等待过程中可每 5 分钟检查一次进度，如果超时仍未 idle，说明查询复杂。此时：
- `list_webset_items` 获取已有结果（Websets 是边搜边出的），展示进度给用户
- 询问用户是否继续等待或就用当前结果

### 2.4 保存状态 + 展示进度

Webset idle 后：

1. **保存 state.json**：
```json
{
  "step": "step2",
  "step_status": "done",
  "webset_id": "ws_abc123",
  "webset_dashboard_url": "https://websets.exa.ai/ws_abc123",
  "companies_found": 12,
  "companies": [...],
  "error": null,
  "last_updated": "2026-04-05T10:30:00Z"
}
```

2. **向用户汇报进度并询问是否追加**：

> "第一次搜索完成，在 [dashboard链接](url) 找到 **12 家**公司。
>
> 是否需要追加搜索以覆盖更多？
> - **不追加**：当前结果已够用
> - **追加 1 轮**：用赛道近义词变体搜索（如 'LLM security' → 'AI safety'）
> - **追加 2 轮**：近义词 + 去掉公司阶段限制
>
> 请确认追加轮数。"

### 数据读取注意事项

**MCP 获取结果**：
- 调用 `list_webset_items(webset_id)` 获取条目
- 如需分页（items 超过限制），继续用 cursor 翻页
- Company 名称在 `item.properties.company.name`
- URL 在 `item.properties.url`
- Enrichment 结果在 `item.enrichments[]` 数组里，每项只有 `enrichment_id`（字符串 ID），需要用 webset 对象上的 `enrichments[]` 做 ID→description 映射

**SDK 获取结果**：
```python
# 获取 enrichment ID 到描述的映射
desc_map = {e.id: e.description for e in webset.enrichments}

# 分页读取所有条目
for item in page.data:
    company_name = item.properties.company.name
    url = item.properties.url
    for enr in item.enrichments:
        desc = desc_map[enr.enrichment_id]    # ID → 人类可读描述
        value = enr.result                     # 永远是 list[str] 或 None
```

## Step 3: 追加搜索 — 扩大候选名单

Step 2 首次搜索完成后，**询问用户是否追加**：

> "第一次搜索完成，找到 X 家公司。是否需要追加搜索以覆盖更多？
> - **不追加**：当前结果已够用
> - **追加 1 轮**：用赛道近义词变体搜索（如 'LLM security' → 'AI safety'）
> - **追加 2 轮**：近义词 + 去掉公司阶段限制
>
> 请确认追加轮数。"

#### 追加搜索执行流程

用户确认后，每轮追加搜索按以下步骤执行：

1. **调用追加搜索**
   - Mode A（MCP）：`create_search`，沿用首次创建时的 criteria 逻辑
   - Mode B（SDK）：`exa.websets.searches.create(webset_id=ws_id, params={"query": "...", "count": 50, "criteria": [...], "entity": {"type": "company"}})`

2. **等待追加搜索完成**
   - Mode A：轮询 `get_search` 检查 completion=100
   - Mode B：`exa.websets.wait_until_idle(webset_id)`

3. **对新条目执行 enrichment**
   - 追加搜索不会自动携带首次的 enrichment，必须显式调 `create_enrichment`（MCP）或 `exa.websets.enrichments.create()`（SDK）
   - 传入与首次创建时相同的 enrichment 描述和 format

4. **更新 state.json**：companies 数组追加新条目，记录 `last_updated`

**如果追加搜索返回 0 条新公司** → 告知用户该关键词组合未找到新结果，询问是否换一个关键词再试或直接结束搜索阶段。

### 3.1 多轮关键词搜索（主要补充手段）

用 Step 1.2 中拆解的**英文关键词变体**，通过 `create_search` 对每轮关键词进行独立搜索，补充候选名单。

**策略**：

| 轮次 | 搜索范围 | 示例（以 AI Agent Security 为例） |
|------|---------|-------------------------------|
| 第 1 轮 | 主关键词 × 阶段限定 | "AI agent security startups series A", "LLM security seed round" |
| 第 2 轮 | 近义词 / 子赛道 | "AI model guardrails startup", "LLM red team security company" |
| 第 3 轮 | 放宽阶段限制 | "AI agent security infrastructure company" |

每轮搜索使用相同的 **criteria**（华人限定、VC 背书等条件保持一致），通过 `create_search` 追加到同一个 Webset。

**每轮搜索后**，确认搜索完成后（`get_search` 检查 completion=100），自动调用 `create_enrichment` 对新增条目抽取基础信息（字段与首次创建时相同）。

### 3.2 榜单策略（可选补充）

多轮关键词搜索完成后，**可选尝试**查找权威榜单进一步补充。不是必须步骤，但能挖到已被行业认可的优质标的。

搜索该赛道中是否有行业分析机构、媒体或研究机构发布的代表性公司榜单。

搜索query示例：
```
"[赛道关键词] top startups list ranking 2024 2025"
"[赛道关键词] best startups emerging companies list"
"[赛道关键词] Fortune 60 CB Insights 50 100 startups"
```

常见权威榜单参考：

| 赛道举例 | 可能的权威榜单 |
|----------|---------------|
| 网络安全 | Fortune Cyber 60, CRN Emerging Cybersecurity Companies |
| AI 基础设施 | CB Insights AI 100, Forbes AI 50 |
| 金融科技 | CB Insights Fintech 100, Forbes Fintech 50 |
| 医疗健康 | Rock Health Digital Health Funding Report, CB Insights Digital Health 150 |
| 具身智能/机器人 | Fortune Future 50, Robotics Business Journal 50 |
| 通用初创 | Forbes America's Best Startup Employers, TIME100 Most Influential Companies |

找到榜单后，对榜单中的公司**批量并行筛查**（每批 3-5 家同时发起搜索），检查是否符合筛选条件（阶段、VC 背书、华人背景等）。

### 3.3 合并去重

将**多轮关键词搜索**和**榜单策略**找到的所有公司与 Websets 直接搜索到的结果**合并去重**，得到最终完整候选名单。

**如果搜索后没有找到相关权威榜单，跳过该策略，继续后续步骤。** 不要过度追求榜单策略而影响整体效率。

## Step 4: 补充信息搜索

对候选名单中的每家公司，使用 **Exa Search MCP** 工具针对以下信号关键词搜索，获取关键信息：

### 工具 1 — `web_search_exa`（创始人/技术/融资详情）

用于搜索创始人背景、技术首创性、融资详情、论文奖项等需要精准信息检索的场景：

- 创始人背景 + 前经历：`query="[公司名] founder [CEO名] background previous company education"`, `type="auto"`
- 技术/产品首创性：`query="[公司名] first pioneering breakthrough"`, `type="auto"`
- 融资详情：`query="[公司名] funding raised seed series A"`, `type="auto"`
- 论文/会议/奖项：`query="[公司名] NeurIPS ICML CVPR award"`, `type="auto"`
- 增长指标：`query="[公司名] ARR revenue growth 3x"`, `type="auto"`

### 工具 2 — `company_research_exa`（公司结构化信息 + 新闻）

用于快速批量获取公司基础信息（员工数、融资总额、总部等）和新闻：

- `companyName="[公司全名]", numResults=5`

### 工具 3 — `get_code_context_exa`（技术型公司深度信息）

用于技术栈、API 文档、开源项目等技术背景补充：

- `query="[公司名] API product architecture stack"`, `tokensNum=5000`

### 工具 4（可选） — `people_search_exa`（创始人深度背景）

用于创始人职业经历深挖（需启用高级工具）：

- `query="[创始人姓名] career experience employer"`, `numResults=5`

### 用户附加的其他要求

根据用户具体需求针对性选用以上工具组合查询。

### 并行策略

**补充信息搜索有两个维度的并行空间，必须并行执行以降低整体延迟：**

**维度 1 — 跨公司并行**：不同公司的搜索完全独立，可同时发起所有公司的搜索请求。例如有 8 家候选公司，一次性并行发起 8 轮搜索，而非逐家串行。

**维度 2 — 单家公司多维度并行**：同一家公司的多个搜索维度（创始人背景 + 融资详情 + 大厂合作 + …）互相独立，可同时发起。

并行矩阵示意（8 家公司 × 4 个搜索维度 = 最多 32 个并行请求）：
```
公司 A [创始人背景] [技术首创性] [大厂合作] [融资详情]  ← 同时发起
公司 B [创始人背景] [技术首创性] [大厂合作] [融资详情]  ← 同时发起
公司 C ...
...
```

> **注意事项**：
> - 如果候选公司数量较多（>10 家），按批次分组并行（每批 5-8 家），批次间串行，避免同时请求过多导致限流。
> - 高优先级公司（2+ 信号）的信息搜索优先级更高，可优先等待其结果。
> - 所有并行搜索完成后，汇总结果再继续下一步信号分析。

### 补充公司结构化数据

通过 `company_research_exa` 返回的结构化数据获取：

- 员工数、融资总额、总部位置、公司简介等字段直接从 `company_research_exa` 结果中提取
- 如有需要，可配合 `web_search_exa` 搜索获取更细粒度的财务数据、融资轮次、月访问量等

## Step 5: 触发信号识别

拿到完整数据后，**逐家公司逐条扫描**以下信号规则的五大类（首创性、业务、资金、团队、赛道）：

读取 `references/signal-rules.md` 获取完整的信号扫描规则和优先级定义。每家公司的最终优先级 = **所有匹配信号中的最高级别**。

## Step 6: 输出报告

**所有赛道挖掘任务的输出必须同时做两件事：**

1. **在对话中展示完整的分析报告**（方便用户即时查看）
2. **将报告写入一个 `.md` 文件**（方便用户保存、分享、转发）

### 文件输出规范

文件名格式：`company_mining_report_{赛道名}_{日期}.md`

赛道名用简短英文（小写下划线），日期为 `YYYY-MM-DD`。文件名过长时可简化。

### 报告模板与 CSV 导出

读取 `references/report-template.md` 获取完整的 Markdown 报告模板和 CSV 导出代码。

## Step 7: 信源与引用

**所有数据必须附带可追溯的信源**：

- 公司 URL + 创始人 LinkedIn URL 必须提供
- 创始人背景信息需标注来源
- 融资金额、轮次、投资方等硬数据标注来源 URL
- Exa 搜索结果自带 `grounding.citations` 即为信源
- **不确定或无法查证的标注 "Uncertain"，绝不编造**

## 关键注意事项

### 华人背景的不确定性

华人定义宽泛（华裔、大陆、港澳台、双重国籍都算）。遇到不确定情况标注 `"likely"` 或 `"uncertain"` 但依然保留，不因不确定就排除。

### 信息分层策略

- **Websets enrichment** → 只做基础字段（公司名/官网/创始人/背景/融资/总部/年份），保证高准确率
- **Exa search** → 针对每家公司精准补充信号数据（创始人前经历、论文、合作、增长指标等）
- **高优先级公司** → 信息不完整时单独用 `deep` search 做深度调研

### 灵活适配用户要求

用户可以在 Step 1 中附加任何筛选条件、地域偏好、排除项等。这些要求会被动态纳入搜索策略。如果用户的要求涉及非常规维度（如"只看有开源项目的公司"、"关注女性创始人"、"只看欧洲公司"），需要相应调整搜索关键词和筛选逻辑。
