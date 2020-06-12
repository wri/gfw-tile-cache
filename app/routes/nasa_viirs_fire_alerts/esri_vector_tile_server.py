from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Path, Query

from app.models.pydantic.esri import VectorTileService
from app.routes import DATE_REGEX
from app.routes.esri_vector_tile_server import get_vector_tile_server
from app.routes.nasa_viirs_fire_alerts.vector_tiles import (
    nasa_viirs_fire_alerts_version,
)

router = APIRouter()


@router.get(
    "/nasa_viirs_fire_alerts/{version}/dynamic/{start_date}/{end_date}/VectorTileServer",
    tags=["ESRI Vector Tile Service"],
    response_model=VectorTileService,
)
async def nasa_viirs_fire_alerts_esri_vector_tile_service_dates(
    *,
    version: str = Depends(nasa_viirs_fire_alerts_version),  # type: ignore
    start_date: str = Path(
        ..., regex=DATE_REGEX, title="Only show alerts for given date and after",
    ),
    end_date: str = Path(
        ..., regex=DATE_REGEX, title="Only show alerts until given date."
    ),
):
    """
    Mock ESRI Vector Tile Server for NASA VIIRS fire alerts.
    When using ESRI JS API, point your root.json to this URL.
    URL Parameters will be forwarded to tile cache.
    """

    fields: Dict[str, Any] = dict()

    fields["start_date"] = start_date
    fields["end_date"] = end_date

    params = [f"{key}={value}" for key, value in fields.items() if value is not None]

    query_params: str = "&".join(params)

    # TODO: add scale factor to tile url
    return await get_vector_tile_server(
        "nasa_viirs_fire_alerts", version, "default", query_params, levels=3
    )


@router.get(
    "/nasa_viirs_fire_alerts/{version}/dynamic/VectorTileServer",
    tags=["ESRI Vector Tile Service"],
    response_model=VectorTileService,
)
async def nasa_viirs_fire_alerts_esri_vector_tile_service(
    *, version: str = Depends(nasa_viirs_fire_alerts_version),  # type: ignore
):
    """
    Mock ESRI Vector Tile Server for NASA VIIRS fire alerts.
    When using ESRI JS API, point your root.json to this URL.
    URL Parameters will be forwarded to tile cache.
    """

    # TODO: add scale factor to tile url
    return await get_vector_tile_server("nasa_viirs_fire_alerts", version, "dynamic")
