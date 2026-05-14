"""
Profile-aware MongoDB CRUD helpers for the mongodb skill.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from client import get_collection, serialize_doc


@dataclass(frozen=True)
class CollectionProfile:
    """Runtime profile for a single collection."""

    skill_name: str
    database: str
    collection: str
    allowed_ops: Tuple[str, ...]
    allowed_fields: Tuple[str, ...]
    required_fields: Tuple[str, ...]
    unique_keys: Tuple[str, ...]
    default_sort: Tuple[Tuple[str, int], ...]
    default_limit: int = 50


def _to_tuple(values: Optional[Iterable[str]]) -> Tuple[str, ...]:
    if not values:
        return ()
    return tuple(values)


def _normalize_sort(
    values: Optional[Sequence[Sequence[Any]]],
) -> Tuple[Tuple[str, int], ...]:
    if not values:
        return (("created_at", -1),)

    normalized: List[Tuple[str, int]] = []
    for item in values:
        if len(item) != 2:
            raise ValueError(f"Invalid sort entry: {item!r}")
        field, direction = item
        normalized.append((str(field), int(direction)))
    return tuple(normalized)


def load_profile(path: Path) -> CollectionProfile:
    """Load a collection profile from JSON."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return CollectionProfile(
        skill_name=raw["skill_name"],
        database=raw["database"],
        collection=raw["collection"],
        allowed_ops=_to_tuple(raw.get("allowed_ops")),
        allowed_fields=_to_tuple(raw.get("allowed_fields")),
        required_fields=_to_tuple(raw.get("required_fields")),
        unique_keys=_to_tuple(raw.get("unique_keys")),
        default_sort=_normalize_sort(raw.get("default_sort")),
        default_limit=int(raw.get("default_limit", 50)),
    )


def assert_operation_allowed(profile: CollectionProfile, operation: str) -> None:
    """Ensure the profile explicitly allows an operation."""
    if operation not in profile.allowed_ops:
        raise ValueError(
            f"Operation '{operation}' is not allowed for profile '{profile.skill_name}'."
        )


def filter_payload(profile: CollectionProfile, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Remove keys that are not explicitly exposed by the profile."""
    return {
        key: value
        for key, value in payload.items()
        if key in profile.allowed_fields and value is not None
    }


def validate_required_fields(
    profile: CollectionProfile,
    payload: Dict[str, Any],
    *,
    fields: Sequence[str],
) -> None:
    """Verify that required keys are present and non-empty."""
    missing = [field for field in fields if payload.get(field) in (None, "")]
    if missing:
        raise ValueError(
            f"Missing required fields for '{profile.skill_name}': {', '.join(missing)}"
        )


def get_collection_handle(profile: CollectionProfile):
    """Resolve the underlying collection from a profile."""
    return get_collection(profile.database, profile.collection)


def insert_one(profile: CollectionProfile, payload: Dict[str, Any]) -> str:
    """Insert a single document after validating the payload."""
    assert_operation_allowed(profile, "insert")
    document = filter_payload(profile, payload)
    validate_required_fields(profile, document, fields=profile.required_fields)

    now = datetime.utcnow()
    document.setdefault("created_at", now)
    document["updated_at"] = now

    result = get_collection_handle(profile).insert_one(document)
    return str(result.inserted_id)


def upsert_one(profile: CollectionProfile, payload: Dict[str, Any]) -> str:
    """Upsert a document using the profile's unique keys."""
    assert_operation_allowed(profile, "upsert")
    document = filter_payload(profile, payload)
    validate_required_fields(profile, document, fields=profile.required_fields)
    validate_required_fields(profile, document, fields=profile.unique_keys)

    selector = {field: document[field] for field in profile.unique_keys}
    now = datetime.utcnow()
    result = get_collection_handle(profile).update_one(
        selector,
        {
            "$set": {
                **document,
                "updated_at": now,
            },
            "$setOnInsert": {
                "created_at": now,
            },
        },
        upsert=True,
    )

    if result.upserted_id:
        return str(result.upserted_id)

    existing = get_collection_handle(profile).find_one(selector)
    if existing is None:
        return ""
    return str(existing["_id"])


def find_one(
    profile: CollectionProfile,
    filters: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Return a single serialized document."""
    assert_operation_allowed(profile, "find")
    return serialize_doc(get_collection_handle(profile).find_one(filters))


def find_many(
    profile: CollectionProfile,
    filters: Optional[Dict[str, Any]] = None,
    *,
    limit: Optional[int] = None,
    sort: Optional[Sequence[Sequence[Any]]] = None,
) -> List[Dict[str, Any]]:
    """Return serialized documents using profile defaults when omitted."""
    assert_operation_allowed(profile, "find")
    resolved_limit = profile.default_limit if limit is None else int(limit)
    resolved_sort = _normalize_sort(sort) if sort else profile.default_sort
    cursor = (
        get_collection_handle(profile)
        .find(filters or {})
        .sort(list(resolved_sort))
        .limit(resolved_limit)
    )
    return [serialize_doc(doc) for doc in cursor]


def update_one(
    profile: CollectionProfile,
    filters: Dict[str, Any],
    payload: Dict[str, Any],
    *,
    upsert: bool = False,
) -> Optional[Dict[str, Any]]:
    """Update a single document and return the stored document."""
    assert_operation_allowed(profile, "update")
    document = filter_payload(profile, payload)
    if not document:
        raise ValueError(f"No allowed fields provided for '{profile.skill_name}'.")

    now = datetime.utcnow()
    update_doc = {
        "$set": {
            **document,
            "updated_at": now,
        }
    }
    if upsert:
        update_doc["$setOnInsert"] = {"created_at": now}

    get_collection_handle(profile).update_one(filters, update_doc, upsert=upsert)
    return find_one(profile, filters)


def count_documents(
    profile: CollectionProfile,
    filters: Optional[Dict[str, Any]] = None,
) -> int:
    """Count documents for a profile with optional filters."""
    return get_collection_handle(profile).count_documents(filters or {})
