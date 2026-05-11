# Top-Tier Venues for 顶刊顶会&一二作引用量 Calculation

A paper counts toward **顶刊顶会&一二作引用量** only if it meets **all** of the following criteria:
1. Published in one of the venues below (or a clear sub-journal thereof).
2. The target scholar is **first or second author**.
3. **Co-first authors**: If Google Scholar or the author list indicates a co-first author (`*`, equal contribution, etc.), the target scholar is counted as **first author** regardless of position.

## Machine Learning

- NeurIPS (Neural Information Processing Systems)
- ICML (International Conference on Machine Learning)
- ICLR (International Conference on Learning Representations)
- JMLR (Journal of Machine Learning Research)
- TMLR (Transactions on Machine Learning Research)

## Computer Vision

- CVPR (IEEE/CVF Conference on Computer Vision and Pattern Recognition)
- ICCV (IEEE/CVF International Conference on Computer Vision)
- ECCV (European Conference on Computer Vision)
- TPAMI (IEEE Transactions on Pattern Analysis and Machine Intelligence)
- IJCV (International Journal of Computer Vision)

## Robotics

- ICRA (IEEE International Conference on Robotics and Automation)
- IROS (IEEE/RSJ International Conference on Intelligent Robots and Systems)
- RSS (Robotics: Science and Systems)
- CoRL (Conference on Robot Learning)
- IJRR (International Journal of Robotics Research)
- T-RO (IEEE Transactions on Robotics)
- Science Robotics

## Artificial Intelligence (General)

- AAAI (AAAI Conference on Artificial Intelligence)
- IJCAI (International Joint Conference on Artificial Intelligence)

## NLP / LLM

- ACL (Association for Computational Linguistics)
- EMNLP (Empirical Methods in Natural Language Processing)
- NAACL (North American Chapter of the ACL)
- TACL (Transactions of the ACL)
- COLING (International Conference on Computational Linguistics)
- Findings of ACL / Findings of EMNLP / Findings of NAACL (ACL 官方 Findings track)

## Data Mining / Web / Knowledge Engineering

- KDD (ACM SIGKDD Conference on Knowledge Discovery and Data Mining)
- WWW (The Web Conference, formerly International World Wide Web Conference)
- TKDE (IEEE Transactions on Knowledge and Data Engineering)

## Interdisciplinary & General Science (AI-related only)

- Nature (仅限 AI/ML/CS 相关主题)
- Science (仅限 AI/ML/CS 相关主题)
- PNAS (Proceedings of the National Academy of Sciences, 仅限 AI/ML/CS 相关主题)

> **Important**: 以上 venue 列表覆盖 AI、ML、CV、Robotics、NLP、Data Mining 六大领域及跨学科顶刊。被计入「顶刊顶会&一二作引用量」仅代表论文发表在上述顶刊顶会上，不代表其研究方向一定与创业路线**直接相关**——相关性需根据论文标题单独判断。例如：一篇 NeurIPS 纯理论优化论文可以计入「顶刊顶会&一二作引用量」，但在 relevance 分析中可能被评为 "中等相关" 或 "低相关"。
>
> **Nature / Science / PNAS 的特殊说明**：这三本为综合科学顶刊，在 AI 细分领域内影响力极高。但仅限与 AI/ML/CS 直接相关的论文计入（如 DeepSeek-R1、AlphaFold 等）；纯生物、纯物理等非 AI 主题论文不计入。

## Matching Aliases & Known Variants

Scholar 上的 venue 字符串不统一，以下别名必须**同等视为命中**：

