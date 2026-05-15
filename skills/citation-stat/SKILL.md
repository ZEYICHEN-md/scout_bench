---
name: citation-stat
description: |
  统计学者 Google Scholar 引用量数据，生成论文分类表格和多人对比表格。当用户需要查询学者引用量、统计论文引用、获取 Google Scholar 数据、做学术引用量对比、生成学者论文分类表时触发。触发词包括："查引用量"、"统计引用"、"Google Scholar 数据"、"学者引用对比"、"论文分类表格"、"引用量统计"、" citation stats"、"学者 h-index"。即使没有明确说"统计"，只要用户提到多个学者并涉及引用数据，也应触发。
dependencies:
  - skill: agent-browser
    install: npx skills add https://github.com/vercel-labs/agent-browser --skill agent-browser
---

# 学者引用量统计 Skill

**依赖要求**：使用本 Skill 前必须先安装 agent-browser
```bash
npx skills add https://github.com/vercel-labs/agent-browser --skill agent-browser
```

## 数据采集方式

### 强制要求：浏览器自动化工具爬取 + WebSearch 仅用于定位

**数据爬取必须使用浏览器自动化工具（如 agent-browser）实时进行。WebSearch / WebFetch 只能用于「发现正确的 Google Scholar Profile URL」这一步，找到 URL 后必须立即用 agent-browser 访问并采集数据。**

支持的浏览器自动化工具：
- **agent-browser**（推荐）: `npx skills add https://github.com/vercel-labs/agent-browser --skill agent-browser`

### Google Scholar 数据采集

**第一步：定位 Profile URL（可用 WebSearch）**
```
1. 用 WebSearch 查询："[姓名] Google Scholar" 或 "[姓名] site:scholar.google.com/citations"
2. 从搜索结果中提取第一个 scholar.google.com/citations?user=... 链接
3. 如名字常见导致歧义，添加机构/代表作关键词重新搜索（如 "+Alibaba"、"+Qwen"）
```

**第二步：爬取数据（必须用 agent-browser）**
```
1. 用 agent-browser 打开第一步找到的 Profile URL
2. 获取：总引用量（All time）、h-index（All time）、论文总数（Scholar 上显示的总发表数）
3. 获取按引用排序的论文列表（点击 SORT BY CITATIONS）
4. ⚠️ Google Scholar 默认只显示约 20 篇论文，必须反复点击 "SHOW MORE" 直到页面不再加载新论文
5. 记录每篇论文的：标题、作者列表、作者位置（一作/二作/其他）、会议/期刊、年份、引用数
6. ⚠️ 爬取完成后必须核对：已记录的论文数量是否等于 Scholar 显示的论文总数？如果少了，说明 SHOW MORE 没点够，必须回去继续点击
7. ⚠️ 特别检查：引用量最高的 5 篇论文是否都已记录？如果缺失了超高引论文，说明爬取不完整
8. 记录总引用量、h-index、论文总数，供后续输出使用
9. ⚠️ 严禁用 WebSearch/WebFetch 直接获取引用量或论文列表（数据会过时）
```

## 数据处理流程

论文分类表格**只包含两类论文**：（1）一二作 + 顶刊顶会的论文；（2）引用量 Top 5 的论文（无论作者位置、无论是否顶会）。非顶会的一二作论文不进入表格。因此不需要处理全部 200 篇论文，只需维护约 20-40 篇关键论文的 JSONL，CoT 压力极小。

**为什么用 JSON Lines（`.jsonl`）？**
- 轻量、可读，人类可直接修改，Python 一行 `json.loads` 即可解析
- 与 markdown 表格职责分离：JSON 负责存储判定数据，markdown 负责展示

### Step 1: 爬取 + 粗筛（只保留关键论文）

用 agent-browser 打开 Scholar Profile，按引用量排序，反复点击 "SHOW MORE" 直到无法继续加载。

**只记录以下论文**到 `{name}_papers_raw.jsonl`，其他论文直接丢弃：
1. **作者列表前 10 位内包含目标学者**的论文（这些可能是一二作）
2. **引用量排名前 10** 的论文（确保 Top 5 池子足够大）

> 被截断在 `...` 后面且引用量不在前 10 的论文 → 直接丢弃（不可能是一二作，也不可能进 Top 5）

每条记录：`{"title": "...", "authors": ["..."], "venue": "...", "year": 2024, "citations": 123}`

这样 raw JSONL 通常不超过 30 篇。

### Step 2: 打标 + 精筛（只保留会进表格的论文）

