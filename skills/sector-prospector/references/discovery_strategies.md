# Phase 2 深度挖掘搜索策略

> 本文件规范 `sector-prospector` Phase 2 的多轮垂直搜索策略。核心目标：**在一个具体的赛道内，通过多轮递进式搜索，挖出搜索引擎首页之后的内容，找到尚未被 public hype 的早期项目。**

---

## 一、核心模型：锚点扩散（Anchor & Expand）

不是从"概念"出发做广泛搜索，而是**从"锚点"出发做定向扩散**。

### 锚点类型

| 锚点类型 | 强度 | 来源 | 扩散方式 |
|---------|------|------|----------|
| **Reference Company** | 强 | 用户提供（如"类似 Multica"） | 分析它的生态位，找替代方案、上下游、同 investors |
| **Phase 1 Key Concepts** | 中 | 赛道解构产出（如"code sandbox"） | 用具体技术词组合搜索，穿透到细分领域 |
| **Round 1 发现的项目** | 动态 | Phase 2 搜索中实时发现 | 反向搜索其竞争对手、创始人、investors |

### 扩散逻辑

```
Round 1: 锚点直接搜索
  → 找到 5-10 个直接相关公司

Round 2: 锚点反向扩散
  → 从 Round 1 的公司找 competitors / alternatives / 同 investors
  → 找到 5-10 个间接相关公司

Round 3: 维度补充搜索
  → 从人（创始人）、技术（开源）、场景（垂直应用）维度补充
  → 找到 3-5 个跨界/隐蔽项目

动态调整: 根据新发现持续生成新 query
```

**质量法则**：一个项目被发现的轮次越早、被独立 query 命中的次数越多，其信息可信度越高。

---

## 二、搜索轮次详解

### Round 1: 锚点直接搜索（Direct Anchor Search）

**目标**：从最强锚点出发，找到最直接的 5-10 个相关公司。

#### 情况 A：有 Reference Company（强锚点）

**核心 query 集**（必须全部执行）：

```
# 1. 直接替代品
"{reference_company} alternatives"
"{reference_company} competitors"
"companies like {reference_company}"

# 2. 同一生态位的不同技术路线
"{reference_company} vs"                    # 看搜索结果中常和谁对比
"open source alternative to {reference_company}"
"{reference_company} similar but different approach"

# 3. 上下游
"{reference_company} integration partners"
"{reference_company} ecosystem"
"tools that work with {reference_company}"

# 4. 投资者线索
"{reference_company} investors"
"{reference_company} backers VC"
```

**从搜索结果中提取**：
- 直接竞品名称
- 对比文章中提到的其他公司
- 投资者名单

**示例**（reference = "e2b"）：
- `"e2b competitors"` → 发现 Daytona, CodeSandbox, Gitpod 等
- `"e2b vs"` → 发现文章中对比的 Theia, DevContainers 等
- `"e2b investors"` → 发现 a16z, Sequoia 等 → 再搜 `"a16z sandbox startup"`

#### 情况 B：无 Reference Company，只有 Key Concepts（弱锚点）

**核心 query 集**（按优先级执行，前 5 个必须）：

```
# 1. 技术概念 + 创业信号（最可能找到早期项目）
"{key_concept} startup"
"{key_concept} early stage company"
"who is building {key_concept}"

# 2. 技术概念 + 融资信号（验证市场活跃度）
"{key_concept} seed funding"
"{key_concept} series A"
"{key_concept} raised funding"

# 3. 技术概念 + 开源信号（找到技术先行的团队）
"{key_concept} github open source"
"{key_concept} open source project"
```

**示例**（key_concept = "code sandbox"）：
- `"code sandbox startup"` → 发现 e2b, Daytona, CodeSandbox
- `"code sandbox seed funding"` → 发现近期融资的早期项目
- `"code sandbox github open source"` → 发现开源项目，再追踪其商业化

---

### Round 2: 锚点反向扩散（Reverse Expansion）

**目标**：从 Round 1 发现的 3-5 个代表性项目出发，反向挖掘其生态。

**触发条件**：Round 1 完成后，必须执行。这是发现"隐藏项目"的关键轮次。

#### 2A. 竞争扩散

从 Round 1 的每个代表性公司出发：

```
"{company_A} vs {company_B}"          # 找直接对比文章中提到的第三方
"alternatives to {company_A}"          # 找替代方案
"{company_A} competitors"              # 找竞争对手列表
"{company_A} similar startups"         # 找同类早期项目
```

**技巧**：对比文章（"A vs B"）往往会提到 C、D 等第三方，这些是高质量线索。

