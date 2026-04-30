# researcher-eval

技术人员学术尽调评估 Skill - 用于评估研究员、工程师、学者的学术影响力和工程能力。

## 适用领域

AI、具身智能、机器人、计算机视觉、NLP、强化学习等各技术领域。

## 依赖

使用本 Skill 前必须先安装浏览器自动化工具：

```bash
# 方式一：agent-browser（推荐）
npx skills add https://github.com/vercel-labs/agent-browser --skill agent-browser

# 方式二：browser-use
pip install browser-use
```

**注意**：如果你使用的是 agent-browser 以外的工具，请在使用 Skill 前明确告知 agent 你安装的是什么工具。

## 安装

```bash
npx skills add https://github.com/YOUR_USERNAME/researcher-eval-skill --skill researcher-eval
```

## 使用方法

触发词包括：
- "评估某某的技术能力"
- "调研某某的学术背景"
- "分析某某的论文和 GitHub"
- "做技术尽调"
- "查某某的引用量"
- "分析某某的开源贡献"
- "分析某某的核心成果"

## 数据采集方式

**所有数据必须通过浏览器自动化工具（例如Agent-browser）实时爬取：**

### Google Scholar
- 学术引用量、h-index、i10-index
- 按引用排序的论文列表
- 每篇论文的作者位置、会议/期刊、引用数

### GitHub
- 个人主页：Followers、贡献记录
- 项目页面：Stars、Forks、Contributors 排名
- 同类项目对比数据

### 个人主页/实验室网站
- 教育背景：本科、硕士、博士院校和专业
- 工作经历：职位、导师、研究组
- 重要 title 和成就

## License

MIT
