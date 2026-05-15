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

**融资信号优先法则**：Round 1 的融资信号 query（`founded 2024 2025`、`seed funding`）是发现早期项目最高效的路径，必须优先执行并充分挖掘。扩散机制（Round 2/3）是对融资信号发现的"基础盘"做补充，而非替代。

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

**核心 query 集**（按优先级执行，前 6 个必须）：

```
# 1. 融资信号 query（发现早期项目效率最高，必须执行）
"{key_concept} startup founded 2024 2025 2026"
"{key_concept} seed funding pre-seed"
"{key_concept} stealth mode early stage"

# 2. 创始人信号 query（高价值人才网络）
"ex-Google ex-OpenAI {key_concept} startup founded"
"PhD {key_concept} company founded 2024 2025"

# 3. 技术概念 + 开源信号（找到技术先行的团队）
"{key_concept} github open source"
"{key_concept} open source project"
"who is building {key_concept}"
```

**示例**（key_concept = "code sandbox"）：
- `"code sandbox startup founded 2024 2025 2026"` → 直接命中近期成立的早期项目
- `"code sandbox seed funding pre-seed"` → 发现刚拿钱的 stealth 项目
- `"code sandbox github open source"` → 发现开源项目，再追踪其商业化

**为什么融资信号 query 放在 Round 1**：
- 融资信号 query（`seed funding`、`founded 2024 2025`）直接命中融资新闻，是发现早期项目最高效的路径
- 融资新闻天然覆盖所有阶段的公司，不受知名度偏差影响
- 作为 Round 1 的"基础盘"，确保每个子赛道至少有 3-5 个高可信度早期项目

---

### Round 2: 锚点反向扩散（Reverse Expansion）

**目标**：从 Round 1 的产出出发做反向扩散。包括从发现的项目扩散（竞品、投资者、创始人、技术栈），以及从已知技术关键词扩散（技术变体、替代路线、技术栈交叉）。

**触发条件**：Round 1 完成后，必须执行。这是发现"隐藏项目"的关键轮次。

#### 2A. 生态扩散

**生态扩散 query 集**（按优先级执行）：

```
# 1. 上下游和生态伙伴（最容易发现新公司）
"{company_A} integration partners"
"{company_A} ecosystem tools"
"tools that work with {company_A}"

# 2. 替代技术路线（保留 alternatives，但目的是找不同技术路线的新玩家）
"{company_A} vs"                       # 看对比文章中提到的不同技术路线
"open source alternative to {company_A}"
"{company_A} similar but different approach"

# 3. 辅助性 competitor 搜索（执行 1-2 个即可，不深入）
"{company_A} competitors"
"{company_A} similar startups"

# 4. 从使用场景扩散
"{company_A} use cases"
"who uses {company_A}"
```

**技巧**：对比文章（"A vs B"）中提到的第三方，如果是**不同技术路线**的公司，往往比"直接竞品"更有早期信号。

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

#### 2E. 技术语义扩展

**目标**：从已知技术关键词出发（包括 Phase 1 的 `key_concepts` 和 Round 1/2 中新发现的技术词），发现同领域的技术变体、替代方案或底层技术栈，用这些**新技术词作为新锚点**去搜 startup。

**触发条件**：每完成一个子赛道的 Round 1 后执行；或在 Round 2 其他扩散路径中遇到新的技术关键词时触发。

**技术词发现 query 集**：

```
# 1. 技术对比与变体发现（从已知技术词找替代/关联技术）
"{tech_keyword} vs"                              → 发现对比文章中提到的替代技术
"{tech_keyword} alternative technology"
"{tech_keyword} comparison different approaches"
"{tech_keyword} vs traditional approach"

# 2. 技术栈组合发现（从技术实现细节挖关键词）
"{tech_keyword} stack architecture"
"{tech_keyword} underlying technology"
"how does {tech_keyword} work internally"
"{tech_keyword} implementation details"
```

**从上述搜索结果中提取新技术词**，然后执行：

```
# 3. 用新技术词搜 startup
"{new_tech_keyword} startup"
"{new_tech_keyword} company founded"
"{new_tech_keyword} commercial"
"{new_tech_keyword} seed funding"

# 4. 技术路线交叉（两个技术词的交叉点往往是最隐蔽的创业方向）
"{tech_keyword_A} and {tech_keyword_B} startup"
"{new_tech_keyword} {sector_theme} company"
```

