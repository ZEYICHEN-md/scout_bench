# 阶段0 数据信源规则

> 本文件规范 `weekly-recommendation` 阶段0（公司列表采集）的多信源处理逻辑。

---

## 通用提取脚本

所有 readtheone 榜单页面（Pitchbook / ARR / LinkedIn 大厂华人离职员工 / Kickstarter）共享同一 DOM 结构，使用同一脚本提取：

```bash
agent-browser eval --file "<skill-dir>/scripts/extract_readtheone.js"
```

> 脚本位置：`weekly-recommendation/scripts/extract_readtheone.js`

## 非真实公司名过滤

**agent 人工过滤非真实公司名**：榜单中常混入描述性条目，agent 在写入 CSV 前必须逐项过滤。

### 过滤规则（命中任一即剔除）

| 规则 | 说明 | 示例 |
|------|------|------|
| **纯描述性短语** | 仅有"形容词/功能词 + 通用名词"，无专有名词或品牌词 | `专家支持系统`、`高效率GTM工具`、`隐私驱动生产力`、`垂直基建AI` |
| **以通用名词结尾** | 结尾为系统/工具/平台/解决方案/框架/引擎/助手/基建/驱动/赋能/生产力等 | `AI客服系统`、`数据分析工具` |
| **赛道标签式命名** | 像行业分类标签而非具体品牌 | `AI视频广告平台`、`B2B营销自动化` |
| **含占位符/模糊词** | 含"XX公司"、"某"、"高管"等占位符 | `XX公司高管创业项目`、`某独角兽联创项目` |
| **纯英文通用词组合** | 无独特造词，仅为领域常见词拼接 | `AI Data Platform`、`Smart Assistant` |

### 真实公司名 vs 描述性条目对比

| 真实公司名（保留） | 描述性条目（剔除） |
|-------------------|-------------------|
| Panta、Genspark、Manus（独特造词） | `专家支持系统` |
| SpaceX、Anthropic（专有名词） | `高效率GTM工具` |
| Canvas、Notion（常见词但组合独特） | `隐私驱动生产力` |
| OpenAI、DeepMind（人名/概念+独特后缀） | `垂直基建AI` |
| Character.AI（含具体产品名） | `AI视频广告平台` |

> **操作建议**：对每条提取结果，先快速对照上表判断。不确定时，用 WebSearch 搜索该名称 + "官网"验证——如果搜索结果全是行业分析文章而非具体公司官网，则大概率是描述性条目。
---

## 信源 1：Pitchbook 榜单

**目标页面**（先尝试中文创始人筛选）：
```
https://trends.readtheone.com/projects?page=1&source=Pitchbook&track=&chinese=true
```

**回退机制**：
1. 先用 `chinese=true` 打开页面并执行提取脚本
2. 若提取结果为空（0 条公司记录），则回退到无中文筛选的 URL：
   ```
   https://trends.readtheone.com/projects?page=1&source=Pitchbook&track=&chinese=
   ```
3. 重新提取，将结果写入 `companies.csv`

**处理规则**：
- 标准筛查信源，全部进入阶段1
- 无特殊过滤规则

---

## 信源 2：ARR 榜单

**目标页面**：`https://trends.readtheone.com/projects?page=1&source=arr&track=&chinese=true`

**特殊处理**：ARR 榜单中常包含已过度曝光/水上的知名项目。命中以下任一条件即标记为 `SKIP_PUBLIC_HYPE`，**不进入阶段1筛查**：
- 公司已上市（IPO）
- 国内项目累计融资额 **>10 亿人民币**
- 项目估值 **>$1B**（10 亿美元）
- 公司已是家喻户晓的超级独角兽（估值 $10B+ 且媒体曝光度极高，如 Manus、Genspark 等）
- 从榜单 reason 或来源列可直接识别的明显水上项目

agent 在阶段0爬取时，对命中条件的公司在 `companies.csv` 的 `note` 字段标记 `SKIP_PUBLIC_HYPE`。

---

## 信源 3：LinkedIn 大厂华人离职员工

**目标页面**：`https://trends.readtheone.com/projects?source=Linkedin%E5%A4%A7%E5%8E%82%E5%8D%8E%E4%BA%BA%E7%A6%BB%E8%81%8C%E5%91%98%E5%B7%A5&track=&chinese=true`

**定位**：监控型信源。该信源变动较少，**核心目的是监控名单变化**，而非每轮都做深度投资分析。

### 监控机制

