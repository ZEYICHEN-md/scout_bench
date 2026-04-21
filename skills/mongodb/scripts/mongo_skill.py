"""
MongoDB skill runtime.

This single skill uses internal collection profiles so we keep one install
surface while still separating collection-specific behavior in code.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from base_ops import (
    count_documents,
    find_many,
    find_one,
    load_profile,
    update_one,
    upsert_one,
)
from client import MONGODB_AVAILABLE, get_db

SIGNALS_PROFILE = load_profile(
    Path(__file__).resolve().parents[1] / "profiles" / "signals.json"
)
COMPANIES_PROFILE = load_profile(
    Path(__file__).resolve().parents[1] / "profiles" / "companies.json"
)


def insert_signal(
    source_type: str,
    source_id: str,
    sector: str,
    title: str,
    summary: str = None,
    metadata: Dict[str, Any] = None,
    company_name: str = None,
) -> str:
    """Compatibility wrapper for signal upsert."""
    return upsert_one(
        SIGNALS_PROFILE,
        {
            "source_type": source_type,
            "source_id": source_id,
            "company_name": company_name,
            "sector": sector,
            "title": title,
            "summary": summary,
            "metadata": metadata or {},
        },
    )


def get_signals_by_company(company_name: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent signals for one company."""
    return find_many(SIGNALS_PROFILE, {"company_name": company_name}, limit=limit)


def get_signals_by_sector(
    sector: str,
    days: int = 30,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Get recent signals for one sector."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    return find_many(
        SIGNALS_PROFILE,
        {"sector": sector, "created_at": {"$gte": cutoff}},
        limit=limit,
    )


def find_signal(source_type: str, source_id: str) -> Optional[Dict[str, Any]]:
    """Find a single signal by source_type + source_id."""
    return find_one(
        SIGNALS_PROFILE,
        {"source_type": source_type, "source_id": source_id},
    )


def insert_company(
    name: str,
    sector: str,
    description: str = None,
    metadata: Dict[str, Any] = None,
) -> str:
    """Compatibility wrapper for company upsert."""
    return upsert_one(
        COMPANIES_PROFILE,
        {
            "name": name,
            "sector": sector,
            "description": description,
            "metadata": metadata or {},
        },
    )


def get_company_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Find the most recently updated company document by name."""
    results = find_many(COMPANIES_PROFILE, {"name": name}, limit=1)
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
    return find_many(COMPANIES_PROFILE, query)


def update_company_status(name: str, status: str) -> bool:
    """Update company status by name across matching sector variants."""
    doc = update_one(COMPANIES_PROFILE, {"name": name}, {"status": status})
    return doc is not None


def count_signals(sector: str = None, days: int = None) -> int:
    """Count signals with optional filters."""
    query: Dict[str, Any] = {}
    if sector:
        query["sector"] = sector
    if days:
        query["created_at"] = {"$gte": datetime.utcnow() - timedelta(days=days)}
    return count_documents(SIGNALS_PROFILE, query)


def count_companies(sector: str = None) -> int:
    """Count companies with an optional sector filter."""
    query = {"sector": sector} if sector else {}
    return count_documents(COMPANIES_PROFILE, query)


if __name__ == "__main__":
    print("MongoDB skill test")
    print(f"pymongo available: {MONGODB_AVAILABLE}")

    try:
        db = get_db("sourcing_system")
        print(f"connected database: {db.name}")
        print(f"collections: {db.list_collection_names()}")
        print()
        print(f"signal count: {count_signals()}")
        print(f"company count: {count_companies()}")
    except Exception as exc:
        print(f"connection failed: {exc}")
