# Phase 3 报告生成规范

> 本文件规范 `sector-prospector` Phase 3 的聚合、筛选、评分和报告生成流程。

---

## 1. 全局去重

读取 `raw_prospects.json`，按 `company_name` 全局去重（不区分大小写）。

若同一公司出现在多个子赛道，合并 `sub_sector` 为逗号分隔列表。

---

## 2. Public Hype 过滤

依据 `references/public_hype_filter.md` 的规则排除过度曝光项目。

对不确定的公司，执行快速验证搜索：

```bash
tvly search "{company_name} valuation funding IPO" --json --max-results 3 --depth basic --time-range year
```

---

## 3. 公司信息确认搜索（进入报告前的必修环节）

对每个保留的公司，执行一次**定向确认搜索**：

```bash
tvly search "{company_name} funding founders overview" --json --max-results 5 --depth basic --time-range year
```

**目的**：
- 验证并修正融资信息（解决搜索结果过时的问题）
- 补充创始人背景（姓名、前公司、学历）
- 获取更完整的公司介绍（产品形态、核心能力、差异化）

**确认搜索的排除哲学**（核心规则）：
- **搜不到更多信息 ≠ 排除**：早期项目网上信息少是正常的，不得因为 confirmation 搜不到而降级或排除
- **只有明确证伪才排除**：
  - 证实为上市公司 / 估值 ≥$1B / 已倒闭 / 赛道完全不对
  - 这类项目进 `excluded_prospects`，记录排除原因
- **验证通过 = 升级**：确认融资/创始人/官网后，`confidence` 提升，`confirmed_fields` 标注
- **搜不到 = 保持原样**：维持原 `confidence` 和原始信息，不额外标注"待确认"

**信息更新规则**：
- 确认搜索的结果**覆盖** Phase 2 的原始信息（以最新为准）
- 如果融资信息与之前矛盾 → 更新并标注 `融资信息已更新`
- 如果仍然无法确认 → **不标注**，直接保持原样（未确认字段在报告中直接省略）

---

## 4. 亮点关键词提取

报告中的"亮点关键词"必须是**公司自身的技术/产品特点**，而非搜索时用的锚点词。

- ❌ 错误：`daytona, e2b alt, modal`（搜索锚点）
- ✅ 正确：`microVM隔离`, `sub-90ms启动`, `SOC2合规`, `开源`, `裸金属`（公司特点）

**提取方法**：从确认搜索结果中，提取 3-5 个最能代表该公司差异化的关键词：
- 技术实现（microVM / Firecracker / WASM / gVisor）
- 性能指标（sub-90ms / <50ms冷启动 / 10k+并行）
- 产品形态（开源 / 托管 / 本地优先 / BYOC）
- 合规认证（SOC2 / HIPAA）
- 目标场景（coding agent / browser automation / 企业级）

---

## 5. 生成 companies.csv

格式必须严格兼容 weekly-recommendation：

```csv
company_name,rank,score,reason,source,track,note
```

字段映射：
- `company_name` → 公司名
- `rank` → 留空
- `score` → 留空（让后续流程处理）
- `reason` → `differentiation`（1-2句话）
- `source` → 挖掘来源摘要（如 `Exa:agent sandbox startup`）
- `track` → `sub_sector`（子赛道名称）
- `note` → 留空，或标记 `非早期，Series B+，已过种子窗口`

---

## 6. 生成 prospector_notes.json

记录每个项目的完整挖掘路径：来源 query、所属子赛道、发现时间戳。

详见 `references/output_schema.md`。

---

## 字数纪律

报告全文中文，公司名保留英文。严格控制各字段字数，杜绝 GenAI 废话：

| 字段 | 上限 | 要求 |
|------|------|------|
| `differentiation` | ≤ 80 字 | 1 句话说明差异化，禁止复制搜索锚点词 |
| `analysis_summary` | 30-50 字 | 赛道总结，不含修饰语 |
| `rationale` | ≤ 30 字 | 子赛道拆分理由 |
| S/A 档公司描述 | 按模板 | 完整填写所有维度 |
| B 档公司描述 | 可简化 | 保留核心信息，省略创始人细节 |
| C 档公司描述 | 极简 | 仅 `公司名 \| 一句话亮点 \| 来源query` |

