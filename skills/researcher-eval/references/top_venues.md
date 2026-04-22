# Top-Tier Venues for 顶刊顶会&一二作引用量 Calculation

A paper counts toward **顶刊顶会&一二作引用量** only if it meets **both** criteria:
1. Published in one of the venues below (or a clear sub-journal thereof).
2. The target scholar is **first or second author**.

## Machine Learning

- NeurIPS (Neural Information Processing Systems)
- ICML (International Conference on Machine Learning)
- ICLR (International Conference on Learning Representations)
- JMLR (Journal of Machine Learning Research)

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

> **Important**: 以上 venue 列表覆盖 AI、ML、CV、Robotics、NLP 五大领域。被计入「顶刊顶会&一二作引用量」仅代表论文发表在上述顶刊顶会上，不代表其研究方向一定与创业路线**直接相关**——相关性需根据论文标题单独判断。例如：一篇 NeurIPS 纯理论优化论文可以计入「顶刊顶会&一二作引用量」，但在 relevance 分析中可能被评为 "中等相关" 或 "低相关"。

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

> **注意 CoRL 的特殊情况**：Google Scholar 上很多 CoRL 论文只显示出版社 `PMLR`。必须在论文标题/作者/年份与已知 CoRL 接收列表一致时，才将 `PMLR` 视为 CoRL。

## Normalization Rules

当进行 venue 匹配时，按以下顺序标准化：
1. Lowercase 全部字符
2. 移除标点、年份、卷号、页码
3. 移除前缀：`in`, `proceedings of`, `the`, `ieee`, `ieee rsj`, `ieee cvf`, `association for`, `empirical methods in`, `transactions of`, `journal of`, `international conference on`, `workshop on`, `conference on`
4. 对标准化后的字符串进行**子串包含匹配**（只要标准名的任意别名是标准化字符串的子串，即算命中）

## arXiv 论文处理规则

Google Scholar 上存在大量 arXiv 预印本论文，需按以下规则处理：

### 1. 低引用量 arXiv 论文（< 100 引用）

**直接过滤，不计入任何统计。**

理由：低引 arXiv 预印本尚未经过同行评审验证，质量参差不齐，不应作为学术影响力的证据。

### 2. 高引用量 arXiv 论文（≥ 100 引用）且该学者为一作或二作

**需进一步判断是否被顶刊顶会接收：**

| 场景 | 处理方式 |
|------|----------|
| Google Scholar 上**已有正式版本**（显示为上述顶刊顶会之一） | **不计入**——正式版本已在对应顶会/顶刊中统计，避免重复计算 |
| Google Scholar 上**仅有 arXiv 预印本**，无正式版本 | **可计入**，但需在备注中注明「arXiv，已被 [顶刊顶会名] 接收」 |
| 无法确认是否被接收 | **不计入**，标记为 `arxiv_unclear` |

### 3. 操作步骤

对每篇高引 arXiv 论文：
1. 记录 arXiv 标题和引用数
2. 在同一 Scholar 列表中搜索是否存在**同标题的正式版本**（会议/期刊版）
3. 若存在正式版本：跳过，不重复计入
4. 若仅有 arXiv：通过论文标题搜索 `accepted at [会议名]` 或 `published in [期刊名]` 确认接收情况
5. 确认被顶刊顶会接收的，计入「顶刊顶会&一二作引用量」并在备注标注接收 venue