#### 2B. 投资者扩散

```
# 1. 查谁投了 Round 1 的公司
"{company_A} funding investors"

# 2. 同一投资者在该领域的其他 portfolio
"{investor_name} {sector_theme} startup"
"{investor_name} portfolio {key_concept}"

# 3. 如果投资者是知名 VC（a16z, Sequoia, Bessemer 等）
"{investor_name} latest investments {sector_theme}"
```

**为什么有效**：VC 通常会在同一赛道投 2-3 家公司。找到一家，就可能通过 investor 找到另外几家。

#### 2C. 创始人扩散

```
# 1. 查创始人背景
"{company_A} founders background"
"{company_A} CEO previous company"

# 2. 如果创始人来自大厂/名校
"ex-{founder_previous_company} {key_concept} startup"
"ex-{founder_previous_company} founded {sector_theme}"
"{university} {key_concept} startup"

# 3. 如果创始人是连续创业者
"{founder_name} new startup"
"{founder_name} founded company"
```

**为什么有效**：大厂背景创业者往往带着同一批同事或校友创业，形成"人才网络"。

#### 2D. 技术扩散

```
# 1. 同一技术栈的其他应用
"{company_A} technology stack" → 发现技术关键词
"{tech_keyword} startup {sector_theme}"

# 2. 同一开源生态
"{company_A} open source"
"{company_A} github"
→ 发现开源项目 → 搜 "{project_name} commercial"
```

---

### Round 3: 维度补充搜索（Dimension Supplement）

**目标**：从人、技术、场景三个维度，补充 Round 1/2 遗漏的隐蔽项目。

**触发条件**：Round 2 完成后，如果当前子赛道发现的项目 < 8 个，必须执行。

#### 3A. 人维度（创始人信号）

```
"ex-OpenAI {key_concept} startup"
"ex-Anthropic {key_concept} founded"
"ex-Google {sector_theme} startup"
"PhD {key_concept} company"
"{university} {key_concept} founder"
```

**big_tech 列表**（根据赛道动态选择）：
- AI Infra：OpenAI, Anthropic, Google DeepMind, Meta AI, Microsoft Research
- 具身智能：Tesla, Boston Dynamics, Figure AI, 1X, Google Robotics
- 中国背景：字节, 阿里, 腾讯, 百度, 华为, 大疆, 商汤

**university 列表**：
- 美国：MIT, Stanford, CMU, Berkeley, UW, UIUC
- 中国：清华, 北大, 复旦, 上交, 浙大, 中科大

#### 3B. 技术维度（开源/学术信号）

```
"{key_concept} github stars"
"{key_concept} arxiv paper"
"{key_concept} research prototype"
"{key_concept} academic spinoff"
"{key_concept} lab commercialization"
```

**追踪链路**：
1. 发现 GitHub repo → 记录作者/组织名
2. 搜索 `"{author_name} startup"` 或 `"{author_name} company"`
3. 发现 arXiv 论文 → 记录作者名
4. 搜索 `"{author_name} founded"` 或 `"{author_name} CEO"`

#### 3C. 场景维度（垂直应用）

```
"{key_concept} for finance startup"
"{key_concept} for healthcare company"
"{key_concept} enterprise security"
"{key_concept} developer tools"
```

**场景选择**：根据 Phase 1 对赛道的理解，选择 2-3 个最可能的应用场景。

---

## 三、动态 Query 调整机制

搜索不是静态执行模板，而是**根据实时结果动态调整**。

### 信号响应规则

| 实时信号 | 调整动作 |
|---------|---------|
| 某 query 连续返回 0 个有效结果 | 放宽关键词（如从 "WASM sandbox for healthcare" 放宽到 "WASM sandbox healthcare"） |
| 某 query 发现大量 public hype 公司 | 加限定词（如加 "seed" / "early stage" / "founded 2024"） |
| 发现某类公司频繁出现（如都是做 Container-based） | 增加 "VM-based" / "WASM-based" 等替代技术路线的搜索 |
| 发现某明星项目的 direct competitor | 立即围绕该 competitor 做 Round 2 扩散 |
| 发现某 VC 多次出现 | 深度搜索该 VC 在该领域的全部 portfolio |
| 某子赛道发现项目 < 5 个 | 尝试换关键词或换搜索维度（从"技术"换到"场景"） |
| 某子赛道发现项目 > 15 个 | 收紧过滤，优先深入挖掘高潜力项目的生态 |

### Query 生成原则

每生成一个新 query，必须自检：

