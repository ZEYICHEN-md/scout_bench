"""
Shared MongoDB client helpers for the mongodb skill.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from bson import ObjectId
    from pymongo import MongoClient

    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    MongoClient = None
    ObjectId = None

_CLIENTS: Dict[str, Any] = {}
_DATABASES: Dict[tuple[str, str], Any] = {}
_SCRIPT_DIR = Path(__file__).resolve().parent


def _read_uri_from_config(path: Path) -> Optional[str]:
    """Read a MongoDB URI from a JSON config file."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid MongoDB config JSON at {path}: {exc}") from exc

    if not isinstance(data, dict):
        return None

    direct_uri = data.get("uri") or data.get("mongodb_uri") or data.get("MONGODB_URI")
    if isinstance(direct_uri, str) and direct_uri.strip():
        return direct_uri.strip()

    mongodb_config = data.get("mongodb")
    if isinstance(mongodb_config, dict):
        nested_uri = (
            mongodb_config.get("uri")
            or mongodb_config.get("default_uri")
            or mongodb_config.get("mongodb_uri")
        )
        if isinstance(nested_uri, str) and nested_uri.strip():
            return nested_uri.strip()

    return None


def _iter_config_paths():
    """Yield likely local config paths in priority order."""
    explicit_path = os.getenv("OPENCLAW_MONGODB_CONFIG")
    if explicit_path:
        yield Path(explicit_path).expanduser()

    seen: set[Path] = set()
    search_roots = [_SCRIPT_DIR, *_SCRIPT_DIR.parents, Path.cwd(), *Path.cwd().parents, Path.home()]

    for candidate in [
        _SCRIPT_DIR.parent / "mongodb.json",
        _SCRIPT_DIR.parent / "openclaw.json",
    ]:
        resolved = candidate.expanduser()
        if resolved in seen:
            continue
        seen.add(resolved)
        yield resolved

    for root in search_roots:
        candidates = [
            root / ".openclaw" / "mongodb.json",
            root / ".openclaw" / "openclaw.json",
        ]
        if root.name == ".openclaw":
            candidates.extend([root / "mongodb.json", root / "openclaw.json"])

        for candidate in candidates:
            resolved = candidate.expanduser()
            if resolved in seen:
                continue
            seen.add(resolved)
            yield resolved


def _resolve_uri_from_local_config() -> Optional[str]:
    """Resolve the MongoDB URI from local JSON config files."""
    for path in _iter_config_paths():
        if not path.is_file():
            continue
        uri = _read_uri_from_config(path)
        if uri:
            return uri
    return None


def resolve_mongodb_uri() -> str:
    """Resolve the MongoDB URI from env vars or local config."""
    uri = os.getenv("MONGODB_URI")
    if uri:
        return uri

    configured_uri = _resolve_uri_from_local_config()
    if configured_uri:
        return configured_uri

    raise RuntimeError(
        "MONGODB_URI is not set. Export MONGODB_URI or add skills/mongodb/mongodb.json before using the mongodb skill."
    )


def get_client(uri: Optional[str] = None):
    """Return a cached MongoClient for the configured URI."""
    if not MONGODB_AVAILABLE:
        raise RuntimeError(
            "pymongo is not installed. Run: pip install -r skills/mongodb/requirements.txt"
        )

    resolved_uri = uri or resolve_mongodb_uri()
    client = _CLIENTS.get(resolved_uri)
    if client is None:
        client = MongoClient(resolved_uri, serverSelectionTimeoutMS=5000)
        _CLIENTS[resolved_uri] = client
    return client


def get_db(database_name: str, uri: Optional[str] = None):
    """Return a cached database handle for a database name."""
    resolved_uri = uri or resolve_mongodb_uri()
    cache_key = (resolved_uri, database_name)
    db = _DATABASES.get(cache_key)
    if db is None:
        db = get_client(resolved_uri)[database_name]
        _DATABASES[cache_key] = db
    return db


def get_collection(
    database_name: str,
    collection_name: str,
    uri: Optional[str] = None,
):
    """Return a collection handle for the configured database and collection."""
    return get_db(database_name, uri=uri)[collection_name]


def serialize_value(value: Any) -> Any:
    """Recursively serialize BSON values into JSON-friendly Python values."""
    if ObjectId is not None and isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize_value(item) for key, item in value.items()}
    return value


def serialize_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Serialize a MongoDB document and rename _id to id."""
    if doc is None:
        return None

    result: Dict[str, Any] = {}
    for key, value in doc.items():
        if key == "_id":
            result["id"] = serialize_value(value)
        else:
            result[key] = serialize_value(value)

    if "id" not in result:
        result["id"] = None
    return result