**示例**（以 "WASM sandbox" 为起点）：
- `"WASM sandbox vs"` → 发现对比文章中提到 **gVisor**, **seccomp-bpf**, **Firecracker microVM**
- `"gVisor startup"` → 发现用 gVisor 做安全隔离的早期项目
- `"Firecracker microVM company founded"` → 发现基于 Firecracker 的 Serverless 沙箱初创公司
- `"WASM sandbox underlying technology"` → 发现 **capabilities-based security**, **software fault isolation** 等概念
- `"capabilities-based security startup"` → 命中一个完全不同的技术路线的早期项目

**为什么有效**：
- 技术对比文章和架构指南天然会提到**替代技术路线**，这些往往是差异化创业的切入点
- 底层技术栈关键词（如 seccomp-bpf, gVisor）在主流媒体中曝光度低，但精准度高
- 技术路线交叉点（如 "WASM + confidential computing"）的竞争密度最低

---

#### 2F. 应用场景语义扩展

**目标**：从已知应用场景出发，发现同领域的细分场景、上下游场景或关联场景，用**新场景 + 技术关键词**作为新锚点去搜 startup。

**触发条件**：每完成一个子赛道的 Round 1 后执行；或在 Round 2 其他扩散路径中遇到新的应用场景时触发。

**场景词发现 query 集**：

```
# 1. 场景细分与关联发现（从已知场景挖更细的切口）
"{application_scene} use cases"                    → 发现该场景下的细分 workflow
"{application_scene} workflow steps"
"{application_scene} sub-applications"
"{application_scene} vs"                           → 看不同场景间的对比和替代关系

# 2. 场景上下游（发现相邻场景的新公司）
"before {application_scene} after {application_scene} tools"
"{application_scene} upstream downstream"
"{application_scene} ecosystem"
```

**从上述搜索结果中提取新场景词**，然后执行：

```
# 3. 用新场景 + 技术词搜 startup
"{new_scene} {key_concept} startup"
"{new_scene} {key_concept} company founded"
"{new_scene} {key_concept} seed funding"

# 4. 场景交叉（两个场景的交叉点往往是竞争盲区）
"{scene_A} and {scene_B} {key_concept} startup"
"{new_scene} automation startup"
```

**示例**（以 "healthcare" + "AI agent" 为起点）：
- `"healthcare AI agent use cases"` → 发现 **clinical documentation**, **prior authorization**, **medical triage**
- `"prior authorization AI startup"` → 发现只做保险预授权这个细分场景的早期项目
- `"before clinical documentation after clinical documentation tools"` → 发现 **medical scribing**, **EHR integration** 等相邻场景
- `"medical triage vs prior authorization"` → 对比文章中可能提到 **patient intake**, **referral management** 等新场景
- `"patient intake AI agent startup"` → 命中又一个差异化切入点

**为什么有效**：
- 垂直场景的细分程度比技术词更深，大厂通常只做顶层场景（"healthcare AI"），细分场景（"prior authorization automation"）留给早期团队
- 场景上下游和 workflow steps 能发现"同一链条上的不同创业机会"
- 场景对比文章会提到很多你原本想不到的细分切口

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
| 发现某明星项目的生态伙伴/投资者 | 立即围绕该投资者做 portfolio 扩散，围绕其技术栈做替代路线搜索 |
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
| Round 1 融资信号 query 已发现 8+ 个高可信度项目 | 重点做 Round 2（投资者/创始人扩散），Round 3 可选 |
| Round 1 只发现 3-5 个项目 | 必须做 Round 2 + Round 3 |
| Round 2 生态扩散返回大量已知平台 | 停止生态扩散，转向投资者/创始人/技术语义扩展 |
| Round 2 技术语义扩展发现大量新技术词 | 优先深挖这些新技术词的 startup 结果，暂停生态扩散 |
| 某子赛道技术属性强 | 优先 Round 2E（技术语义扩展）和 Round 3B（开源/学术） |
| 某子赛道应用属性强 | 优先 Round 3C（垂直场景） |
| 有 reference_company | Round 1 优先执行投资者扩散 + 生态扩散 |

---

## 七、每轮搜索的覆盖目标

**理想情况下**，每个子赛道应通过多轮搜索覆盖到以下信息源：

1. **科技媒体**（TechCrunch, The Information, VentureBeat）—— 融资新闻
2. **垂直社区**（Hacker News, Reddit, Discord）—— 早期口碑
3. **开源平台**（GitHub, Hugging Face）—— 技术线索
4. **学术渠道**（arXiv, Google Scholar, 实验室主页）—— 成果转化
5. **LinkedIn/Twitter** —— 人脉变动（通过搜索间接捕获）
6. **行业报告**（a16z, Sequoia, Bessemer 博客）—— 生态位分析

agent 不需要专门访问这些平台，而是通过 Tavily/Exa 的搜索覆盖到它们的内容。
