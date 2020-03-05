import functools
from typing import Optional, Any, Tuple, Dict
from shapely.geometry import shape, box
from shapely.geometry.base import BaseGeometry

import mercantile
import pendulum
import requests

from app import get_module_logger
from app.vector_tiles import get_aggregated_tile, get_tile
from fastapi import APIRouter, Path, Query, HTTPException
from starlette.responses import Response

LOGGER = get_module_logger(__name__)
router = APIRouter()
NOW = pendulum.now()
DATE_REGEX = "^\d{4}\-(0?[1-9]|1[012])\-(0?[1-9]|[12][0-9]|3[01])$"  # mypy: ignore
DEFAULT_START = NOW.subtract(weeks=1).to_date_string()
DEFAULT_END = NOW.to_date_string()

Geometry = Dict[str, Any]


@router.get(
    "/nasa_viirs_fire_alerts/latest/default/{z}/{x}/{y}.pbf",
    response_class=Response,
    tags=["tiles"],
)
async def nasa_viirs_fire_alerts(
    x: int = Path(..., title="Tile grid column", ge=0),
    y: int = Path(..., title="Tile grid row", ge=0),
    z: int = Path(..., title="Zoom level", ge=0, le=22),
    start_date: str = Query(DEFAULT_START, regex=DATE_REGEX),
    end_date: str = Query(DEFAULT_END, regex=DATE_REGEX),
    high_confidence_only: bool = Query(False),
    geostore_id: Optional[str] = Query(None),
) -> Response:
    LOGGER.info(f"Get tile {z}/{x}/{y}")
    LOGGER.info(f"Date range set to {start_date} - {end_date}")

    _validate_dates(start_date, end_date)
    tile_bounds = _validate_tile_index(x, y, z)

    geometry_filter = await get_geometry_filter(geostore_id, tile_bounds)
    confidence_filter = get_confidence_filter(high_confidence_only)

    if z >= 6:
        return await get_tile(
            tile_bounds, start_date, end_date, confidence_filter, geometry_filter
        )
    else:
        return await get_aggregated_tile(
            tile_bounds, start_date, end_date, confidence_filter, geometry_filter
        )


def _validate_dates(start_date: str, end_date: str) -> None:
    _start_date = pendulum.from_format(start_date, "YYYY-MM-DD")
    _end_date = pendulum.from_format(end_date, "YYYY-MM-DD")

    if _start_date > _end_date:
        raise HTTPException(
            status_code=403, detail="Start date must be smaller or equal to end date"
        )

    diff = _end_date - _start_date
    if diff.in_days() > 90:
        raise HTTPException(status_code=403, detail="Date range cannot exceed 90 days")


def _validate_tile_index(x: int, y: int, z: int) -> box:
    tile = mercantile.Tile(x, y, z)
    left, bottom, right, top = mercantile.bounds(tile)
    if left < -180 or bottom < -90 or right > 180 or top > 90:
        raise HTTPException(status_code=403, detail="Tile index is out of bounds")

    return box(left, bottom, right, top)


async def get_geometry_filter(geostore_id: Optional[str], tile_bounds: box) -> str:
    geometry_filter: str = ""

    if isinstance(geostore_id, str):
        geometry, envelope = await _get_geostore_geometry(geostore_id)
        if not envelope.intersects(tile_bounds):
            raise HTTPException(
                status_code=404, detail="Tile does not intersect with geostore"
            )
        geometry_filter = f"AND ST_Intersects(t.geom, ST_SetSRID(ST_GeomFromGeoJSON({geometry}),4326))"

    return geometry_filter


@functools.lru_cache(maxsize=128, typed=False)
async def _get_geostore_geometry(geostore_id: str) -> Tuple[Geometry, BaseGeometry]:
    url = f"https://production-api.globalforestwatch/v2/geostore/{geostore_id}"
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=403, detail="Call to geostore failed")

    try:
        geometry = response.json()["data"]["attributes"]["geojson"]["features"][0][
            "geometry"
        ]
    except KeyError:
        raise HTTPException(status_code=403, detail="Cannot fetch geostore geometry")

    return geometry, shape(geometry).envelope


def get_confidence_filter(high_confidence_only):
    if high_confidence_only:
        confidence_filter = "AND confidence = 'h'"
    else:
        confidence_filter = ""

    return confidence_filter
