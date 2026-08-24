"""Planet imagery masked to integrated alerts.

Proxies the WMTS service that does the masking. Planet mosaics are monthly, so
tiles are requested by month.
"""

import datetime

import httpx
from fastapi import APIRouter, HTTPException, Path, Query, Response
from fastapi.logger import logger

from ..settings.globals import GLOBALS

router = APIRouter()

client = httpx.AsyncClient(timeout=GLOBALS.httpx_timeout)

dataset = "integrated_alerts_planet_imagery"

MONTH_REGEX = r"^\d{4}-(0[1-9]|1[0-2])$"


@router.get(
    f"/{dataset}/{{z}}/{{x}}/{{y}}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def integrated_alerts_planet_imagery_tile(
    *,
    month: str = Query(
        ...,
        pattern=MONTH_REGEX,
        description="Month the imagery should cover, as `YYYY-MM`. The Planet mosaic for this month is served.",
        examples=["2026-07"],
    ),
    z: int = Path(..., description="Zoom level", ge=3, le=15),
    x: int = Path(..., description="Tile grid column", ge=0),
    y: int = Path(..., description="Tile grid row", ge=0),
) -> Response:
    """Planet imagery masked to integrated alerts."""

    url = (
        f"{GLOBALS.integrated_alerts_planet_imagery_url}/wmts/v1/"
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

    # A mosaic is only final once its month is over; the current month's is still
    # being built from incoming imagery, and a future one doesn't exist yet.
    # Zero-padded `YYYY-MM` sorts chronologically, so compare as strings.
    is_final = month < f"{datetime.date.today():%Y-%m}"
    max_age = 31536000 if is_final else 86400  # 1y / 1d

    return Response(
        response.content,
        media_type="image/png",
        headers={"Cache-Control": f"max-age={max_age}"},
    )
