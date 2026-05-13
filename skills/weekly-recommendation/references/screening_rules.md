# 华人创始人筛查规则

> 本文件为阶段1（华人筛查）的详细规则，SKILL.md 引用本文件。

---

## 强信号 → 直接视为华人（无需领英验证）

| 信号类型 | 判断标准 |
|----------|----------|
| **汉字姓名** | 姓名含汉字（如"张明""王伟"） |
| **拼音+华裔姓氏** | 全名均为拼音，且姓氏为常见华裔姓氏 |
| **明确拼音姓氏 + 西方名** | 姓氏为**高确定性拼音**（Li, Zhang, Wang, Chen, Liu, Yang, Huang, Zhao, Zhou, Wu, Xu, Sun, Ma, Zhu, Hu, Guo, He, Lin, Gao, Dai, Zheng, Feng, Han, Wen 等），名字为西方名 |
| **台港澳/新加坡拼音** | 姓名含台港澳/新加坡拼音特征（如 "Wei-Lun Huang", "Jia-En Tan"） |

**高确定性拼音姓氏**（按字母序）：

An, Bai, Cai, Cao, Chang, Chen, Cheng, Cui, Dai, Deng, Ding, Dong, Du, Duan, Fan, Fang, Feng, Fu, Gan, Gao, Ge, Gong, Gu, Han, Hao, He, Hou, Hu, Huang, Jiang, Jin, Kang, Kong, Lai, Lei, Li, Liang, Liao, Lin, Ling, Long, Lu, Luo, Ma, Mao, Meng, Miao, Niu, Pan, Peng, Qian, Qin, Qiu, Qu, Ren, Shao, Shen, Shi, Song, Su, Sun, Tan, Tang, Tian, Wan, Wang, Wen, Wu, Xia, Xiang, Xie, Xiong, Xu, Xue, Yan, Yang, Ye, Yi, Yin, Yu, Yuan, Zeng, Zhai, Zhang, Zhao, Zheng, Zhou, Zhu

**拼写变体姓氏（风险较高）**：这类拼写也可能出现在韩裔、东南亚裔或其他族裔中，需结合名字做领英验证。

| 变体类型 | 常见姓氏 |
|----------|----------|
| **粤语** | Chan, Cheung, Chiu, Choi, Chong, Chow, Ho, Kwok, Lam, Lau, Leung, Ng, Tse, Tsang, Wong, Yip, Yuen |
| **闽南语/台湾** | Hsu, Hsieh, Tsai, Tseng, Chuang, Pei, Chiang |
| **客家话** | Yong, Fong, Phua |
| **东南亚** | Oei, Tjia, Tjan, Ong |

### 台港澳/新加坡拼音参考

以下拼音体系本身即视为强信号（尤其在名字也出现对应文化特征时）：

- **香港（粤语罗马化）**：Chan, Cheung, Chiu, Choi, Chong, Chow, Fu, Hui, Kwok, Lam, Lau, Lee, Leung, Lai, Mak, Ng, Pang, Shum, So, Szeto, Tam, Tang, Tse, Tsang, Tsoi, Wan, Wong, Wu, Yau, Yip, Yu, Yuen
- **台湾（威妥玛/通用拼音）**：Hsieh, Hsu, Tsai, Tseng, Chuang, Pei, Chiang, Wei, Chou
- **新加坡/闽南语**：Tan, Lim, Ng, Ong, Goh, Chua, Koh, Teo, Ang, Yeo, Tay, Low, Toh

---

## 弱信号 → 建议做领英验证

- 姓氏为**拼写变体**（Lee, Jen, Chin, Yong, Cheung, Chiu 等）但名字是西方名或拼音
- 使用首字母缩写
- 搜索结果中出现中文拼音姓名但无法确认对应创始人

---

## 排除规则（直接跳过，不视为华人）

| 类型 | 常见姓氏 |
|------|----------|
| **日语** | 田中、山本、鈴木、佐藤、渡辺、伊藤、井上、吉田 |
| **韩语** | Kim, Park, Lee / Yi / Rhee, Kang, Choi, Ahn |
| **越南语** | 姓名含 "van", "thi", "nguyen" 且原文为越南语拼写 |

