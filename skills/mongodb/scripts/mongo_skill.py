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
    CollectionProfile,
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

SECTOR_RANKINGS_PROFILE = CollectionProfile(
    skill_name="mongodb-sector-rankings-legacy",
    database="sourcing_system",
    collection="sector_rankings",
    allowed_ops=("find", "upsert"),
    allowed_fields=(
        "week_start",
        "sector",
        "company_name",
        "rank",
        "rationale",
        "source_signals",
    ),
    required_fields=("week_start", "sector", "company_name", "rank", "rationale"),
    unique_keys=("week_start", "sector", "rank"),
    default_sort=(("sector", 1), ("rank", 1)),
    default_limit=100,
)

IC_SESSIONS_PROFILE = CollectionProfile(
    skill_name="mongodb-ic-sessions-legacy",
    database="sourcing_system",
    collection="ic_sessions",
    allowed_ops=("find", "insert"),
    allowed_fields=("week_start", "status"),
    required_fields=("week_start",),
    unique_keys=("week_start",),
    default_sort=(("created_at", 1),),
    default_limit=20,
)

IC_VOTES_PROFILE = CollectionProfile(
    skill_name="mongodb-ic-votes-legacy",
    database="sourcing_system",
    collection="ic_votes",
    allowed_ops=("find", "insert"),
    allowed_fields=(
        "session_id",
        "company_id",
        "company_name",
        "role",
        "agent_name",
        "score",
        "argument",
        "verdict",
    ),
    required_fields=(
        "session_id",
        "company_name",
        "role",
        "score",
        "argument",
        "verdict",
    ),
    unique_keys=(),
    default_sort=(("created_at", 1),),
    default_limit=100,
)

WEEKLY_RANKINGS_PROFILE = CollectionProfile(
    skill_name="mongodb-weekly-rankings-legacy",
    database="sourcing_system",
    collection="weekly_rankings",
    allowed_ops=("find", "upsert"),
    allowed_fields=(
        "week_start",
        "company_id",
        "company_name",
        "final_rank",
        "final_score",
        "recommendation",
        "action_items",
    ),
    required_fields=(
        "week_start",
        "company_name",
        "final_rank",
        "final_score",
        "recommendation",
    ),
    unique_keys=("week_start", "company_name"),
    default_sort=(("final_rank", 1),),
    default_limit=100,
)

MANUAL_INPUTS_PROFILE = CollectionProfile(
    skill_name="mongodb-manual-inputs-legacy",
    database="sourcing_system",
    collection="manual_inputs",
    allowed_ops=("find", "insert"),
    allowed_fields=("input_type", "content", "created_by"),
    required_fields=("input_type", "content"),
    unique_keys=(),
    default_sort=(("created_at", -1),),
    default_limit=50,
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


def insert_sector_ranking(
    week_start: str,
    sector: str,
    company_name: str,
    rank: int,
    rationale: str,
    source_signals: List[str] = None,
) -> str:
    """Insert or update one sector ranking document."""
    return upsert_one(
        SECTOR_RANKINGS_PROFILE,
        {
            "week_start": week_start,
            "sector": sector,
            "company_name": company_name,
            "rank": rank,
            "rationale": rationale,
            "source_signals": source_signals or [],
        },
    )


def get_sector_rankings(week_start: str, sector: str = None) -> List[Dict[str, Any]]:
    """Get sector rankings, optionally narrowed to a single sector."""
    query: Dict[str, Any] = {"week_start": week_start}
    if sector:
        query["sector"] = sector
        return find_many(
            SECTOR_RANKINGS_PROFILE,
            query,
            sort=(("rank", 1),),
            limit=SECTOR_RANKINGS_PROFILE.default_limit,
        )
    return find_many(SECTOR_RANKINGS_PROFILE, query)


def create_ic_session(week_start: str) -> str:
    """Create a session if missing, otherwise return the existing id."""
    existing = find_one(IC_SESSIONS_PROFILE, {"week_start": week_start})
    if existing:
        return existing["id"]

    db = get_db(IC_SESSIONS_PROFILE.database)
    result = db[IC_SESSIONS_PROFILE.collection].insert_one(
        {
            "week_start": week_start,
            "status": "pending",
            "created_at": datetime.utcnow(),
        }
    )
    return str(result.inserted_id)


def insert_ic_vote(
    session_id: str,
    company_name: str,
    role: str,
    score: int,
    argument: str,
    verdict: str,
    agent_name: str = "unknown",
) -> str:
    """Insert one IC vote."""
    company = get_company_by_name(company_name)
    company_id = company.get("id") if company else None
    now = datetime.utcnow()

    db = get_db(IC_VOTES_PROFILE.database)
    result = db[IC_VOTES_PROFILE.collection].insert_one(
        {
            "session_id": session_id,
            "company_id": company_id,
            "company_name": company_name,
            "role": role,
            "agent_name": agent_name,
            "score": score,
            "argument": argument,
            "verdict": verdict,
            "created_at": now,
            "updated_at": now,
        }
    )
    return str(result.inserted_id)


def get_ic_votes(session_id: str, company_name: str = None) -> List[Dict[str, Any]]:
    """Get IC votes for a session and optional company."""
    query: Dict[str, Any] = {"session_id": session_id}
    if company_name:
        query["company_name"] = company_name
    return find_many(IC_VOTES_PROFILE, query)


def insert_weekly_ranking(
    week_start: str,
    company_name: str,
    final_rank: int,
    final_score: int,
    recommendation: str,
    action_items: List[str] = None,
) -> str:
    """Insert or update one weekly ranking document."""
    company = get_company_by_name(company_name)
    company_id = company.get("id") if company else None
    return upsert_one(
        WEEKLY_RANKINGS_PROFILE,
        {
            "week_start": week_start,
            "company_id": company_id,
            "company_name": company_name,
            "final_rank": final_rank,
            "final_score": final_score,
            "recommendation": recommendation,
            "action_items": action_items or [],
        },
    )


def get_weekly_rankings(week_start: str) -> List[Dict[str, Any]]:
    """Get weekly rankings sorted by final rank."""
    return find_many(
        WEEKLY_RANKINGS_PROFILE,
        {"week_start": week_start},
        sort=(("final_rank", 1),),
        limit=WEEKLY_RANKINGS_PROFILE.default_limit,
    )


def insert_manual_input(
    input_type: str,
    content: Dict[str, Any],
    created_by: str = "user",
) -> str:
    """Insert a manual input record."""
    now = datetime.utcnow()
    db = get_db(MANUAL_INPUTS_PROFILE.database)
    result = db[MANUAL_INPUTS_PROFILE.collection].insert_one(
        {
            "input_type": input_type,
            "content": content if isinstance(content, dict) else {"raw": content},
            "created_by": created_by,
            "created_at": now,
            "updated_at": now,
        }
    )
    return str(result.inserted_id)


def get_manual_inputs(input_type: str = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Get manual input records."""
    query: Dict[str, Any] = {}
    if input_type:
        query["input_type"] = input_type
    return find_many(MANUAL_INPUTS_PROFILE, query, limit=limit)


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
