"""
WeChat articles collection operations (read-only).

Profile  : profiles/wechat_articles.json
Database : db1
Collection: wechat.articles

Schema note
-----------
The source system stores articles with a hex-string `_id` field remapped to
`source_id`.  Pass the original `_id` value as the `source_id` argument.

Individual extraction structure
--------------------------------
Each article may carry an `individuals` list.  Every entry looks like:
{
    "entrepreneur_name": str,
    "technical_field": str,
    "former_company": str,
    "former_position": str,
    "current_company": str,
    "current_position": str,
    "is_chinese": bool,
    "is_startup": bool,
    "is_startup_reason": str,
    "is_chinese_reason": str,
    "is_validate_name": bool,
    "is_validate_name_reason": str,
    "is_recent_resignation": bool,
    "is_recent_resignation_reason": str,
    "has_funding": bool,
    "is_tech_domain": bool,
    "is_strong_sign": bool,
    "has_big_company_experience": bool,
}
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from base_ops import count_documents, find_many, find_one, load_profile

_PROFILE = load_profile(_SCRIPT_DIR.parent / "profiles" / "wechat_articles.json")


def get_article(source_id: str) -> Optional[Dict[str, Any]]:
    """Find a single article by its source_id."""
    return find_one(_PROFILE, {"source_id": source_id})


def get_articles_by_wx_name(
    wx_name: str,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Get recent articles from a specific WeChat account."""
    return find_many(_PROFILE, {"wx_name": wx_name}, limit=limit)


def get_articles_by_batch(
    batch: str,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """Get all articles belonging to a batch (YYYY-MM-DD)."""
    return find_many(_PROFILE, {"batch": batch}, limit=limit)


def get_articles_with_individuals(
    batch: str = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Get articles that have at least one extracted individual record."""
    query: Dict[str, Any] = {"individuals": {"$exists": True, "$ne": []}}
    if batch:
        query["batch"] = batch
    return find_many(_PROFILE, query, limit=limit)


def count_articles(
    wx_name: str = None,
    batch: str = None,
) -> int:
    """Count articles with optional wx_name and batch filters."""
    query: Dict[str, Any] = {}
    if wx_name:
        query["wx_name"] = wx_name
    if batch:
        query["batch"] = batch
    return count_documents(_PROFILE, query)
