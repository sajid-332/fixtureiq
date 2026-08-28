"""
FixtureIQ API-Football local cache.

Stage 7.1.9

Responsibilities:
- Store raw API responses locally.
- Generate deterministic cache filenames.
- Load previously cached responses.
- Keep API credentials completely out of cache metadata.

The API key is NEVER stored in this cache.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


# =================================================
# Project paths
# =================================================

BASE_DIR = Path(__file__).resolve().parents[2]

CACHE_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "api_football"
)


# =================================================
# Endpoint normalization
# =================================================


def _normalize_endpoint(
    endpoint: str,
) -> str:
    """
    Normalize an API endpoint so that:

        fixtures
        /fixtures
        /fixtures/

    all refer to the same cache key.
    """

    return (
        str(endpoint)
        .strip()
        .strip("/")
    )


# =================================================
# Request hash
# =================================================


def _request_hash(
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a deterministic identifier for an API request.

    Endpoint formatting is normalized before hashing.
    """

    normalized_endpoint = _normalize_endpoint(
        endpoint
    )

    normalized_params = (
        params or {}
    )

    payload = json.dumps(
        {
            "endpoint": normalized_endpoint,
            "params": normalized_params,
        },
        sort_keys=True,
        default=str,
    )

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()[:16]


# =================================================
# Cache filename
# =================================================


def _cache_path(
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Build the deterministic cache file path.
    """

    normalized_endpoint = _normalize_endpoint(
        endpoint
    )

    request_id = _request_hash(
        normalized_endpoint,
        params,
    )

    safe_endpoint = (
        normalized_endpoint
        .replace("/", "_")
        or "root"
    )

    filename = (
        f"{safe_endpoint}_"
        f"{request_id}.json"
    )

    return CACHE_DIR / filename


# =================================================
# Save response
# =================================================


def save_response(
    endpoint: str,
    params: Optional[Dict[str, Any]],
    response: Dict[str, Any],
) -> Path:
    """
    Save a raw API response locally.

    The API key is not included in the saved document.
    """

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = _cache_path(
        endpoint,
        params,
    )

    cache_document = {
        "cached_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "endpoint":
            _normalize_endpoint(endpoint),

        "params":
            params or {},

        "response":
            response,
    }

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            cache_document,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return path


# =================================================
# Load response
# =================================================


def load_response(
    endpoint: str,
    params: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Load a cached API response.

    Returns None when the cache does not exist
    or contains invalid JSON.
    """

    path = _cache_path(
        endpoint,
        params,
    )

    if not path.exists():

        return None

    try:

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    except (
        OSError,
        json.JSONDecodeError,
    ):

        return None


# =================================================
# Cache existence
# =================================================


def cache_exists(
    endpoint: str,
    params: Optional[Dict[str, Any]],
) -> bool:
    """
    Check whether a cached response exists.
    """

    return _cache_path(
        endpoint,
        params,
    ).exists()


# =================================================
# Cache information
# =================================================


def get_cache_path(
    endpoint: str,
    params: Optional[Dict[str, Any]],
) -> Path:
    """
    Return the expected cache path.

    Useful for diagnostics and tests.
    """

    return _cache_path(
        endpoint,
        params,
    )