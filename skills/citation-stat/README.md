# citation-stat

学者引用量统计 Skill - 用于统计学者 Google Scholar 引用量数据，生成论文分类表格和多人对比表格。

## 适用场景

- 查询学者引用量、统计论文引用
- 获取 Google Scholar 数据
- 做学术引用量对比
- 生成学者论文分类表

## 依赖

使用本 Skill 前必须先安装浏览器自动化工具：

```bash
npx skills add https://github.com/vercel-labs/agent-browser --skill agent-browser
```

## 安装

```bash
npx skills add https://github.com/YOUR_USERNAME/citation-stat-skill --skill citation-stat
```

## 使用方法

触发词包括：
- "查引用量"
- "统计引用"
- "Google Scholar 数据"
- "学者引用对比"
- "论文分类表格"
- "引用量统计"
- "citation stats"
- "学者 h-index"

## 数据采集方式

**所有数据必须通过浏览器自动化工具实时爬取：**

### Google Scholar
- 总引用量、h-index、论文总数
- 按引用排序的完整论文列表（反复点击 SHOW MORE 加载全部）
- 每篇论文的标题、作者列表、作者位置、会议/期刊、年份、引用数

### 数据处理
- 两步 JSONL 存档：`{name}_papers_raw.jsonl` → `{name}_papers_classified.jsonl`
- Venue 判定：按 `references/top_venues.md` 的 Normalization Rules 和 aliases 判定
- 引用量统计：仅对 A 类论文（一二作 + 顶刊顶会）求和

## License

MIT