| 标准名 | 必须同时匹配的别名/变体 |
|--------|------------------------|
| NeurIPS | `neural information processing systems`, `nips`, `advances in neural` |
| ICML | `international conference on machine learning` |
| ICLR | `international conference on learning representations` |
| JMLR | `journal of machine learning research` |
| AAAI | `aaai conference on artificial intelligence` |
| IJCAI | `international joint conference on artificial intelligence` |
| CVPR | `conference on computer vision and pattern recognition`, `ieee cvf conference on computer vision` |
| ICCV | `international conference on computer vision`, `ieee cvf international conference on computer vision` |
| ECCV | `european conference on computer vision` |
| TPAMI | `ieee transactions on pattern analysis and machine intelligence`, `trans pattern anal mach intell`, `pami` |
| IJCV | `international journal of computer vision` |
| ICRA | `ieee international conference on robotics and automation`, `ieee conf robotics autom` |
| IROS | `ieee rsj international conference on intelligent robots and systems`, `intelligent robots and systems` |
| RSS | `robotics science and systems` |
| CoRL | `conference on robot learning`, `pmlr` (仅当论文标题/作者明确为 CoRL 论文时) |
| IJRR | `international journal of robotics research` |
| T-RO | `ieee transactions on robotics`, `ieee trans robot`, `trans robotics` |
| Science Robotics | `sci robot` |
| ACL | `annual meeting of the association for computational linguistics` |
| EMNLP | `empirical methods in natural language processing` |
| NAACL | `north american chapter of the association for computational linguistics` |
| TACL | `transactions of the association for computational linguistics` |
| COLING | `international conference on computational linguistics` |
| Findings of ACL/EMNLP/NAACL | `findings of the association for computational linguistics`, `findings of the acl`, `findings of emnlp`, `findings of naacl`, `findings` (当 venue 字段同时出现 `findings` 和 `acl/emnlp/naacl` 关键词时) |
| TMLR | `transactions on machine learning research` |
| KDD | `knowledge discovery and data mining`, `sigkdd` |
| WWW | `the web conference`, `world wide web conference`, `international world wide web conference` |
| TKDE | `ieee transactions on knowledge and data engineering`, `trans knowl data eng`, `tkde` |
| Nature | `nature` (需结合论文主题判断是否为 AI/ML/CS 相关) |
| Science | `science` (需结合论文主题判断是否为 AI/ML/CS 相关) |
| PNAS | `proceedings of the national academy of sciences`, `pnas` (需结合论文主题判断是否为 AI/ML/CS 相关) |

> **注意 CoRL 的特殊情况**：Google Scholar 上很多 CoRL 论文只显示出版社 `PMLR`。必须在论文标题/作者/年份与已知 CoRL 接收列表一致时，才将 `PMLR` 视为 CoRL。

## Normalization Rules

当进行 venue 匹配时，按以下顺序标准化：
1. Lowercase 全部字符
2. 移除标点、年份、卷号、页码
3. 移除前缀：`in`, `proceedings of`, `the`, `ieee`, `ieee rsj`, `ieee cvf`, `association for`, `empirical methods in`, `transactions of`, `journal of`, `international conference on`, `workshop on`, `conference on`
4. 对标准化后的字符串进行**子串包含匹配**（只要标准名的任意别名是标准化字符串的子串，即算命中）

## arXiv 论文处理规则

Google Scholar 上存在大量 arXiv 预印本论文，需按以下规则处理：

### 1. 同一论文去重原则

**同一篇论文无论出现多少次，仅计入一次，且优先使用正式 venue 版本。**

- 若 Scholar 列表中同时存在 **arXiv 版本** 和 **正式版本**（顶会/顶刊）：**以正式版本为准**，arXiv 版本不重复统计
- 若 Scholar 列表中**仅有 arXiv 版本**，无正式版本：按下文规则 2 处理

### 2. 低引用量 arXiv 论文（< 100 引用）

**直接过滤，不计入任何统计。**

理由：低引 arXiv 预印本尚未经过同行评审验证，质量参差不齐，不应作为学术影响力的证据。

> **例外**：对于明显属于 researcher 核心代表作、且后续被证实已接收为顶刊顶会的论文（如机构技术报告后续发 Nature/Science），**不受 100 引用阈值限制**，必须核验。

### 3. 高引用量 arXiv 论文（≥ 100 引用）且该学者为一作或二作

**需进一步判断是否被顶刊顶会接收：**

| 场景 | 处理方式 |
|------|----------|
| 同一 Scholar 列表中**已存在该论文的正式版本** | 以正式版本计入，arXiv 版本不重复统计 |
| Scholar 上**仅有 arXiv 预印本**，无正式版本，且**已确认被顶刊顶会接收** | **可计入**，使用 arXiv 版本的引用量，备注中注明「arXiv，已被 [顶刊顶会名] 接收」 |
| 无法确认是否被接收 | **不计入**，标记为 `arxiv_unclear` |

### 4. 操作步骤

对每篇高引 arXiv 论文：
1. 记录 arXiv 标题和引用数
2. **首先在同一 Scholar 列表中搜索是否存在同标题的正式版本**（会议/期刊版）—— 这是去重优先步骤
3. 若存在正式版本：以正式版本计入，arXiv 版本直接跳过
4. 若仅有 arXiv 版本：通过论文标题搜索 `accepted at [会议名]` 或 `published in [期刊名]` 确认接收情况
5. 确认被顶刊顶会接收的，计入「顶刊顶会&一二作引用量」并在备注标注接收 venue
