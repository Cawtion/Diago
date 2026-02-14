"""
Simple in-memory rate limiter per user tier.

For production, replace with Redis-backed rate limiting.
"""

import logging
import time
from collections import defaultdict
from typing import Optional

from fastapi import Depends, HTTPException, Request

from api.middleware.auth import AuthenticatedUser, UserTier, get_optional_user

logger = logging.getLogger(__name__)

# ─── Rate Limit Configuration ───

# Diagnoses per month by tier
TIER_LIMITS = {
    UserTier.FREE: 3,
    UserTier.PRO: 1000,       # effectively unlimited
    UserTier.PREMIUM: 10000,  # effectively unlimited
}

# In-memory counters: { user_id: { month_key: count } }
_counters: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))


def _month_key() -> str:
    """Current month key for rate limiting."""
    t = time.gmtime()
    return f"{t.tm_year}-{t.tm_mon:02d}"


def check_diagnosis_rate_limit(
    user: Optional[AuthenticatedUser] = None,
    client_ip: str = "unknown",
) -> None:
    """
    Check if the user has exceeded their monthly diagnosis limit.

    Raises HTTPException 429 if over limit.
    """
    tier = user.tier if user else UserTier.FREE
    limit = TIER_LIMITS[tier]
    key = user.user_id if user else f"anon:{client_ip}"
    month = _month_key()

    current = _counters[key][month]
    if current >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Monthly diagnosis limit reached ({limit} for {tier.value} tier). Upgrade for more.",
        )


def increment_diagnosis_count(
    user: Optional[AuthenticatedUser] = None,
    client_ip: str = "unknown",
) -> None:
    """Increment the diagnosis counter after a successful diagnosis."""
    key = user.user_id if user else f"anon:{client_ip}"
    month = _month_key()
    _counters[key][month] += 1


def get_remaining_diagnoses(
    user: Optional[AuthenticatedUser] = None,
    client_ip: str = "unknown",
) -> dict:
    """Get remaining diagnosis count for the current month."""
    tier = user.tier if user else UserTier.FREE
    limit = TIER_LIMITS[tier]
    key = user.user_id if user else f"anon:{client_ip}"
    month = _month_key()
    used = _counters[key][month]

    return {
        "tier": tier.value,
        "limit": limit,
        "used": used,
        "remaining": max(0, limit - used),
    }