---

## 实体验证（强制）

阶段1在识别中文姓名后，必须执行实体验证（Phase 1.5），解决官网死链与创始人错配问题。

### 触发条件

- 强信号公司：官网验证（创始人已隐含在 Step 1 中）
- 弱信号公司：官网验证（同上，founder 验证已隐含在 Step 1 snippet 中）
- NOT_CHINESE 公司：跳过验证

### 验证内容

1. **官网验证**：用 `tvly extract` 批量抓取候选 URL，验证可达性（HTTP 200 + 内容 ≥200 字），区分真官网与聚合站（Crunchbase / LinkedIn / Tracxn / TheOrg 等）
2. **创始人验证**：隐含在 Step 1 搜索结果中。从 Tavily/Exa snippet 中提取 founder 姓名时，同步确认 snippet 中已把该名字和公司绑定。仅当 Step 1 完全无 founder 信息时，才补充搜索 Crunchbase/LinkedIn。

### 处理结果

- 官网通过 + Step 1 已提取 founder → CONFIRMED
- 官网聚合站/打不开 + Step 1 已提取 founder → CONFIRMED（`verified_website` 留空）
- 官网+创始人双双失败 → UNCLEAR，`error: entity_verification_failed`

详见 `references/entity_verification.md`。

---

## LinkedIn 登录态预检查

在尝试任何 LinkedIn 弱信号验证前，agent 必须先执行以下预检查：

```bash
agent-browser --session-name linkedin open "https://www.linkedin.com/"
agent-browser --session-name linkedin wait 3000
agent-browser --session-name linkedin eval "(function() { return window.location.href; })();"
```

- 若 URL 仍停留在 `linkedin.com/login` 或 `linkedin.com/authwall`，说明 session 无效
- **处理方式**：跳过所有弱信号的 LinkedIn 验证，将相关公司标记为 `UNCLEAR`，`error` 字段记录 `linkedin_session_invalid`
- **不阻塞**筛查流程，继续处理其他公司

---

## L3: agent-browser LinkedIn 验证（fallback）

> 仅当 L1（官网抓取）和 L2（search snippet 反查）都未命中时执行；若 L3 也无可用 LinkedIn slug，则标 `failed`（最终状态为 UNCLEAR）。

对弱信号创始人，agent 直接调用 agent-browser 打开 LinkedIn 个人页面，提取页面文本并判定：

```bash
agent-browser --session-name linkedin open "https://www.linkedin.com/in/<url-slug>/"
agent-browser --session-name linkedin wait --load networkidle
agent-browser --session-name linkedin wait 2000
agent-browser --session-name linkedin eval --stdin <<'EVALEOF'
(function() {
  const text = document.body.innerText;
  const keywords = [
    // 语言能力
    "Chinese","Mandarin","中文","普通话","Cantonese","粤语",
    // 中国大陆大学
    "Tsinghua","Peking","Fudan","SJTU","Zhejiang","USTC","Nanjing","Renmin","Wuhan","Harbin","Sun Yat-sen","Beihang","Beijing Normal","Tongji","Nankai","Sichuan","Xi'an Jiaotong","HUST","UESTC","Southeast","SCUT","ECNU","SUFE","UIBE",
    // 港澳台/新加坡大学
    "HKU","HKUST","NUS","NTU","CUHK","CityU","PolyU","清华","北大","复旦","交大","浙大","中科大","南大","人大","武大","哈工大","中大","港大","科大","新国立","南洋理工","港中文","港科大",
    // 中国大陆城市
    "Beijing","Shanghai","Shenzhen","Hangzhou","Guangzhou","Chengdu","Xi'an","Tianjin","Suzhou","Chongqing","Qingdao","Dalian","Xiamen","Changsha","Hefei","Jinan","Fuzhou",
    // 港澳台/新加坡城市
    "Hong Kong","Taipei","Taichung","Kaohsiung","Hsinchu","Macau",
    // 科技公司
    "字节","腾讯","阿里","百度","华为","小米","美团","滴滴","京东","网易","Pinduoduo","拼多多","Kuaishou","快手","Xiaohongshu","小红书","Bilibili","哔哩哔哩","Weibo","微博","iQiyi","爱奇艺","Sohu","搜狐","Ctrip","Trip.com","携程","Lenovo","联想","DJI","大疆","SenseTime","商汤","Megvii","旷视","iFlytek","科大讯飞",
    // 汽车/硬件/制造
    "CATL","宁德时代","BYD","比亚迪","NIO","蔚来","XPeng","小鹏","Li Auto","理想汽车","Hikvision","海康威视","ZTE","中兴","Qihoo 360","奇虎360","SF Express","顺丰",
    // 社团/文化信号
    "CSSA","Chinese Students and Scholars Association"
  ];
  const hits = [];
  keywords.forEach(k => { if (text.includes(k)) hits.push(k); });
  return JSON.stringify({
    hitCount: hits.length,
    hits: hits,
    preview: text.substring(0, 6000) + (text.length > 6000 ? "\n...[truncated]" : "")
  });
})();
EVALEOF
```

