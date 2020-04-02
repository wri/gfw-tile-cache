import logging
from typing import Optional, Any, Dict, List, Tuple

import pendulum
from asyncpg import Connection
from fastapi import APIRouter, Path, Query, HTTPException, Response, Depends
from sqlalchemy.sql import TableClause

from app.database import a_get_db
from app.routers import DATE_REGEX, VERSION_REGEX
from app.schemas.enumerators import ViirsVersion, Implementation, Dataset
from app.schemas.esri import VectorTileService
from app.services.vector_tiles import get_mvt_table, nasa_viirs_fire_alerts
from app.services.vector_tiles.vector_tile_service import get_vector_tile_server
from app.utils.dependencies import nasa_viirs_fire_alerts_filters
from app.utils.tiles import to_bbox
from app.utils.filters import (
    geometry_filter,
    confidence_filter,
    date_filter,
    contextual_filter,
)
from app.utils.validators import (
    validate_dates,
    validate_bbox,
    validate_field_types,
    sanitize_fields,
    validate_version,
)
from app.services import vector_tiles

LOGGER = logging.Logger(__name__)
router = APIRouter()
NOW = pendulum.now()

DEFAULT_START = NOW.subtract(weeks=1).to_date_string()
DEFAULT_END = NOW.to_date_string()

Geometry = Dict[str, Any]
Bounds = Tuple[float, float, float, float]


@router.get(
    "/nasa_viirs_fire_alerts/{version}/tile/{implementation}/{z}/{x}/{y}.pbf",
    response_class=Response,
    tags=["Tiles"],
    response_description="PBF Vector Tile",
)
async def nasa_viirs_fire_alerts_tile(
    version: ViirsVersion,
    implementation: Implementation,
    x: int = Path(..., title="Tile grid column", ge=0),
    y: int = Path(..., title="Tile grid row", ge=0),
    z: int = Path(..., title="Zoom level", ge=0, le=22),
    geostore_id: Optional[str] = Query(None),
    start_date: str = Query(DEFAULT_START, regex=DATE_REGEX),
    end_date: str = Query(DEFAULT_END, regex=DATE_REGEX),
    high_confidence_only: Optional[bool] = Query(False),
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

    # TODO: There must be a better way!
    fields: Dict[str, Any] = contextual_filters

    fields = sanitize_fields(**fields)
    validate_field_types(**fields)
    validate_dates(start_date, end_date)
    validate_version("dataset", version)

    bbox = to_bbox(x, y, z)
    validate_bbox(*bbox)

    filters = [
        await geometry_filter(geostore_id, bbox),
        confidence_filter(high_confidence_only),
        date_filter(start_date, end_date),
    ] + contextual_filter(**fields)

    filters = [f for f in filters if f is not None]

    if implementation == "default" and z >= 6:
        return await nasa_viirs_fire_alerts.get_tile(db, version, bbox, *filters)
    elif implementation == "default" and z < 6:
        return await nasa_viirs_fire_alerts.get_aggregated_tile(
            db, version, bbox, *filters
        )
    else:
        raise HTTPException(
            status_code=400, detail=f"Unknown Implementation {implementation}."
        )


@router.get(
    "/{dataset}/{version}/tile/{implementation}/{z}/{x}/{y}.pbf",
    response_class=Response,
    tags=["Tiles"],
    response_description="PBF Vector Tile",
)
async def tile(
    *,
    dataset: Dataset,
    version: str = Path(..., title="Dataset version", regex=VERSION_REGEX),
    implementation: Implementation,
    x: int = Path(..., title="Tile grid column", ge=0),
    y: int = Path(..., title="Tile grid row", ge=0),
    z: int = Path(..., title="Zoom level", ge=0, le=22),
    geostore_id: Optional[str] = Query(None),
    db: Connection = Depends(a_get_db),
) -> Response:
    """
    Generic vector tile
    """

    bbox = to_bbox(x, y, z)
    validate_bbox(*bbox)
    validate_version(dataset, version)

    filters: List[TableClause] = list()

    f = await geometry_filter(geostore_id, bbox)

    if f is not None:
        filters.append(f)

    if implementation == "default":
        query, values = get_mvt_table(dataset, version, bbox, list(), *filters)

        return await vector_tiles.get_tile(db, query)

    raise HTTPException(
        status_code=400, detail=f"Unknown implementation {implementation}"
    )


@router.get(
    "/nasa_viirs_fire_alerts/{version}/tile/{implementation}/VectorTileServer",
    tags=["Tiles"],
    response_model=VectorTileService,
)
async def nasa_viirs_fire_alerts_esri_vector_tile_service(
    *,
    dataset: Dataset,
    version: str = Path(..., title="Dataset version", regex=VERSION_REGEX),
    implementation: Implementation,
    geostore_id: Optional[str] = Query(None),
    start_date: str = Query(DEFAULT_START, regex=DATE_REGEX),
    end_date: str = Query(DEFAULT_END, regex=DATE_REGEX),
    high_confidence_only: Optional[bool] = Query(False),
    contextual_filters: dict = Depends(nasa_viirs_fire_alerts_filters),
):
    """
    Mock ESRI Vector Tile Server for NASA VIIRS fire alerts.
    When using ESRI JS API, point your root.json to this URL.
    URL Parameters will be forwarded to tile cache.
    """

    # TODO: There must be a better way!
    fields: Dict[str, Any] = contextual_filters

    fields = sanitize_fields(**fields)
    validate_field_types(**fields)
    validate_dates(start_date, end_date)
    validate_version("dataset", version)

    fields["geostore_id"] = geostore_id
    fields["start_date"] = start_date
    fields["end_date"] = end_date
    fields["high_confidence_only"] = high_confidence_only

    params = [f"{key}={value}" for key, value in fields.items() if value is not None]

    query_params: str = "&".join(params)

    return await get_vector_tile_server(dataset, version, implementation, query_params)


@router.get(
    "/{dataset}/{version}/tile/{implementation}/VectorTileServer",
    tags=["Tiles"],
    response_model=VectorTileService,
)
async def esri_vector_tile_service(
    *,
    dataset: Dataset,
    version: str = Path(..., title="Dataset version", regex=VERSION_REGEX),
    implementation: Implementation,
    geostore_id: Optional[str] = Query(None),
):
    """
    Generic Mock ESRI Vector Tile Server.
    When using ESRI JS API, point your root.json to this URL.
    URL Parameters will be forwarded to tile cache.
    """
    validate_version(dataset, version)
    query_params: str = f"geostore_id={geostore_id}" if geostore_id else ""

    return await get_vector_tile_server(dataset, version, implementation, query_params)
