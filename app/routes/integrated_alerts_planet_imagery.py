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

router = APIRouter()

client = httpx.AsyncClient(timeout=GLOBALS.httpx_timeout)

MONTH_REGEX = r"^\d{4}-(0[1-9]|1[0-2])$"

ARCHIVE_START_MONTH = "2020-09"  # first Planet monthly mosaic


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
    z: int = Path(..., description="Zoom level", ge=3, le=15),
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

    # Every month served is complete, so its imagery never changes again.
    return Response(
        response.content,
        media_type="image/png",
        headers={"Cache-Control": "max-age=31536000"},  # 1y
    )