对 `{name}_papers_raw.jsonl` 逐篇判定，**只保留以下两类论文**写入 `{name}_papers_classified.jsonl`：

**A 类：一二作 + 顶刊顶会**（`target_author_position` 为 `"first"` 或 `"second"` 且 `is_top_venue: true`）
**B 类：全局引用量 Top 5**（无论作者位置、无论是否顶会）

其他论文（如一作非顶会、二作非顶会、非 Top 5 的其他）**全部丢弃**，不进入 JSONL。

**⚠️ Venue 判定**

按 `references/top_venues.md` 的 Normalization Rules 和 aliases 判定。Google Scholar 上的 venue 字段常被截断，标准化后的子串匹配通常能正确识别。若 venue 被严重截断导致规则无法匹配，以论文标题搜索确认。

```json
{
  "title": "HotpotQA: A dataset for diverse, explainable multi-hop question answering",
  "authors": ["Zhilin Yang", "Peng Qi", "Saizheng Zhang", "..."],
  "target_author_position": "first",
  "target_author_index": 0,
  "venue": "EMNLP",
  "year": 2018,
  "citations": 4997,
  "is_top_venue": true,
  "domain": "自然语言处理",
  "label": "问答数据集",
  "paper_class": "A",
  "include_in_table": true
}
```

字段说明：
- `authors`：**完整作者列表**（保留 Google Scholar 上的 `*` 标注）
- `target_author_index`：目标学者在 `authors` 中的 0-based 索引
- `target_author_position`：根据索引严格判定 — `"first"` / `"second"` / `"other"`
- `is_top_venue`：对照 `references/top_venues.md` 判定
- `paper_class`：论文类别 — `"A"`（一二作顶会）或 `"B"`（全局 Top 5）。生成表格时必须按此字段排序
- `include_in_table`：**仅当该论文属于 A 类或 B 类时才为 `true`**

**打标完成后必须执行交叉验证**：
1. 检查 `authors` 中目标学者名字带 `*` 的，其 `target_author_position` 必须是 `"first"`
2. 检查全局引用量 Top 5 是否全部在 JSONL 中
3. 运行 `python validate_papers.py {name}_papers_classified.jsonl`，有错误立即修正

### Step 3: 基于精筛后的 JSONL 生成输出

- 读取 `{name}_papers_classified.jsonl`（通常 20-40 篇）
- 计算引用量统计：**仅对 A 类论文（一二作 + 顶会）求和**，B 类（Top 5）不计入
- 生成分类表格：展示 JSONL 中全部论文（A 类 + B 类），按领域分组
- 组内排序：**先按 `paper_class`（`"A"` < `"B"`），再按 `citations` 降序**
- 引用量统计摘要中的一作/二作顶刊顶会引用量，必须等于 A 类论文的求和

---

### 作者位置判定规则（严格）

必须根据 Google Scholar 上显示的作者列表顺序严格判定，并记录到 JSON 字段：

**基础规则（无共同一作标注时）**：
- **一作**：作者列表中第一位，即 `target_author_index == 0`
- **二作**：作者列表中第二位，即 `target_author_index == 1`
- **其他**：第三位及以后，即 `target_author_index >= 2`

**共同一作规则（有 `*` 或 equal contribution 标注时）**：
- 如果目标学者被明确标注为共同一作（作者名旁有 `*` 或列表中有 equal contribution 说明），则无论其在列表中的索引是多少，`target_author_position` 都记为 `"first"`
- 举例：作者列表显示 `[Peng Wang*, An Yang*, Junyang Lin, ...]`，则 Wang 和 Yang 都是 `"first"`，Junyang Lin 是 `"other"`
- **注意**：共同一作存在时，列表中未被标为共同一作的作者不因此获得"二作"身份。二作严格定义为`index==1`且**不是**共同一作的作者

**硬性要求**：
1. 必须将完整作者列表写入 `{name}_papers_classified.jsonl` 的 `authors` 字段（保留 Scholar 上的原始顺序和 `*` 标注）
2. 必须将目标学者的索引写入 `target_author_index` 字段
3. `target_author_position` 必须根据上述规则严格推导，**禁止根据论文内容、知名度或"核心作者"等概念人为调整**
4. **No exceptions based on paper importance or perceived contribution**

### 顶刊顶会判定规则

**判定方式**：按 `references/top_venues.md` 的 Normalization Rules 和 aliases 判定；venue 被严重截断导致规则无法匹配时，以论文标题搜索确认。

