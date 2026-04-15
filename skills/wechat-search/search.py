#!/usr/bin/env python3
"""WeChat Public Account Articles Search via JZL/dajiala API"""

import argparse
import http.client
import json
import sys


class WeChatSearch:
    def __init__(self):
        self.api_key = "JZL9145b9c50fc2d48f"
        self.base_url = "www.dajiala.com"
        self.endpoint = "/fbmain/monitor/v3/kw_search"

    def _search(self, kw="", any_kw="", ex_kw="", period=7, page=1):
        """Single page search"""
        conn = http.client.HTTPSConnection(self.base_url)

        payload = {
            "sort_type": 1,
            "mode": 3,
            "period": period,
            "page": page,
            "key": self.api_key,
            "kw": kw,
            "any_kw": any_kw,
            "ex_kw": ex_kw,
            "verifycode": "",
        }

        headers = {"Content-Type": "application/json"}
        conn.request("POST", self.endpoint, json.dumps(payload), headers)

        res = conn.getresponse()
        data = json.loads(res.read().decode("utf-8"))

        if data.get("data"):
            for article in data["data"]:
                article["search_kw"] = kw
                article["search_any_kw"] = any_kw
                article["search_ex_kw"] = ex_kw
            return data["data"]
        return None

    def search(self, kw="", any_kw="", ex_kw="", period=7, pages=1):
        """Multi-page search"""
        results = []
        for page in range(1, pages + 1):
            data = self._search(kw, any_kw, ex_kw, period, page)
            if not data:
                break
            results.extend(data)
        return results

    def format_article(self, article):
        """Format article for display"""
        title = article.get("title", "N/A")
        author = article.get("author", "N/A")
        url = article.get("url", "")
        pub_time = article.get("pub_time", "")
        read_count = article.get("read_count", "N/A")

        return f"""📝 {title}
   作者: {author} | 阅读: {read_count}
   时间: {pub_time}
   链接: {url}"""


def main():
    parser = argparse.ArgumentParser(description="Search WeChat public account articles")
    parser.add_argument("--kw", default="", help="Exact keyword (must appear)")
    parser.add_argument("--any", default="", help="Any keyword match (OR logic)")
    parser.add_argument("--ex", default="", help="Exclude keywords")
    parser.add_argument("--period", type=int, default=7, help="Time range in days")
    parser.add_argument("--pages", type=int, default=1, help="Number of pages")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not args.kw and not args.any:
        print("Error: Must specify --kw or --any", file=sys.stderr)
        sys.exit(1)

    searcher = WeChatSearch()
    results = searcher.search(
        kw=args.kw,
        any_kw=args.any,
        ex_kw=args.ex,
        period=args.period,
        pages=args.pages
    )

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        if not results:
            print("No results found")
        else:
            print(f"Found {len(results)} articles:\n")
            for article in results:
                print(searcher.format_article(article))
                print("-" * 50)


if __name__ == "__main__":
    main()
