from typing import Optional, Any, Dict, List, Tuple

import pendulum
from asyncpg import Connection
from fastapi import APIRouter, Query, Response, Depends
from fastapi.logger import logger
from sqlalchemy.sql import TableClause

from app.database import a_get_db
from app.routers import DATE_REGEX
from app.schemas.esri import VectorTileService
from app.services.vector_tiles import get_mvt_table, nasa_viirs_fire_alerts
from app.services.vector_tiles.vector_tile_service import get_vector_tile_server
from app.utils.dependencies import (
    include_attributes,
    nasa_viirs_fire_alerts_filters,
    nasa_viirs_fire_alerts_version,
    dataset_version,
    xyz,
)
from app.utils.filters import (
    geometry_filter,
    confidence_filter,
    date_filter,
    contextual_filter,
)
from app.utils.validators import validate_dates
from app.services import vector_tiles

router = APIRouter()
NOW = pendulum.now()

DEFAULT_START = NOW.subtract(weeks=1).to_date_string()
DEFAULT_END = NOW.to_date_string()

Geometry = Dict[str, Any]
Bounds = Tuple[float, float, float, float]


@router.get(
    "/nasa_viirs_fire_alerts/{version}/dynamic/{z}/{x}/{y}.pbf",
    response_class=Response,
    tags=["Dynamic Vector Tiles"],
    response_description="PBF Vector Tile",
)
async def nasa_viirs_fire_alerts_tile(
    version: str = Depends(nasa_viirs_fire_alerts_version),
    bbox_z: Tuple[Bounds, int, int] = Depends(xyz),
    geostore_id: Optional[str] = Query(
        None, title="Only show fire alerts within selected geostore area"
    ),
    start_date: str = Query(
        DEFAULT_START,
        regex=DATE_REGEX,
        title="Only show alerts for given date and after",
    ),
    end_date: str = Query(
        DEFAULT_END, regex=DATE_REGEX, title="Only show alerts until given date."
    ),
    force_date_range: Optional[bool] = Query(
        False,
        title="Bypass the build in limitation to query more than 90 days at a time. Use cautiously!",
    ),
    high_confidence_only: Optional[bool] = Query(
        False, title="Only show high confidence alerts"
    ),
    include_attribute: List[str] = Depends(include_attributes),
    contextual_filters: dict = Depends(nasa_viirs_fire_alerts_filters),
    db: Connection = Depends(a_get_db),
) -> Response:
    """
    NASA VIIRS fire alerts vector tiles.
    This dataset holds the full archive of NASA VIIRS fire alerts, starting in 2012. Latest version is updated daily.
    Check `Max Date` endpoint to retrieve latest date in dataset.
    You can query fire alerts for any time period of up to 90 days. By default, the last 7 days are displayed.
    Use additional query parameters to further filter alerts.
    Vector tiles for zoom level 6 and lower will aggregate adjacent alerts into a single point.
    """
    bbox, z, extent = bbox_z
    validate_dates(start_date, end_date, force_date_range)

    filters = [
        await geometry_filter(geostore_id, bbox),
        confidence_filter(high_confidence_only),
        date_filter(start_date, end_date),
    ] + contextual_filter(**contextual_filters)

    # Remove empty filters
    filters = [f for f in filters if f is not None]

    return await nasa_viirs_fire_alerts.get_aggregated_tile(
        db, version, bbox, extent, include_attribute, *filters
    )


@router.get(
    "/{dataset}/{version}/dynamic/{z}/{x}/{y}.pbf",
    response_class=Response,
    tags=["Dynamic Vector Tiles"],
    response_description="PBF Vector Tile",
)
async def dynamic_vector_tile(
    *,
    dv: Tuple[str, str] = Depends(dataset_version),
    bbox_z: Tuple[Bounds, int, int] = Depends(xyz),
    geostore_id: Optional[str] = Query(
        None, title="Only show fire alerts within selected geostore area"
    ),
    db: Connection = Depends(a_get_db),
) -> Response:
    """
    Dynamic vector tile
    """
    dataset, version = dv
    bbox, _, extent = bbox_z

    filters: List[TableClause] = list()

    geom_filter = await geometry_filter(geostore_id, bbox)

    if geom_filter is not None:
        filters.append(geom_filter)

    query, values = get_mvt_table(dataset, version, bbox, extent, list(), *filters)

    return await vector_tiles.get_tile(db, query, name=dataset, extent=extent)