核心规则摘要：
- 一作/二作顶刊顶会引用量 = 一作顶刊顶会论文引用量 + 二作顶刊顶会论文引用量
- 共同一作按一作计入
- arXiv 论文处理：低引（<100）直接过滤；高引需确认是否被顶刊顶会接收
- 同一论文去重：优先使用正式 venue 版本

### 论文领域分类

根据论文标题和内容，将论文归类到以下领域之一（可扩展）：
- 自然语言处理
- 多模态学习
- 计算机视觉
- 机器学习
- 机器人学
- 数据挖掘
- 人工智能（通用）
- 其他

每篇论文应标注一个**标签**（2-4字精简描述，如"摘要生成"、"多标签分类"、"多模态预训练"）。

---

## 输出格式（⚠️ 只输出数据表格，禁止输出分析性文字）

**本 skill 只输出纯数据表格和统计数字，严禁输出以下内容：**
- 研究轨迹时间线
- 论文详细介绍（含金量、解决的问题、方法、突破、局限）
- 核心贡献总结
- 工业应用分析
- 团队角色定位
- 任何评价性、分析性、解释性的段落文字

允许的最简文字：领域名称、标签名称、数据口径说明、研究方向一句话概括。

### 输出0：研究方向一句话概括（每人一份，默认输出）

> ⚠️ **仅限一句话**，基于论文分类表格中的 A-class 论文分布客观概括，**严禁扩展为段落**。

**规则**：
- 只能陈述事实，禁止出现评价性词汇（如"开创性"、"领先"、"突破"、"奠基性"等）
- 禁止预测未来趋势、分析工业应用、总结核心贡献
- 格式：`主要研究方向为[领域1]、[领域2]，代表性工作集中在[细分标签1]、[细分标签2]。`
- 如 A-class 论文分布不明显，可简化为：`研究方向涵盖[领域1]、[领域2]等。`

**示例**：
- 杨植麟 → "主要研究方向为自然语言处理与机器学习，代表性工作集中在预训练语言模型、半监督学习与问答系统。"
- 吴俣 → "主要研究方向为自然语言处理，代表性工作集中在语音预训练与命名实体识别。"

**位置**：放在「引用量统计摘要」之后、「论文分类表格」之前。

---

### 输出1：引用量统计摘要（每人一份）

```markdown
## [姓名] 引用量统计

| 指标 | 数值 |
|------|------|
| 总引用量 | [数值] |
| h-index | [数值] |
| 一作/二作顶刊顶会引用量 | [数值] |

**一作顶刊顶会**：
- [论文1] ([引用量]) + [论文2] ([引用量]) + ... = **[合计]**

**二作顶刊顶会**：
- [论文1] ([引用量]) + [论文2] ([引用量]) + ... = **[合计]**

> ⚠️ **一作/二作顶刊顶会引用量必须等于上面两个合计之和**。上面的摘要数字是由下面的详细列表求和得出的，不是独立计算。如果两者不一致，以详细列表的求和为准，并修正摘要中的数字。

数据口径说明：通过 agent-browser 于 [日期] 从 Google Scholar 实时爬取。
```

### 输出2：论文分类表格（每人一份）

> **⚠️ 论文分类表格只包含两类论文**：（1）该学者为一作或二作**且**发表在顶刊顶会的论文；（2）该学者全部论文中**引用量 Top 5** 的论文（无论作者位置、无论是否顶会）。非顶会的一二作论文、非 Top 5 的其他论文均不进入表格。
>
> **⚠️ 绝对禁止拆分成多个子表**：必须输出**一张合并的总表**。不同研究领域使用**合并单元格行**分隔，格式为 `| **[领域名称]** |||||`。禁止用 `### [领域名]` 标题 + 独立子表的方式输出。
>
> **错误示例（禁止）**：
> ```markdown
> ### 自然语言处理
> | 标签 | 论文 | ... |
> |------|------|-----|
> | ...  |
>
> ### 多模态学习
> | 标签 | 论文 | ... |
> |------|------|-----|
> | ...  |
> ```
>
> **正确示例**：
> ```markdown
> | 标签 | 论文（年份/出处） | 作者角色 | 是否顶会/顶刊 | 引用量 |
> |------|-------------------|----------|---------------|--------|
> | **自然语言处理** |||||
> | 预训练 | XLNet...（2019，NeurIPS） | 一作 | 是（NeurIPS） | 16305 |
> | 问答系统 | HotpotQA...（2018，EMNLP） | 一作 | 是（EMNLP） | 4997 |
> | **大语言模型** |||||
> | 技术报告 | GLM...（2022，ACL） | 其他 | 是（ACL） | 2290 |
> ```

