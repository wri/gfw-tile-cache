"""How much of Planet's monthly tile allowance is left.

The reading is taken on the tile path rather than by a background poller, but
cached, so Planet is asked at most once per TTL per gunicorn worker. Caching on
the month means a new allowance is picked up the moment the month turns, with
no extra call.

It fails open: an unreadable usage figure serves tiles, because Planet's
reporting being broken is not a reason to stop serving imagery. Failures are
cached alongside successes so an outage can't turn every tile request into a
retry.
"""

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

    `month` is a cache key rather than a query parameter: Planet is always asked
    about the current calendar month, and a new month is a new key.
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
    """Planet bills per calendar month, so the allowance returns at the 1st."""
    now = pendulum.now("UTC")
    return int((now.start_of("month").add(months=1) - now).total_seconds())
