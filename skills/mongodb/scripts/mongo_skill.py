"""
MongoDB skill runtime — thin re-export layer.

Each collection lives in its own <name>_ops.py module under scripts/.
To add a new collection:
  1. Add profiles/<name>.json          ← schema, allowed_ops, unique_keys …
  2. Add scripts/<name>_ops.py         ← collection-specific functions
  3. Re-export the public API below    ← one import block + __all__ entries
  4. Update SKILL.md                   ← document the new functions
"""

import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from client import MONGODB_AVAILABLE, get_db

# ── signals ───────────────────────────────────────────────────────────────────
from signals_ops import (
    count_signals,
    find_signal,
    get_signals_by_company,
    get_signals_by_sector,
    insert_signal,
)

# ── companies ─────────────────────────────────────────────────────────────────
from companies_ops import (
    count_companies,
    get_all_companies,
    get_company_by_name,
    insert_company,
    update_company_status,
)

# ── add new collections above this line ───────────────────────────────────────

__all__ = [
    # signals
    "insert_signal",
    "find_signal",
    "get_signals_by_company",
    "get_signals_by_sector",
    "count_signals",
    # companies
    "insert_company",
    "get_company_by_name",
    "get_all_companies",
    "update_company_status",
    "count_companies",
]


if __name__ == "__main__":
    print("MongoDB skill test")
    print(f"pymongo available: {MONGODB_AVAILABLE}")

    try:
        db = get_db("sourcing_system")
        print(f"connected database: {db.name}")
        print(f"collections: {db.list_collection_names()}")
        print()
        print(f"signal count:  {count_signals()}")
        print(f"company count: {count_companies()}")
    except Exception as exc:
        print(f"connection failed: {exc}")