表格格式：

```markdown
| 标签 | 论文（年份/出处） | 作者角色 | 是否顶会/顶刊 | 引用量 |
|------|-------------------|----------|---------------|--------|
| **[领域名称①]** |||||
| [标签] | [论文标题]（[年份]，[会议/期刊]） | 一作/二作/其他 | 是（[顶会名]）/ 否 | [引用量] |
| [标签] | [论文标题]（[年份]，[会议/期刊]） | 一作/二作/其他 | 是（[顶会名]）/ 否 | [引用量] |
| **[领域名称②]** |||||
| [标签] | [论文标题]（[年份]，[会议/期刊]） | 一作/二作/其他 | 是（[顶会名]）/ 否 | [引用量] |
| ... | ... | ... | ... | ... |
```

**排序规则**：
1. 按领域分组
2. 组内排序键：`(paper_class, -citations)`，即先按 `paper_class`（`"A"` < `"B"`），再按引用量降序

> A 类 = `target_author_position` 为 `"first"` 或 `"second"` 且 `is_top_venue: true`
> B 类 = 全局引用量 Top 5 的论文（无论作者位置）

### 输出3：多人对比表格（当输入≥2人时）

```markdown
## 学者引用量对比

| 姓名 | 出生年份 | 总引用量 | h-index | 一/二作顶刊顶会引用量 | 当前身份 |
|------|----------|----------|---------|---------------------|----------|
| [姓名1] | [年份] | [数值] | [数值] | [数值] | [身份] |
| [姓名2] | [年份] | [数值] | [数值] | [数值] | [身份] |
| ... | ... | ... | ... | ... | ... |
```

> 注：出生年份和当前身份如用户未提供或在 Scholar 上无法确认，可留空或标注"未确认"。

---

## 关键检查清单

### 数据检查
- [ ] WebSearch 仅用于定位 Google Scholar Profile URL，找到后立即用 agent-browser 爬取
- [ ] 反复点击 "SHOW MORE" 直到无法继续加载
- [ ] 爬取时只记录两类论文到 raw JSONL：（1）作者列表前 10 位包含目标学者的；（2）引用量排名前 10 的。其他论文直接丢弃
- [ ] `{name}_papers_classified.jsonl` 只包含两类论文：A. 一二作 + 顶刊顶会；B. 全局引用量 Top 5。其他论文已丢弃
- [ ] `target_author_position` 已根据 `target_author_index` 严格判定：index==0→一作，index==1→二作，index>=2→其他。`authors` 中带 `*` 的必须设为 `"first"`
- [ ] 区分顶会顶刊/非顶会顶刊（按 `references/top_venues.md` 的 Normalization Rules 和 aliases 判定；venue 被严重截断导致规则无法匹配时，以论文标题搜索确认）
- [ ] 引用量统计摘要 = 一作顶刊顶会合计 + 二作顶刊顶会合计（仅 A 类论文，必须严格相等）
- [ ] 引用量统计数字是从 `{name}_papers_classified.jsonl` 的 A 类论文计算得出，不是独立估算
- [ ] 引用量 Top 5 的论文无缺失（已在 raw JSONL 中核对）
- [ ] 高引 arXiv 论文已核验 venue
- [ ] 论文分类表格**只包含** A 类（一二作顶会）+ B 类（Top 5）论文，非顶会一二作、非 Top 5 的其他论文均不进入表格
- [ ] 论文按领域分组，组内按 `(paper_class, -citations)` 排序

### 格式检查
- [ ] **论文表格必须是一张合并的总表**：不同研究领域用合并单元格行（`| **[领域名]** |||||`）分隔，绝对禁止拆分成多个独立子表，绝对禁止用 `### [领域名]` 标题分隔
- [ ] 每人均有一句「研究方向一句话概括」，放在引用量统计之后、论文分类表格之前
- [ ] 「研究方向一句话概括」**仅限一句话**，无评价性词汇（"开创性"、"领先"、"突破"等），无趋势预测，无工业应用分析
- [ ] 多人输入时必须有"学者引用量对比"总表
- [ ] **禁止输出任何分析性文字**：无研究轨迹、无论文详细介绍、无核心贡献总结、无评价性段落
- [ ] 日期使用当前日期

---

*数据生成时间：[日期]*
*数据来源：Google Scholar（通过 agent-browser 实时爬取）*
