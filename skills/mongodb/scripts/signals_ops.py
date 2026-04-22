"""
Signals collection operations.

Profile: profiles/signals.json
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from base_ops import count_documents, find_many, find_one, load_profile, upsert_one

_PROFILE = load_profile(_SCRIPT_DIR.parent / "profiles" / "signals.json")


def insert_signal(
    source_type: str,
    source_id: str,
    sector: str,
    title: str,
    summary: str = None,
    metadata: Dict[str, Any] = None,
    company_name: str = None,
) -> str:
    """Upsert a signal document (idempotent on source_type + source_id)."""
    return upsert_one(
        _PROFILE,
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


def find_signal(source_type: str, source_id: str) -> Optional[Dict[str, Any]]:
    """Find a single signal by source_type + source_id."""
    return find_one(_PROFILE, {"source_type": source_type, "source_id": source_id})


def get_signals_by_company(
    company_name: str,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Get recent signals for one company."""
    return find_many(_PROFILE, {"company_name": company_name}, limit=limit)


def get_signals_by_sector(
    sector: str,
    days: int = 30,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Get recent signals for one sector within the last N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    return find_many(
        _PROFILE,
        {"sector": sector, "created_at": {"$gte": cutoff}},
        limit=limit,
    )


def count_signals(sector: str = None, days: int = None) -> int:
    """Count signals with optional sector and date filters."""
    query: Dict[str, Any] = {}
    if sector:
        query["sector"] = sector
    if days:
        query["created_at"] = {"$gte": datetime.utcnow() - timedelta(days=days)}
    return count_documents(_PROFILE, query)
