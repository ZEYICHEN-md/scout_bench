# social-media-analysis

Twitter/X 数据爬取与情感分析 Skill。

## 功能

- 使用 Apify `kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest` Actor 爬取推文
- 支持自然语言输入和 Twitter 高级搜索语法自动解析
- 自动过滤 Mock 数据
- 并发调用 DeepSeek API 进行三分类情感分析（positive / negative / neutral）
- 识别反讽、欲扬先抑、欲抑先扬、英文社媒俚语等复杂表达
- 输出结构化统计报告与 Markdown 文档

## 测试

- 输入解析测试：7/7 通过
- 情感分析准确性测试：10/10 通过（100%）
- 端到端全流程测试：通过
