"""
build_query.py
Run after stage0 (companies.csv generated) and before stage1 (search).
Outputs keywords.json with search queries per company.

Strategy:统一生成默认 query `{company_name} AI {search_target}`。
通用名的精细消歧由 agent 在执行阶段根据搜索结果，从 reason 提取英文关键词 override，
不再在脚本层做 is_generic 判断或 track 翻译。
"""
import csv
import json
from pathlib import Path

INPUT_FILE = Path("companies.csv")
OUTPUT_FILE = Path("keywords.json")


def build_query(name: str, target: str) -> str:
    """Construct default search query."""
    return f"{name} AI {target}"


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"{INPUT_FILE} not found. Run stage0 first.")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        companies = list(csv.DictReader(f))

    queries = {}
    for c in companies:
        name = c.get("company_name", "").strip() or c.get("name", "").strip()
        if not name:
            continue
        queries[name] = {
            "founder": build_query(name, "founder"),
            "funding": build_query(name, "funding"),
        }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(queries, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(queries)} query sets to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