@router.get(
    "/{dataset}/{version}/default/{z}/{x}/{y}.pbf",
    response_class=Response,
    tags=["Vector Tiles"],
    response_description="PBF Vector Tile",
)
async def vector_tile(
    *,
    dv: Tuple[str, str] = Depends(dataset_version),
    bbox_z: Tuple[Bounds, int] = Depends(xyz),
) -> Response:
    """
    Generic vector tile
    """
    # This endpoint is not implemented and only exist for documentation purposes
    # Default vector layers are stored on S3.
    # If tile is not found, Cloud Front will redirect request to dynamic endpoint.
    # Hence, this function should never be called.
    raise NotImplementedError


@router.get(
    "/{dataset}/{version}/default/{z}/{x}/{y}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def raster_tile(
    *,
    dv: Tuple[str, str] = Depends(dataset_version),
    bbox_z: Tuple[Bounds, int] = Depends(xyz),
) -> Response:
    """
    Generic raster tile
    """
    # This endpoint is not implemented and only exist for documentation purposes
    # Default vector layers are stored on S3.
    # If tile is not found, Cloud Front will redirect request to dynamic endpoint.
    # Hence, this function should never be called.
    raise NotImplementedError


@router.get(
    "/nasa_viirs_fire_alerts/{version}/dynamic/VectorTileServer",
    tags=["ESRI Vector Tile Service"],
    response_model=VectorTileService,
)
async def nasa_viirs_fire_alerts_esri_vector_tile_service(
    *,
    version: str = Depends(nasa_viirs_fire_alerts_version),  # type: ignore
    geostore_id: Optional[str] = Query(None),
    start_date: str = Query(
        DEFAULT_START,
        regex=DATE_REGEX,
        title="Only show alerts for given date and after",
    ),
    end_date: str = Query(
        DEFAULT_END, regex=DATE_REGEX, title="Only show alerts until given date."
    ),
    force_date_range: Optional[bool] = Query(
        False,
        title="Bypass the build in limitation to query more than 90 days at a time. Use cautiously!",
    ),
    high_confidence_only: Optional[bool] = Query(
        False, title="Only show high confidence alerts"
    ),
    include_attribute: List[str] = Depends(include_attributes),
    contextual_filters: dict = Depends(nasa_viirs_fire_alerts_filters),
):
    """
    Mock ESRI Vector Tile Server for NASA VIIRS fire alerts.
    When using ESRI JS API, point your root.json to this URL.
    URL Parameters will be forwarded to tile cache.
    """

    fields: Dict[str, Any] = contextual_filters

    fields["geostore_id"] = geostore_id
    fields["start_date"] = start_date
    fields["end_date"] = end_date
    fields["high_confidence_only"] = high_confidence_only
    fields["force_date_range"] = force_date_range
    fields["include_attribute"] = include_attribute

    params = [f"{key}={value}" for key, value in fields.items() if value is not None]

    query_params: str = "&".join(params)

    # TODO: add scale factor to tile url
    return await get_vector_tile_server(
        "nasa_viirs_fire_alerts", version, "default", query_params
    )


@router.get(
    "/{dataset}/{version}/dynamic/VectorTileServer",
    tags=["ESRI Vector Tile Service"],
    response_model=VectorTileService,
)
async def dynamic_esri_vector_tile_service(
    *,
    dv: Tuple[str, str] = Depends(dataset_version),
    geostore_id: Optional[str] = Query(None),
):
    """
    Generic Mock ESRI Vector Tile Server.
    When using ESRI JS API, point your root.json to this URL.
    URL Parameters will be forwarded to tile cache.
    """

    dataset, version = dv
    query_params: str = f"geostore_id={geostore_id}" if geostore_id else ""

    return await get_vector_tile_server(dataset, version, "dynamic", query_params)


@router.get(
    "/{dataset}/{version}/default/VectorTileServer",
    tags=["ESRI Vector Tile Service"],
    response_model=VectorTileService,
)
async def esri_vector_tile_service(
    *, dv: Tuple[str, str] = Depends(dataset_version),
):
    """
    Generic Mock ESRI Vector Tile Server.
    When using ESRI JS API, point your root.json to this URL.
    URL Parameters will be forwarded to tile cache.
    """
    # This endpoint is not implemented and only exist for documentation purposes
    # Default vector layers are stored on S3.
    # If tile is not found, Cloud Front will redirect request to dynamic endpoint.
    # Hence, this function should never be called.
    raise NotImplementedError