**满足任意一项即 CONFIRMED**：
- 教育背景含中国大学（清华、北大、复旦、交大、浙大、中科大、南大、人大、武大、哈工大、中大、港大、科大、新国立、南洋理工、北航、同济、南开、川大、西安交大、华科、电子科大、东南等）
- 工作经历含中国公司（字节、腾讯、阿里、百度、华为、小米、美团、滴滴、京东、网易、拼多多、快手、小红书、B站、携程、联想、大疆、商汤、旷视、科大讯飞、宁德时代、比亚迪、蔚来、小鹏、理想、顺丰等）
- LinkedIn "About" 或 "Language" 标注 Chinese / Mandarin / 中文 / 普通话 / Cantonese / 粤语
- 个人简介出现中文
- 出现 CSSA、Chinese Students and Scholars Association 等华人学生社团

---

## 弱信号升级规则

LinkedIn 验证结果按命中质量决定如何升级置信度：

| 命中类型 | 升级动作 |
|----------|----------|
| **直接 CONFIRMED** | 命中上述任意一项核心标准（大学/公司/中文/CSSA） |
| **强辅助信号** | Profile 中出现华人校友会、中文媒体采访链接、繁体中文姓名标注等 → 可升至 **MEDIUM** 或更高 |
| **头像/照片弱信号** | LinkedIn 头像明显为亚裔 → 仅作 **LOW** 辅助参考，不可单独 CONFIRMED |
| **零命中** | 页面无上述任何关键词 → 保持 **UNCLEAR** 或 **NOT_CHINESE**（需结合 Tavily/Exa 其他搜索结果综合判断） |

---

## 置信度标准

| 置信度 | 触发条件 |
|--------|----------|
| **HIGH** | 创始人姓名含汉字；或拼音+领英验证命中 2 项以上；或同时发现多项中文姓名线索 |
| **MEDIUM** | 拼音姓名，领英验证命中 1 项；或姓氏为高概率华裔姓氏（李、王、张、刘、陈）且有一项辅助信号 |
| **LOW** | 仅有姓氏匹配，无其他验证；或搜索结果极少，信息严重不足；或 UNCLEAR 状态无法升级 |

---

## 公司类型判定（本土 vs 海外华人）

确认是华人公司后，agent 从同一批 Step 1 搜索结果中进一步判定是**本土华人公司**还是**海外华人公司**，决定是否进入 Phase 2 投资分析。

### 判定优先级（从高到低）

1. **主要服务市场**（最高优先级）：产品/服务明确仅面向中国大陆市场 → DOMESTIC_CHINESE；明确面向海外（欧美、东南亚等）→ OVERSEAS_CHINESE
2. 创始人姓名语言：汉字姓名 → 倾向本土；拼音姓名 → 倾向海外
3. 公司名语言：纯中文/纯拼音 → 倾向本土；纯英文 → 倾向海外
4. 媒体来源：中文媒体为主 → 倾向本土；英文媒体为主 → 倾向海外

> **不作为独立判定依据**：官网语言、域名后缀（.cn/.com）、中文社交媒体账号。这些仅作辅助参考，**不得**因"有中文官网"或".cn 域名"就直接标为 DOMESTIC_CHINESE。