- [ ] **是否包含至少一个 Phase 1 的 key_concept？**（确保不偏离赛道）
- [ ] **是否包含一个信号词？**（startup / founded / github / funding / competitors 等）
- [ ] **是否比上一轮更具体或角度更新？**（避免重复搜索同一批公司）
- [ ] **是否可能返回 public hype 公司？**（如是，加 early stage / seed 等限定）

---

## 四、信息可信度评分

从搜索结果中提取公司时，按以下标准评分：

| 可信度 | 标准 | 处理方式 |
|--------|------|----------|
| **高** | 在 2+ 个独立 query 中出现；或有融资信息；或有创始人信息；或有官网 | 直接纳入 prospects |
| **中** | 在 1 个 query 中出现，但有详细描述（如产品功能、技术特点） | 纳入 prospects，标注 "待验证" |
| **低** | 只在 1 个 query 中出现，且只有名字，无其他信息 | 记录但暂不纳入，后续尝试补充搜索验证 |

**独立 query 的定义**：两个 query 的核心关键词组合不同（如 "code sandbox startup" 和 "ex-OpenAI code execution" 是独立的；"code sandbox startup" 和 "code sandbox early stage" 不算独立）。

---

## 五、创始人姓名信号识别

在从搜索结果提取 `founders` 字段时，同步执行轻量的姓名拼音启发式判断，用于 Phase 3 的华人偏好加分。此步骤**不改变搜索 query**，仅在信息提取层运行。

### 识别规则

**拼音姓氏库（高频 50 个）**：
Li, Zhang, Wang, Liu, Chen, Yang, Huang, Zhao, Zhou, Wu, Xu, Sun, Ma, Zhu, Hu, Guo, Lin, He, Gao, Luo, Zheng, Liang, Xie, Song, Tang, Han, Feng, Deng, Cao, Peng, Zeng, Xiao, Tian, Dong, Pan, Yuan, Cai, Jiang, Yu, Du, Ye, Cheng, Su, Wei, Ding, Ren, Shen, Lu, Yao, Tan

**置信度分级**：

| 级别 | 判定标准 | 示例 |
|------|---------|------|
| **high** | 姓氏匹配拼音，且名字符合拼音结构（常见拼音名或无明显英文特征） | `"Wei Wang"`, `"Yifan Lu"`, `"Zihang Dai"` |
| **medium** | 仅姓氏匹配拼音，名字为典型英文名或无法判断 | `"David Chen"`, `"Alex Li"`, `"Michael Zhang"` |
| **none** | 姓氏不匹配拼音库 | `"John Doe"`, `"Jane Smith"` |

**注意事项**：
- 此识别为**初筛标记**，不替代 `weekly-recommendation` 的华人创始人确认流程
- 存在 false positive（如韩裔、越南裔也可能使用拼音姓氏），作为加分项的权重设计已考虑此误差
- 多创始人时，只要其中一人的信号为 `high` 或 `medium`，即按最高级别标记整个项目
- 结果写入 `raw_prospects.json` 的 `founder_name_signal` 和 `founder_name_signal_basis` 字段

---

## 六、搜索深度与取舍

**不是所有轮次都必须执行到满**。agent 应根据以下信号动态取舍：

| 信号 | 行动 |
|------|------|
| Round 1 已发现 10+ 个高可信度项目 | 重点做 Round 2（反向扩散），Round 3 可选 |
| Round 1 只发现 3-5 个项目 | 必须做 Round 2 + Round 3 |
| Round 2 发现大量 competitors | 对最有代表性的 2-3 个做深度扩散 |
| 某子赛道技术属性强 | 优先 Round 3B（开源/学术） |
| 某子赛道应用属性强 | 优先 Round 3C（垂直场景） |
| 有 reference_company | Round 1 优先执行 2A 和 2B（投资者扩散） |

---

## 六、每轮搜索的覆盖目标

**理想情况下**，每个子赛道应通过多轮搜索覆盖到以下信息源：

1. **科技媒体**（TechCrunch, The Information, VentureBeat）—— 融资新闻
2. **垂直社区**（Hacker News, Reddit, Discord）—— 早期口碑
3. **开源平台**（GitHub, Hugging Face）—— 技术线索
4. **学术渠道**（arXiv, Google Scholar, 实验室主页）—— 成果转化
5. **LinkedIn/Twitter** —— 人脉变动（通过搜索间接捕获）
6. **行业报告**（a16z, Sequoia, Bessemer 博客）—— 生态位分析

agent 不需要专门访问这些平台，而是通过 Tavily/Exa 的搜索覆盖到它们的内容。
