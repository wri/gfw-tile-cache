"""Planet imagery masked to integrated alerts.

The upstream WMTS service serves Planet monthly basemap imagery clipped to a
buffer around integrated alerts. That masking is the reason this route exists
and why alerts are in its name; general-purpose Planet imagery would go straight
to Planet's public endpoints instead.

Planet publishes one mosaic per calendar month, so tiles are requested by month.
"""

import httpx
import pendulum
from fastapi import APIRouter, HTTPException, Path, Query, Response
from fastapi.logger import logger
from newrelic.agent import record_custom_event

from ..settings.globals import GLOBALS
from ..utils.planet_quota import seconds_until_quota_reset, tiles_used_this_month

router = APIRouter()

client = httpx.AsyncClient(timeout=GLOBALS.httpx_timeout)

MONTH_REGEX = r"^\d{4}-(0[1-9]|1[0-2])$"

ARCHIVE_START_MONTH = "2020-09"  # first Planet monthly mosaic

PLANET_SUBSCRIPTION_ID = 800877
MONTHLY_TILE_LIMIT = 250_000
ALERT_REFRESH_DAY = 16


def seconds_until_alert_refresh(now: pendulum.DateTime) -> int:
    """Seconds until Planet next republishes the alert mask."""
    refresh = now.set(day=ALERT_REFRESH_DAY).start_of("day")
    if refresh <= now:
        refresh = refresh.add(months=1)
    return int((refresh - now).total_seconds())


def cache_headers(now: pendulum.DateTime) -> dict:
    """Cache headers that expire with the alert mask."""
    return {"Cache-Control": f"max-age={seconds_until_alert_refresh(now)}"}


async def quota_exhausted() -> bool:
    """Whether the plan has spent its monthly tile allowance."""
    if not GLOBALS.planet_api_key:
        return False
    used = await tiles_used_this_month(
        client,
        subscription_id=PLANET_SUBSCRIPTION_ID,
        api_key=str(GLOBALS.planet_api_key),
        month=pendulum.now("UTC").format("YYYY-MM"),
    )
    return used is not None and used >= MONTHLY_TILE_LIMIT


@router.get(
    "/integrated_alerts_planet_imagery/{z}/{x}/{y}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def integrated_alerts_planet_imagery_tile(
    *,
    month: str = Query(
        ...,
        pattern=MONTH_REGEX,
        description="Month the imagery should cover, as `YYYY-MM`. The Planet mosaic for this month is served. "
        f"Ranges from {ARCHIVE_START_MONTH} to the last full calendar month.",
        examples=["2026-07"],
    ),
    z: int = Path(..., description="Zoom level", ge=10, le=15),
    x: int = Path(..., description="Tile grid column", ge=0),
    y: int = Path(..., description="Tile grid row", ge=0),
) -> Response:
    """Planet imagery masked to integrated alerts."""

    if not GLOBALS.planet_integrated_alerts_url:
        raise HTTPException(
            status_code=503, detail="Planet imagery service is not configured"
        )

    # Mosaics run from the start of the archive to the last month that has ended.
    # Zero-padded `YYYY-MM` sorts chronologically, so compare as strings.
    last_full_month = pendulum.today().subtract(months=1).format("YYYY-MM")
    if not ARCHIVE_START_MONTH <= month <= last_full_month:
        raise HTTPException(
            status_code=422,
            detail=f"Month must be between {ARCHIVE_START_MONTH} and {last_full_month}, the last full calendar month",
        )

    if await quota_exhausted():
        raise HTTPException(
            status_code=429,
            detail="Planet monthly tile allowance is exhausted",
            headers={
                "Retry-After": str(seconds_until_quota_reset()),
                "Cache-Control": "no-store",
            },
        )

    url = (
        f"{GLOBALS.planet_integrated_alerts_url}/wmts/v1/"
        f"planet_medres_visual_{month}_mosaic/{z}/{x}/{y}.png"
    )

    try:
        response = await client.get(url)
    except httpx.HTTPError as error:
        logger.error(f"Could not reach {url}: {error}")
        raise HTTPException(status_code=502, detail="Planet imagery is unavailable")

    if response.status_code == 404:
        raise HTTPException(
            status_code=404, detail="No Planet mosaic for this month and tile"
        )

    if response.status_code != 200:
        logger.error(f"{url} returned status {response.status_code}")
        raise HTTPException(status_code=502, detail="Planet imagery is unavailable")

    # NR Telemetry: Track tiles actually served against Planet's monthly tile quota.
    record_custom_event("PlanetTileRequest", {"month": month, "zoom": z})

    return Response(
        response.content,
        media_type="image/png",
        headers=cache_headers(pendulum.now("UTC")),
    )
