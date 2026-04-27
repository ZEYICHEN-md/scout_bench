# 实体验证规则

> 本文件为阶段1实体验证（Phase 1.5）的详细规则，SKILL.md 和 screening_rules.md 引用本文件。
> 目标：将“信任 search snippet”升级为“打开页面再核对”，解决官网死链与创始人错配问题。

---

## 1. 官网识别

### 1.1 聚合站黑名单

以下域名出现在 search snippet 中时，视为**非官网**，仅可作为创始人验证的辅助来源：

```
crunchbase.com, linkedin.com, tracxn.com, cbinsights.com, theorg.com,
wikipedia.org, pitchbook.com, dealroom.co, businessinsider.com,
forbes.com, techcrunch.com, ycombinator.com, producthunt.com, github.com
```

### 1.2 官网正向规则

必须**同时满足**：
1. 域名 token 包含 normalized 公司名（去空格 / 去 "AI"/"Inc"/"Labs" 后缀），**或** search snippet 明确出现 "official site" / "homepage" 指向该 URL
2. 不在黑名单中

> **不满足条件1的 URL**（如 `36kr.com/p/xxx`、`techcrunch.com/xxx`）→ **不视为候选官网**，不传给 `tvly extract` 做官网验证。这些媒体文章可作为 L2 founder 验证的信息来源，但本身不是官网。

**示例**：

| 公司名 | URL | 是否候选官网 | 原因 |
|--------|-----|-------------|------|
| Patlytics | `patlytics.ai` | ✅ 是 | token 匹配 |
| Patlytics | `crunchbase.com/organization/patlytics` | ❌ 否 | 黑名单 |
| Mastra | `mastra.ai` | ✅ 是 | token 匹配 |
| Spirit AI | `spiritai.cn` | ✅ 是 | token 部分匹配 |
| Red Bear AI | `36kr.com/p/redbear-ai` | ❌ 否 | 媒体文章，非官网 |

---

## 2. 官网可达性验证

### 2.1 工具调用

```bash
# 一次最多 20 URLs；5 家公司 × 每家 2-4 个候选 URL，正好一批
tvly extract <url1> <url2> ... <urlN> \
  --query "{company_name} {keyword1} {keyword2} founder" \
  --chunks-per-source 3 \
  --json
```

> 参数说明：
> - `--query`：定向抽取与创始人/公司相关的文本片段，减少无关内容噪音
> - `--chunks-per-source 3`：每个 URL 返回最多 3 个相关片段
> - `--json`：结构化输出，方便解析 `http_status`、`content`、`raw_content`

### 2.2 判定标准

| 结果 | 条件 | `website_verification_status` | `verified_website` |
|------|------|------------------------------|-------------------|
| 通过 | HTTP 200 + 内容非空 + 内容字数 ≥ 200 | `verified` | 填该 URL |
| 不可达 | HTTP 4xx/5xx / 超时 / 内容为空 | `unreachable` | 留空 |
| 无独立官网 | 全部候选 URL 都是聚合站（通过黑名单过滤后无剩余） | `aggregator_only` | 留空 |

> **字数 ≥ 200 的过滤目的**：排除纯 landing page（仅含 "Coming soon"、邮箱订阅框、无实质内容）。允许 marketing site，只要内容足够识别产品形态。

---

## 3. 创始人验证

> **创始人验证不需要额外搜索步骤**。
>
> Step 1 搜索 `{company_name} {keywords} founder/CEO/CTO` 时，Tavily/Exa 返回的 snippet 中提到的人名**天然就是该公司的 founder**——因为 query 已包含公司名，搜索引擎返回的结果都是关于该公司的，snippet 中的职位描述（如 "CEO at Patlytics"、"co-founder of Mastra"）自然完成了 founder-company 绑定。
>
> 因此：
> - **默认情况**：从 Step 1 snippet 中提取 founder 姓名时，**同步完成了 founder 验证**
> - `founder_verification_layer` 默认记为 `L0_search_snippet`
>
> **仅当 Step 1 结果完全没有 founder 信息时**，才补充搜索：
> ```
> {company_name} crunchbase founders
> {founder_name} linkedin {company_name}
> ```
> 补充搜索命中 → `founder_verification_layer = L1_supplement`
> 补充搜索也未命中 → `founder_verification_layer = failed`

---

## 4. 官网+创始人综合判定

| 官网验证 | 创始人信息 | 状态 | Phase 2 | 备注 |
|---------|-----------|------|---------|------|
| ✅ `verified` | ✅ Step 1 已提取 founder | CONFIRMED | 进入 | 正常 case |
| ❌ `aggregator_only` / `unreachable` | ✅ Step 1 已提取 founder | CONFIRMED | 进入 | `verified_website` 留空，备注"无独立官网，见 Crunchbase 链接" |
| ✅ `verified` | ❌ Step 1 无 founder + 补充搜索失败 | UNCLEAR | 不进 | `error: entity_verification_failed` |
| ❌ | ❌ | UNCLEAR | 不进 | `error: entity_verification_failed` |

---

## 5. Phase 1.5 触发条件

- **强信号公司**：官网验证（创始人已隐含在 Step 1 中，无需额外搜索）
- **弱信号公司**：官网验证（同上， founder 验证已隐含在 Step 1 snippet 中）
- **NOT_CHINESE 公司**：不验证（节省调用）

---

## 6. 工具与限速

| 工具 | 用途 | 限速处理 |
|------|------|---------|
| `tvly extract` | 官网可达性验证 | 复用 Tavily key 轮换策略（每 5 次切 key） |
| `tvly search` / Exa search | Step 1 搜索 + 补充 founder 搜索（极少触发） | 复用现有 search 限速策略 |
| `agent-browser` | 补充 LinkedIn 验证（极少触发） | 仅 Step 1 完全无 founder 信息时才考虑 |
