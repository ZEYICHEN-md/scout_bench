# 搜索引擎策略与 CLI 调用规范

> 本文件规范 Phase 1-2 的搜索引擎使用策略、CLI 调用方式和错误处理规则。

---

## 双引擎分层使用策略

**不是每个 query 都双引擎**，按环节定策略，平衡覆盖面和 API 成本：

| 环节 | 引擎策略 | 原因 |
|------|---------|------|
| **Phase 1 赛道解构** | 单引擎（Tavily 为主） | 目的是理解赛道结构，不需要交叉验证 |
| **Phase 2 Round 1 锚点直接搜索** | **必须双引擎并行** | 发现项目的核心轮次，Tavily 偏新闻融资、Exa 偏语义深度，互补覆盖 |
| **Phase 2 Round 2 反向扩散** | **必须双引擎并行** | 从已知项目找竞品/投资者/创始人，需要最大覆盖 |
| **Phase 2 Round 3 维度补充** | 单引擎即可（Tavily） | 查缺补漏，如果 Round 1/2 已发现足够项目，快速扫一遍即可 |

### 两个引擎的分工

- **Tavily**：更适合找融资新闻、TechCrunch 报道、产品发布、融资轮次信息
- **Exa**：更适合语义搜索、找到不那么"热门"但技术扎实的早期项目，以及学术/开源转化线索

### 双引擎并行执行方式

同一个 query 同时投到两个引擎：

```bash
# Tavily
tvly search "{query}" --json --max-results 10 --depth basic > tavily_results/{sub_sector}_{round}_{keyword}.json

# Exa（同时执行）
mcporter call 'exa.web_search_exa(query: "{query}", numResults: 10)' > exa_results/{sub_sector}_{round}_{keyword}.json
```

---

## CLI 工具调用规范

### Tavily

**首选**：`tvly search "{query}" --json --max-results 5 --depth basic`

**参数说明**：
- `--json`：输出 JSON 格式，便于解析
- `--max-results 5`：默认 5 条，Phase 1/2 可用 10 条
- `--depth basic`：快速搜索，balanced 用于深度验证

**备选**（curl）：

```bash
curl -s -X POST https://api.tavily.com/search \
  -H "Content-Type: application/json" \
  -d "{\"api_key\":\"$TAVILY_API_KEY\",\"query\":\"{query}\",\"max_results\":5,\"search_depth\":\"basic\",\"include_answer\":true}"
```

### Exa

**首选**：`mcporter call 'exa.web_search_exa(query: "{query}", numResults: 5)'`

**参数说明**：
- `numResults`：结果数量，Phase 1/2 可用 10
- `useAutoprompt`：自动优化 query（可选）

**备选**（curl）：

```bash
curl -s -X POST https://api.exa.ai/search \
  -H "Content-Type: application/json" \
  -H "x-api-key: $EXA_API_KEY" \
  -d "{\"query\":\"{query}\",\"numResults\":5,\"useAutoprompt\":true,\"type\":\"auto\"}"
```

---

## 限速与错误处理

| 场景 | 处理方式 |
|------|----------|
| 429/503 | 等 15 秒重试；同 key 连续 3 次失败后切换备用 key |
| 401/403 | 立即切换 key |
| 所有 key 均失败 | 记录 error，当前 query 跳过，不阻塞整批 |
| 单条 query 搜索失败 | 记录 error，继续处理其他 query |
| 搜索超时（无响应 > 30s）| 终止当前 query，标记超时，继续下一批 |

### 指数退避重试策略（推荐）

替代固定 15s 重试，使用指数退避：

```
第 1 次失败：等 15s 重试
第 2 次失败：等 30s 重试
第 3 次失败：等 60s 重试，同时切换备用 key
```

---

## 并发控制

- 同一子赛道内，每批并行 **5 个** search query
-  Tavily 和 Exa 的同一 query 在**同一 Bash 调用**中并行执行（用 `&` 后台 + `wait`）
- 所有原始 JSON 保存到 `tavily_results/` 和 `exa_results/`，文件名格式：`{sub_sector}_{round}_{keyword}_{engine}.json`