### 默认策略

信号冲突或无法明确判断时，**保守标为 OVERSEAS_CHINESE**（宁可多分析几家）。

### 判定结果

| company_type | 含义 | Phase 2 | Phase 3 排名表 |
|--------------|------|---------|----------------|
| `OVERSEAS_CHINESE` | 海外华人公司 | **进入** | **评分排名** |
| `DOMESTIC_CHINESE` | 本土华人公司 | **不进入** | **不进入**，在最终报告"本土华人公司名单"中列出名称和 tagline |
| `NOT_CHINESE` | 非华人公司 | 不进入 | 不进入 |

---

## 状态判定

| 状态 | 条件 |
|------|------|
| `CONFIRMED` | 找到明确的华人/华裔创始人，且 company_type 已判定（OVERSEAS_CHINESE 或 DOMESTIC_CHINESE） |
| `NOT_CHINESE` | 创始团队全部为非华人，无任何中文信号 |
| `UNCLEAR` | 找到中文拼音姓名但无法通过实体验证确认（官网验证失败且 Step 1 无 founder 信息），或信息不足，或 API 全部失败，或无法判定华人身份 |
| `SKIP_PUBLIC_HYPE` | 阶段0已标记为过度曝光/已成熟项目，不进入阶段1搜索 |

---

## 阶段0量化排除标准

阶段0爬取时，若从榜单 reason 或公开信息中可直接识别以下任一条件，即标记为 `SKIP_PUBLIC_HYPE`：
- 公司已上市（IPO）
- 国内项目累计融资额 **>10 亿人民币**
- 项目估值 **>$1B**（10 亿美元）
- 公司已是家喻户晓的超级独角兽（媒体曝光度极高，如 Manus、Genspark 等）

---

## 状态转移规则

```
PENDING  → CONFIRMED      (找到明确华人创始人且实体验证通过)
PENDING  → NOT_CHINESE    (确认无华人创始人)
PENDING  → UNCLEAR        (信息不足，需人工复核)
PENDING  → SKIP_PUBLIC_HYPE  (阶段0已标记为过度曝光/已成熟项目，直接跳过)
PENDING  → UNCLEAR        (实体验证全部失败:entity_verification_failed)
UNCLEAR  → CONFIRMED      (补充搜索后找到确认信号)
UNCLEAR  → NOT_CHINESE    (补充搜索后确认无华人)
UNCLEAR  → PENDING        (需要重新搜索)
```

---

## Checkpoint 字段定义（SQLite Schema）

`scripts/screening_db.py` 使用的数据库字段说明：

| 列名 | 类型 | 含义 | 示例 |
|------|------|------|------|
| `company` | TEXT PK | 公司名称 | `Patlytics` |
| `status` | TEXT | `PENDING`/`CONFIRMED`/`NOT_CHINESE`/`UNCLEAR` | `CONFIRMED` |
| `company_type` | TEXT | `OVERSEAS_CHINESE`/`DOMESTIC_CHINESE`/`NOT_CHINESE` | `OVERSEAS_CHINESE` |
| `source` | TEXT | 信源 | `Pitchbook\|ARR` |
| `score` | REAL | 榜单评分 | `9.0` |
| `track` | TEXT | 赛道 | `AI 医疗` |
| `reason` | TEXT | 上榜理由 | `AI denial management` |
| `founder_name` | TEXT | 创始人姓名 | `Wilson Wang` |
| `founder_verification_layer` | TEXT | `L0_search_snippet` / `L1_supplement` / `failed` | `L0_search_snippet` |
| `verified_website` | TEXT | 验证通过的官网 URL | `https://patlytics.ai` |
| `website_verification_status` | TEXT | `verified` / `indirect_verified` / `aggregator_only` / `unreachable` / `not_attempted` | `verified` |
| `evidence_quote` | TEXT | ≤200 字的证据原文 | `"Paul Lee, CEO at Patlytics..."` |
| `evidence_url` | TEXT | 证据来源 URL | `https://linkedin.com/in/...` |
| `error` | TEXT | 错误/异常标记 | `search_conflated` |
| `updated_at` | TIMESTAMP | 最后更新时间 | — |
