"""
Car API (carapi.app) client for OBD-II code lookup.
Used as fallback when a code is not in the local database.
Free tier available; optional CAR_API_KEY for higher limits.
"""

import logging
from typing import Any

import httpx

from core.config import get_settings

logger = logging.getLogger(__name__)

CAR_API_BASE = "https://carapi.app/api"


def get_obd_code(code: str) -> dict[str, Any] | None:
    """
    Look up a single OBD-II code from Car API.

    Args:
        code: OBD-II code (e.g. P0300, B1200). Normalized to uppercase.

    Returns:
        Dict with "code" and "description", or None if not found / API unavailable.
    """
    code = (code or "").strip().upper()
    if not code or len(code) < 5:
        return None

    settings = get_settings()
    headers = {"Accept": "application/json"}
    if settings.car_api_key:
        headers["Authorization"] = f"Bearer {settings.car_api_key}"

    # Car API filter: get single code
    params = {"json": '[{"field":"code","op":"=","val":"' + code + '"}]'}

    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{CAR_API_BASE}/obd-codes", headers=headers, params=params)
            if r.status_code == 401:
                logger.debug("Car API: unauthorized (key may be required)")
                return None
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.debug("Car API lookup failed for %s: %s", code, e)
        return None

    results = data.get("data") or []
    if not results:
        return None

    first = results[0] if isinstance(results[0], dict) else None
    if not first:
        return None

    return {
        "code": first.get("code") or code,
        "description": first.get("description") or "",
    }
