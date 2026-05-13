"""
merge_readtheone.py
Standard merge script for stage0 outputs from multiple readtheone sources.
Reads multiple CSV files, deduplicates by company_name (case-insensitive),
merges source column, and outputs companies.csv.
"""
import csv
import sys
from pathlib import Path

OUTPUT_FILE = Path("companies.csv")
FIELDNAMES = ["company_name", "rank", "score", "reason", "source", "track", "tags"]


def merge_csvs(csv_paths):
    dedup = {}
    for p in csv_paths:
        with open(p, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                name = row.get("company_name", "").strip() or row.get("name", "").strip()
                if not name:
                    continue
                key = name.lower()
                if key not in dedup:
                    dedup[key] = {k: row.get(k, "").strip() for k in FIELDNAMES}
                    dedup[key]["company_name"] = name
                else:
                    # Merge source field
                    existing_src = dedup[key].get("source", "")
                    new_src = row.get("source", "").strip()
                    sources = {s.strip() for s in existing_src.split("|") if s.strip()}
                    if new_src:
                        sources.add(new_src)
                    dedup[key]["source"] = "|".join(sorted(sources))
    return list(dedup.values())


def main():
    csv_files = [Path(p) for p in sys.argv[1:]]
    if not csv_files:
        # Default: grab all CSVs in current directory
        csv_files = sorted(Path(".").glob("*.csv"))
        csv_files = [p for p in csv_files if p.name != OUTPUT_FILE.name]

    if not csv_files:
        print("No input CSV files found.", file=sys.stderr)
        sys.exit(1)

    records = merge_csvs(csv_files)

    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(records)

    print(f"Merged {len(records)} unique companies from {len(csv_files)} file(s) into {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
