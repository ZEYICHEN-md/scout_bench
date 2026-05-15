# Phase 0 赛道引导与拆分方法论

> 当用户输入的赛道过于宽泛时，使用本文件指导从宽泛主题到具体子赛道的拆分流程。

---

## 核心原则

不要凭知识库硬编选项，而是通过搜索从真实市场信号中**提取结构化线索，再聚类成选项**。

---

## 步骤 1：全景扫描（3 个搜索并行）

```bash
# 融资热度扫描 —— 看哪些细分方向在拿钱
tvly search "{宽泛主题} startup funding landscape 2026" --json --max-results 10 --depth basic --time-range year

# 技术趋势扫描 —— 看有哪些不同的技术路线
tvly search "{宽泛主题} emerging approaches different implementations" --json --max-results 10 --depth basic --time-range year

# 语义深度扫描（Exa）—— 找非热门的隐蔽方向
mcporter call 'exa-full.web_search_exa(query: "{宽泛主题} technical approaches architectures", numResults: 10, type: "auto")'
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

## 步骤 5：自动选择并分批次挖掘

agent 根据信号强度自动选择，**不中断用户确认**。

**自动分批次规则**：

- **Batch 1**：自动选择信号最强的 1-2 个子赛道优先挖掘
  - 判定标准（按优先级）：近期融资信号最密集、与用户 `investment_thesis` 最匹配、技术差异化最明确
- **Batch 2**：剩余所有子赛道继续挖掘，与 Batch 1 结果合并
- **最终**：所有子赛道的项目汇总去重，生成统一报告

**示例**（用户说"帮我看看 AI Agent 领域"）：

agent 扫描后会自动识别出 5 个方向，并按信号强度排序：

| 批次 | 子赛道 | 选择理由 |
|------|--------|----------|
| Batch 1 | Agent 执行环境 / Sandbox | 近半年 5+ 种子轮，a16z/Bessemer 均有布局，融资信号最强 |
| Batch 1 | Agent 编排与调度 / Orchestration | 企业需求快速增长，与用户"看好企业级 Agent 基础设施"的 thesis 最匹配 |
| Batch 2 | Agent 记忆与状态 / Memory | 融资热度上升，但信号密度低于前两者 |
| Batch 2 | Agent 安全与对齐 / Guardrails | 大企业刚需，但早期项目数量较少 |
| Batch 2 | Agent 工具集成 / Tooling | 生态扩展快，但项目同质化程度较高 |

agent 自动将 Sandbox 和 Orchestration 作为 Batch 1 优先挖掘，其余进入 Batch 2，整个过程无需用户介入。
