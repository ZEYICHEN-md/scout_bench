"""
screening_db.py
阶段1华人创始人筛查的 SQLite checkpoint 管理。
替代手工追加 CSV，避免编码、格式、并发写入问题。
"""
import argparse
import csv
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_DB = Path("screening.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS screening (
    company TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'PENDING',
    source TEXT,
    score REAL,
    track TEXT,
    reason TEXT,
    founder_name TEXT,
    founder_verification_layer TEXT DEFAULT 'not_attempted',
    company_type TEXT,
    verified_website TEXT,
    website_verification_status TEXT DEFAULT 'not_attempted',
    evidence_quote TEXT,
    evidence_url TEXT,
    error TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_status ON screening(status);
CREATE INDEX IF NOT EXISTS idx_source ON screening(source);
"""


def get_conn(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path) -> None:
    conn = get_conn(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"Initialized {db_path}")


def upsert(
    db_path: Path,
    company: str,
    status: str = None,
    source: str = None,
    score: float = None,
    track: str = None,
    reason: str = None,
    founder_name: str = None,
    founder_verification_layer: str = None,
    company_type: str = None,
    verified_website: str = None,
    website_verification_status: str = None,
    evidence_quote: str = None,
    evidence_url: str = None,
    error: str = None,
) -> None:
    conn = get_conn(db_path)
    # 先查是否存在，存在则只更新传入的非 None 字段
    row = conn.execute(
        "SELECT * FROM screening WHERE company = ?", (company,)
    ).fetchone()

    fields = {
        "status": status,
        "source": source,
        "score": score,
        "track": track,
        "reason": reason,
        "founder_name": founder_name,
        "founder_verification_layer": founder_verification_layer,
        "company_type": company_type,
        "verified_website": verified_website,
        "website_verification_status": website_verification_status,
        "evidence_quote": evidence_quote,
        "evidence_url": evidence_url,
        "error": error,
        "updated_at": datetime.now().isoformat(),
    }

    if row is None:
        # INSERT
        cols = ["company"] + [k for k, v in fields.items() if v is not None]
        vals = [company] + [v for v in fields.values() if v is not None]
        placeholders = ", ".join(["?"] * len(cols))
        sql = f"INSERT INTO screening ({', '.join(cols)}) VALUES ({placeholders})"
        conn.execute(sql, vals)
    else:
        # UPDATE only provided fields
        updates = {k: v for k, v in fields.items() if v is not None}
        if updates:
            set_clause = ", ".join([f"{k} = ?" for k in updates])
            sql = f"UPDATE screening SET {set_clause} WHERE company = ?"
            conn.execute(sql, list(updates.values()) + [company])

    conn.commit()
    conn.close()
    print(f"Upserted {company}")


def list_rows(db_path: Path, status: str = None, source: str = None) -> None:
    conn = get_conn(db_path)
    conditions = []
    params = []
    if status:
        conditions.append("status = ?")
        params.append(status)
    if source:
        conditions.append("source = ?")
        params.append(source)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    sql = f"SELECT * FROM screening {where} ORDER BY updated_at DESC"

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    if not rows:
        print("No records found.")
        return

    headers = rows[0].keys()
    writer = csv.DictWriter(sys.stdout, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(dict(row))


def export_csv(db_path: Path, output: Path) -> None:
    conn = get_conn(db_path)
    rows = conn.execute("SELECT * FROM screening ORDER BY score DESC, company").fetchall()
    conn.close()

    if not rows:
        print("No records to export.")
        return

    with open(output, "w", newline="", encoding="utf-8-sig") as f:
        headers = rows[0].keys()
        writer = csv.DictWriter(f, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))
    print(f"Exported {len(rows)} rows to {output}")


def import_companies(db_path: Path, csv_path: Path) -> None:
    """从阶段0的 companies.csv 导入初始数据，status 默认 PENDING。"""
    conn = get_conn(db_path)
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            company = row.get("company_name", "").strip()
            if not company:
                continue
            note = row.get("note", "").strip()
            status = "SKIP_PUBLIC_HYPE" if note == "SKIP_PUBLIC_HYPE" else "PENDING"
            conn.execute(
                """
                INSERT OR IGNORE INTO screening
                (company, source, score, track, reason, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    company,
                    row.get("source", ""),
                    row.get("score", None),
                    row.get("track", ""),
                    row.get("reason", ""),
                    status,
                ),
            )
    conn.commit()
    conn.close()
    print(f"Imported companies from {csv_path}")


def main():
    parser = argparse.ArgumentParser(description="Screening checkpoint SQLite manager")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to SQLite db")
    sub = parser.add_subparsers(dest="cmd")

    p_init = sub.add_parser("init", help="Initialize database")

    p_import = sub.add_parser("import", help="Import companies.csv into db")
    p_import.add_argument("csv", type=Path, help="Path to companies.csv")

    p_upsert = sub.add_parser("upsert", help="Upsert a company record")
    p_upsert.add_argument("--company", required=True)
    p_upsert.add_argument("--status")
    p_upsert.add_argument("--source")
    p_upsert.add_argument("--score", type=float)
    p_upsert.add_argument("--track")
    p_upsert.add_argument("--reason")
    p_upsert.add_argument("--founder_name")
    p_upsert.add_argument("--founder_verification_layer")
    p_upsert.add_argument("--company_type")
    p_upsert.add_argument("--verified_website")
    p_upsert.add_argument("--website_verification_status")
    p_upsert.add_argument("--evidence_quote")
    p_upsert.add_argument("--evidence_url")
    p_upsert.add_argument("--error")

    p_list = sub.add_parser("list", help="List records")
    p_list.add_argument("--status")
    p_list.add_argument("--source")

    p_export = sub.add_parser("export", help="Export to CSV")
    p_export.add_argument("--output", type=Path, default=Path("checkpoint_export.csv"))

    args = parser.parse_args()

    if args.cmd == "init":
        init_db(args.db)
    elif args.cmd == "import":
        init_db(args.db)
        import_companies(args.db, args.csv)
    elif args.cmd == "upsert":
        upsert(
            args.db,
            company=args.company,
            status=args.status,
            source=args.source,
            score=args.score,
            track=args.track,
            reason=args.reason,
            founder_name=args.founder_name,
            founder_verification_layer=args.founder_verification_layer,
            company_type=args.company_type,
            verified_website=args.verified_website,
            website_verification_status=args.website_verification_status,
            evidence_quote=args.evidence_quote,
            evidence_url=args.evidence_url,
            error=args.error,
        )
    elif args.cmd == "list":
        list_rows(args.db, status=args.status, source=args.source)
    elif args.cmd == "export":
        export_csv(args.db, args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
