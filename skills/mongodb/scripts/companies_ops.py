"""
Companies collection operations.

Profile: profiles/companies.json
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from base_ops import count_documents, find_many, load_profile, update_one, upsert_one

_PROFILE = load_profile(_SCRIPT_DIR.parent / "profiles" / "companies.json")


def insert_company(
    name: str,
    sector: str,
    direction: str = "AI",
    author: str = "Bin",
    description: str = None,
    metadata: Dict[str, Any] = None,
) -> str:
    """Upsert a company document (idempotent on name + sector)."""
    return upsert_one(
        _PROFILE,
        {
            "name": name,
            "sector": sector,
            "direction": direction,
            "author": author,
            "description": description,
            "metadata": metadata or {},
        },
    )


def get_company_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Find the most recently updated company document by name."""
    results = find_many(_PROFILE, {"name": name}, limit=1)
    return results[0] if results else None


def get_all_companies(
    sector: str = None,
    status: str = None,
) -> List[Dict[str, Any]]:
    """List companies with optional sector and status filters."""
    query: Dict[str, Any] = {}
    if sector:
        query["sector"] = sector
    if status:
        query["status"] = status
    return find_many(_PROFILE, query)


def update_company_status(name: str, status: str) -> bool:
    """Update company status by name."""
    doc = update_one(_PROFILE, {"name": name}, {"status": status})
    return doc is not None


def count_companies(sector: str = None) -> int:
    """Count companies with an optional sector filter."""
    query = {"sector": sector} if sector else {}
    return count_documents(_PROFILE, query)
