# Public Hype 过滤规则

> 本文件规范 `sector-prospector` Phase 3 的 public hype 过滤逻辑。目标是排除已经被大众媒体广泛曝光、已进入共识阶段的知名公司，保留早期、非共识的项目。

---

## 过滤层级

### 第一层：硬性排除（命中任一即排除，无需搜索验证）

**1. 已上市**
- 在纳斯达克、纽交所、港交所、科创板等已 IPO 的公司
- 已知 SPAC 上市的公司

**2. 超级独角兽 / 家喻户晓**
- 估值 $10B+ 且媒体曝光度极高的公司
- 典型名单（AI/Agent/具身智能相关）：OpenAI, Anthropic, xAI, Character.AI（被收购前）, Manus, Genspark, Figure AI, 1X Technologies, Physical Intelligence
- 中国背景：DeepSeek, 智谱AI, 月之暗面, MiniMax, 零一万物, 百川智能, 阶跃星辰

**3. 估值 / 融资额阈值**
- 估值 **≥ $1B**（10亿美元）
- 累计融资额 **≥ 10 亿人民币**（约 $140M）
- 对于美国项目，Series C 及以后的公司**建议排除**（除非处于非常小众的细分赛道）

**4. 已被大型科技公司收购**
- 被 FAANG + Microsoft + Tesla + NVIDIA 等收购的公司（通常已失去早期投资价值）

---

### 第二层：快速验证（疑似 hype 时搜索确认）

当 agent 对一个公司是否属于 public hype 不确定时，执行快速验证：

```bash
tvly search "{company_name} valuation funding IPO series" --json --max-results 3 --depth basic
```

**验证标准**：
- 如果搜索结果明确显示估值 ≥$1B 或已上市 → 排除
- 如果搜索结果显示是大型科技公司的内部项目/子公司 → 排除
- 如果搜索结果中该公司频繁出现在"Top 10 AI Startups""Most Valuable AI Companies"等列表中 → 排除
- 如果无法确认（信息太少），**保留**（宁可误留，不误杀）

---

### 第三层：模式识别（从名称/描述判断）

**明显是描述性条目而非真实公司名的**：
- 纯描述性短语："AI 客服系统"、"数据分析工具"、"垂直基建AI"
- 以通用名词结尾："XX平台"、"XX引擎"、"XX助手"
- 含占位符："XX公司高管创业项目"

这些不是 public hype 问题，而是数据质量问题。直接排除。

---

## 常见误判与处理

| 情况 | 处理 |
|------|------|
| 大公司的新产品/子品牌（如 "Microsoft Copilot"） | 排除，这不是独立公司 |
| 知名公司的前员工创业项目（如 "ex-OpenAI founder's new project"） | **保留**，这正是我们要找的早期信号 |
| 已有一定知名度但仍在 Seed/Series A 的项目（如刚完成 $10M 融资） | **保留**，$10M 融资不等于 public hype |
| 被 TechCrunch 报道过一次的公司 | **保留**，单次报道不等于 hype，要看是否频繁出现在各种榜单中 |
| 中国公司，无法确认估值 | 保留，标注 "估值待确认"，交给后续流程处理 |

---

## 软性标记（不强制排除，但需标注）

有些公司**未达到硬性排除阈值**，但已经过了最典型的早期投资窗口。这类公司**不强制排除**，而是保留在结果中，并在 `note` 或 `prospects_report.md` 中标注，让投资人自行判断。

**触发条件**：
- 融资阶段为 **Series B 及以后**
- 或累计融资额 **≥ $50M**
- 或在开发者/投资圈已有较高知名度（如频繁出现在对比文章、benchmark 中）

**处理方式**：
- 保留在 `companies.csv` 中
- 在 `note` 字段标注：`非早期，Series B+，已过种子窗口`
- 在 `prospects_report.md` 中下调一档（如 S→A，A→B）或单独列出

**为什么不直接排除**：
- sector-prospector 的定位是**信息发现和收集**，不是投资决策
- 某些 Series B 公司如果处于**非常小众的细分赛道**或**近期有重大技术突破**，仍可能有投资价值
- 投资人可能有不同的投资阶段偏好（如成长期基金）
- 最终的投资判断应交给 `weekly-recommendation` 的完整分析流程

---

## 过滤后处理

被排除的公司，在 `prospector_notes.json` 中记录排除原因：

```json
{
  "company_name": "OpenAI",
  "excluded": true,
  "reason": "public_hype: 估值$80B+，家喻户晓",
  "source_query": "agent sandbox startup"
}
```

这有助于用户审计："为什么某个知名公司没有出现在列表中？"

---

## 与 weekly-recommendation 的衔接

`sector-prospector` 生成的 `companies.csv` 中的 `note` 字段，可复用 weekly-recommendation 的标记：

- `SKIP_PUBLIC_HYPE` — 在 sector-prospector 中已被排除，不应出现在最终 CSV 中
- 如果 sector-prospector 判断失误，让某个 public hype 公司混入了 CSV，weekly-recommendation 的 Phase 0/1 可再次标记

**原则**：sector-prospector 做第一轮粗筛，weekly-recommendation 做第二轮精筛。两层过滤降低漏网率。
