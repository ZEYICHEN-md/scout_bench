# team-academic-comp

学术引用投资 Brief 生成 Skill - 为创业公司创始人生成投资级别的学术引用分析 Brief。

## 适用场景

- 对比不同创始团队的学术影响力/引用量
- 爬取 Google Scholar 资料并生成投资 Brief
- 评估团队研究背景与创业路线的匹配度
- 生成包含引用量、顶刊顶会一二作引用、研究方向相关性、年龄推断的结构化报告
- 对机器人、AI、深度学习创业团队进行公开论文数据的尽调分析

## 依赖

使用本 Skill 前必须先安装浏览器自动化工具：

```bash
npx skills add https://github.com/vercel-labs/agent-browser --skill agent-browser
```

## 安装

```bash
npx skills add https://github.com/YOUR_USERNAME/team-academic-comp-skill --skill team-academic-comp
```

## 使用方法

触发词包括：
- "Google Scholar"
- "论文引用"
- "学术对比"
- "投资 Brief"
- "创始人学术"
- 提供研究人员/公司列表进行尽调

## 数据采集方式

**所有数据必须通过浏览器自动化工具实时爬取：**

### Google Scholar
- 侧边栏 totals（All time / Since 2021）
- 完整论文列表（反复点击 SHOW MORE 加载，约200篇时停止）
- 每篇论文的标题、作者、会议/期刊、年份、引用数

### 数据处理
- JSONL 存档：`{company}_{name}_papers.jsonl`
- Venue 判定：按 `references/top_venues.md` 的 Normalization Rules 和 aliases 判定
- 核心指标：顶刊顶会 & 一二作引用量

## License

MIT
