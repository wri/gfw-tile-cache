"""How much of Planet's monthly tile allowance is left."""

import datetime
from typing import Optional

import httpx
import pendulum
from async_lru import alru_cache
from fastapi.logger import logger

from .planet_usage import fetch_monthly_usage

USAGE_CACHE_SECONDS = 300


@alru_cache(maxsize=2, ttl=USAGE_CACHE_SECONDS)
async def tiles_used_this_month(
    client: httpx.AsyncClient,
    *,
    subscription_id: int,
    api_key: str,
    month: str,
) -> Optional[int]:
    """Tile views so far this month, or None if Planet can't be read.

    `month` is a cache key, not a query parameter.
    """
    try:
        return await fetch_monthly_usage(
            client,
            subscription_id=subscription_id,
            api_key=api_key,
            today=datetime.date.today(),
        )
    except (httpx.HTTPError, KeyError, ValueError) as error:
        logger.error(f"Planet tile usage for {month} is unavailable: {error}")
        return None


def seconds_until_quota_reset() -> int:
    """Seconds until the allowance resets."""
    now = pendulum.now("UTC")
    return int((now.start_of("month").add(months=1) - now).total_seconds())
