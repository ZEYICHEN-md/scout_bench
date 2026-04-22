# Phase 0 赛道引导与拆分方法论

> 当用户输入的赛道过于宽泛时，使用本文件指导从宽泛主题到具体子赛道的拆分流程。

---

## 核心原则

不要凭知识库硬编选项，而是通过搜索从真实市场信号中**提取结构化线索，再聚类成选项**。

---

## 步骤 1：全景扫描（3 个搜索并行）

```bash
# 融资热度扫描 —— 看哪些细分方向在拿钱
tvly search "{宽泛主题} startup funding landscape 2026" --json --max-results 10 --depth basic

# 技术趋势扫描 —— 看有哪些不同的技术路线
tvly search "{宽泛主题} emerging approaches different implementations" --json --max-results 10 --depth basic

# 语义深度扫描（Exa）—— 找非热门的隐蔽方向
mcporter call 'exa.web_search_exa(query: "{宽泛主题} technical approaches architectures", numResults: 10)'
```

---

## 步骤 2：从搜索结果中提取结构化线索

从搜索结果中系统性地提取以下**五个维度**的线索：

| 提取维度 | 在搜索结果中找什么 | 例子（"AI Agent"） |
|---------|------------------|------------------|
| **技术路线差异** | 不同实现方式的关键词对比 | Sandbox vs Orchestration vs Memory vs Tooling |
| **明星锚点项目** | 被多次提及的具体公司/产品 | e2b（代码沙箱）、CrewAI（编排）、Mem0（记忆） |
| **场景切口** | "for XX" / "in YY" 的垂直应用搭配 | agent for coding / agent for customer service |
| **融资热点** | 近期集中融资的子方向 | "近3个月5个 sandbox 项目获 seed" |
| **大厂/开源动作** | 大公司产品或高星开源项目 | OpenAI computer use、Anthropic MCP、LangChain |

**提取技巧**：
- 如果一篇文章同时提到 A、B、C 三家公司 → 它们可能是同一细分方向的竞品
- 如果某个技术词（如 "microVM"）在多篇文章中出现 → 这是一个值得关注的技术路线
- 如果某个公司名频繁出现 → 这是该方向的锚点公司

---

## 步骤 3：聚类形成子赛道选项

把提取到的线索按**技术路线**或**应用场景**聚类，每个聚类就是一个具体子赛道选项。

**聚类规则**：
- 同一个聚类内的项目应该用**同一个技术名词**或**同一个场景词**描述
- 聚类之间应该是**互斥的**（如 Sandbox 和 Orchestration 是不同的事）
- 聚类名称必须具体到**技术/产品粒度**（如"Agent Sandbox"而非"Agent Infra"）

---

## 步骤 4：每个选项附带锚点证据

不是空口说白话，每个选项必须给出**从搜索结果中提取的证据**：

| 要素 | 说明 | 例子 |
|------|------|------|
| **代表锚点** | 1-2 个被搜索到的具体公司 | e2b, Daytona |
| **技术关键词** | 3-5 个该方向的核心技术词 | code execution, microVM, Firecracker, sandbox |
| **近期信号** | 从搜索结果中读到的融资/趋势信号 | 近半年 5+ 种子轮，a16z/Bessemer 布局 |
| **一句话描述** | 这个方向在解决什么问题 | 让LLM Agent安全执行代码和浏览器操作 |

---

## 步骤 5：呈现选项，让用户选 1-2 个

**示例**（用户说"帮我看看 AI Agent 领域"）：

```
"AI Agent" 范围很大，我快速扫描了当前市场的融资和创业信号，
建议从以下具体方向中选 1-2 个深入挖掘：

  1. Agent 执行环境 / Sandbox
     -> 让LLM安全运行代码/浏览器/文件操作（如 e2b, Daytona）
     -> 信号：近半年 5+ 种子轮，a16z/Bessemer 均有布局

  2. Agent 编排与调度 / Orchestration
     -> 多Agent协作、工作流编排（如 LangGraph, CrewAI）
     -> 信号：企业需求快速增长，开源社区活跃

  3. Agent 记忆与状态 / Memory
     -> 上下文持久化、长期记忆、知识图谱（如 Mem0）
     -> 信号：从"玩具"转向企业级，2026年融资热度上升

  4. Agent 安全与对齐 / Guardrails
     -> 输出校验、行为护栏、策略控制（如 Guardrails AI）
     -> 信号：大企业采购刚需，合规驱动

  5. Agent 工具集成 / Tooling
     -> MCP协议、Function Calling中间件、工具市场
     -> 信号：Anthropic推MCP后生态快速扩展

你可以：
- 回复数字选 1-2 个（如"1 和 3"）
- 或者直接给我一个更具体的赛道词（如"agent 代码沙箱"）
```

**用户选择后**：将用户选的方向作为新的 `sector_theme`，进入 Phase 1（赛道解构）。未被选的方向丢弃，不保留在上下文中。