## 7. 生成 prospects_report.md（投资人扫描报告）

按**推荐度排序**，方便投资人快速扫描。

### 推荐度评分规则

| 维度 | 权重 | 评分标准 |
|------|------|----------|
| 发现轮次 | 30% | Round 1 发现=10分，Round 2=7分，Round 3=5分 |
| 信息完整度 | 30% | 有创始人+融资+官网=10分，缺一项扣3分 |
| 早期信号强度 | 25% | Launch HN/YC/Seed轮/开源高星=10分，有其中1-2个=7分，无=4分 |
| 差异化独特性 | 15% | 技术路线独特或场景独特=10分，跟随者=5分 |

**额外加分项（不占权重，总分计算后叠加）**：

| 加分项 | 条件 | 加分值 |
|--------|------|--------|
| 华人创始人信号 | `founder_name_signal=high` | +0.5 |
| 华人创始人信号 | `founder_name_signal=medium` | +0.3 |

> 加分作为 tie-breaker，提升疑似华人项目的排序优先级。此信号为基于姓名的初筛标记，不替代 `weekly-recommendation` 的确认流程。

**总分 = 加权平均 + 加分项，按分数分档**：
- **S 档（>=8.5）**：高优先级推荐
- **A 档（7.0-8.4）**：值得重点关注
- **B 档（5.5-6.9）**：中优先级，需进一步验证
- **C 档（<5.5）**：待验证线索

### 报告语言

全文中文（公司名保留英文原名，其余描述、赛道、关键词等均用中文）。

### 报告格式

```markdown
# {sector_theme} 赛道标的初筛报告

> 生成时间：{timestamp}
> 挖掘引擎：Tavily + Exa
> 总项目数：{count}
> 高优先级：{S档数量} | 重点关注：{A档数量} | 中优先级：{B档数量} | 待验证：{C档数量} | 非早期观察：{非早期数量}

---

## 挖掘路径摘要

| 维度 | 内容 |
|------|------|
| 初始锚点 | {用户提及的参考公司 / 关键概念，如 e2b, code sandbox} |
| 扩散锚点 | {Round 2 反向搜索滚动发现的新锚点，如 Daytona → Modal → Blaxel} |
| 核心关键词 | {贯穿本次挖掘的 3-5 个技术/场景关键词} |
| 子赛道覆盖 | {按优先级调度覆盖的所有子赛道名称} |
| 关键发现 | {从某个锚点扩散出的重要线索，如 "从 Daytona 的投资者 Bessemer 发现 2 个同赛道项目"} |

---

## S 档 -- 高优先级推荐

### {company_name} {总分}/10
| 维度 | 内容 |
|------|------|
| 一句话亮点 | {differentiation} |
| 具体赛道 | {sub_sector} |
| 创始人背景 | {founders} {founder_name_signal != "none" ? "【华人创始人信号: " + founder_name_signal + "】" : ""} |
| 融资信息 | {funding_stage} |
| 亮点关键词 | {3-5个公司自身技术/产品特点关键词} |

---

## A 档 -- 重点关注

...（同上格式）

## B 档 -- 中优先级

...（同上格式，可简化为紧凑列表）

## C 档 -- 待验证线索

...（仅列公司名称 + 一句话 + 来源 query）

## 非早期观察（赛道版图参考）

> 以下项目融资阶段为 Series B 及以后，或累计融资 ≥$50M，已过最典型的早期投资窗口，但仍在赛道版图中具有参考意义。

| 公司 | 一句话亮点 | 融资阶段 | 来源query |
|------|-----------|----------|----------|
| {company_name} | {differentiation} | {funding_stage} | {source_query} |
```

### 注意事项

- sector-prospector 的评分是**初筛评分**，基于搜索结果的可获得信息，不是完整的 VC due diligence
- 评分目的是帮助投资人**优先看哪些项目**，而非给出投资建议
- 最终的投资分析应由 `weekly-recommendation` 的 Phase 1-3 完成
- 挖掘路径和置信度**不放入报告**（留在 `prospector_notes.json` 中）