1. **保存快照**：爬取后保存完整名单到 `$WORKSPACE/linkedin_hires_snapshot.json`
   ```json
   {"date": "2026-04-17", "companies": ["公司A", "公司B", "公司C"]}
   ```
2. **对比历史快照**：检查上一次 `linkedin_hires_snapshot.json`（优先查找最近的历史工作目录，其次查找固定历史路径）
   - 若**无新增公司**：final report 的执行摘要中直接写 `LinkedIn 大厂华人离职员工信源无变动信号`
   - 若**有新增公司**：将新增公司写入 `companies.csv`，`source` 标记为 `LinkedInHires`，进入正常阶段1→阶段2分析流程

### Final Report 呈现规则

- **无新增**：在执行摘要末尾追加一句 `LinkedIn 大厂华人离职员工信源无变动信号`
- **有新增**：
  - 执行摘要中单独列出新增公司名称
  - 若新增公司经阶段1/2分析后产生 `CONFIRMED` 且有投资信号，正常纳入 VC 评分排名和投资分析正文
  - 可选在 final report 末尾加"LinkedIn 大厂华人离职员工监控附录"，列出本次新增名单

---

## 断点续爬

- 状态文件：`$WORKSPACE/scrape_state.json`，按信源隔离存储
  ```json
  {"pitchbook": {"last_page": 3}, "arr": {"last_page": 2}, "linkedinhires": {"last_page": 1}, "kickstarter": {"last_page": 1}}
  ```
- 每成功翻一页，立即更新对应信源的 `last_page`

---

## 信源 4：Kickstarter 榜单

**目标页面**：`https://trends.readtheone.com/projects?source=kickstarter&track=&chinese=true`

**处理规则**：
- **仅爬取第一页**，不翻页
-  Stage1 准入需同时满足以下三个条件：
  1. 榜单评分 **≥ 9**
  2. 众筹/融资额 **> $1M**（100 万美元）
  3. 项目为 **AI 原生产品**（从 `reason` 或 `track` 列可直接识别为 AI 项目）
- 未同时满足以上条件的公司标记为 `SKIP_KICKSTARTER_FILTER`，不进入阶段1

### 投资分析模板

Kickstarter 项目通常处于早期（尚未完成公司化或尚未获得 VC 融资），投资分析采用**简版众筹项目模板**，不套用标准 Verdict 结构：

```markdown
# 【项目名称】Tiiny AI Pocket Lab
官网：<https://example.com>（如有）
【产品】口袋级本地120B LLM推理设备，提供私密、无需云端的本地化AI运行体验。
【核心卖点】全球首个可于口袋级设备上运行高达1200亿参数（120B）大模型的本地AI设备。
【众筹表现】截至4月初，众筹金额已接近300万美元，获得超过2000名支持者。上线仅5小时，众筹金额便突破100万美元。
【公司状态】20XX年X月已成立公司
【团队】CEO [姓名]，前[公司][岗位职级]，全职团队5人。上海交大团队孵化
【交付预期】2026年8月
【追踪建议】公司化已完成，建议交付后立即接触，预判天使轮窗口
```

### 公司化/团队信息查证渠道

Kickstarter 项目信息较稀缺，按以下优先级补充查证：
1. **中国内地项目**：天眼查 / 企查查（查工商注册、成立时间、股东结构）
2. **海外项目**：Crunchbase / OpenCorporates（查公司注册信息）
3. **创始人 LinkedIn**：查看 "About" 或 "Experience" 栏是否标注了公司名
4. **公司官方 LinkedIn 页面**（验证公司存在、团队规模、动态更新）
5. **公司官网**（如有，优先放在项目名称下方）
6. **媒体报道 / 众筹页面 FAQ**：提取公司背景、团队规模、交付计划等线索
7. **以上均查不到**：在 `investment_analysis.md` 中明确标注"公司注册信息未公开"，并基于已有信息给出追踪建议

---

## 去重与写入

- 多信源合并后，按 `company_name` 去重
- 若同一家公司出现在多个信源，`source` 列合并写入（如 `Pitchbook|ARR`）
- `note` 列记录 `SKIP_PUBLIC_HYPE` 等标记
- 最终写入 `companies.csv`：
  ```csv
  company_name,rank,score,reason,source,track,note
  Panta,1,9.2,AI Insurance,Pirate、AON、Liberty,Insurance AI,
  Genspark,3,8.5,...,...,...,SKIP_PUBLIC_HYPE
  ```
