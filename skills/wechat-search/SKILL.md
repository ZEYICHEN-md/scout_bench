# WeChat Public Account Articles Search

Search WeChat public account articles via JZL/dajiala API.

## Triggers
Use when user asks to:
- Search WeChat articles / posts / content
- Find WeChat public account articles
- Search 微信文章 / 微信搜索 / 微信公众号
- Query WeChat for news, analysis, or posts
- "搜一下微信" / "search WeChat" / "找微信文章"

## Usage

```bash
# Basic search (any keyword match)
uv run ~/.openclaw/skills/wechat-search/search.py --any "高榕资本 高榕创投" --period 7

# Exact keyword search
uv run ~/.openclaw/skills/wechat-search/search.py --kw "高榕资本" --period 7

# Exclude keywords
uv run ~/.openclaw/skills/wechat-search/search.py --any "高榕资本" --ex "广告" --period 7

# Multiple pages
uv run ~/.openclaw/skills/wechat-search/search.py --any "高榕资本" --period 7 --pages 3

# JSON output (for programmatic use)
uv run ~/.openclaw/skills/wechat-search/search.py --any "高榕资本" --period 7 --json
```

## Parameters

- `--kw`: Exact keyword (must appear in title/content, AND logic)
- `--any`: Any keyword match (space-separated, OR logic)
- `--ex`: Exclude keywords (space-separated, OR logic)
- `--period`: Time range in days (default: 1)
- `--pages`: Number of pages to fetch (default: 1)
- `--json`: Output as JSON (default: true)

## API Notes

Uses JZL/dajiala.com API with built-in key. Rate limits may apply.
