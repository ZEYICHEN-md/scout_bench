"""
Shared MongoDB client helpers for the mongodb skill.
"""

import os
from datetime import datetime
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


def resolve_mongodb_uri() -> str:
    """Resolve the MongoDB URI from environment variables."""
    uri = os.getenv("MONGODB_URI")
    if uri:
        return uri
    raise RuntimeError(
        "MONGODB_URI is not set. Export MONGODB_URI before using the mongodb skill."
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
