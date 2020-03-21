from enum import Enum
from typing import Optional, Any, Dict, Union, List

import pendulum
from sqlalchemy.sql import TableClause

from app.src import get_module_logger  # , get_pool
from app.src.services.vector_tiles import get_mvt_table
from app.src.utils.tiles import to_bbox
from app.src.utils.filters import (
    geometry_filter,
    confidence_filter,
    date_filter,
    contextual_filter,
)
from app.src.utils.validators import (
    validate_dates,
    validate_bbox,
    validate_field_types,
    sanitize_fields,
)
from app.src.services import nasa_viirs_fire_alerts, vector_tiles
from fastapi import APIRouter, Path, Query, HTTPException, Response

LOGGER = get_module_logger(__name__)
router = APIRouter()
NOW = pendulum.now()
DATE_REGEX = "^\d{4}\-(0?[1-9]|1[012])\-(0?[1-9]|[12][0-9]|3[01])$"  # mypy: ignore
VERSION_REGEX = r"^v\d{,8}\.?\d{,3}\.?\d{,3}$|^latest$"
DEFAULT_START = NOW.subtract(weeks=1).to_date_string()
DEFAULT_END = NOW.to_date_string()

Geometry = Dict[str, Any]


# pool = get_pool()


# @router.get(
#     "/nasa_viirs_fire_alerts/latest/default/max_date"
# )
# async def nasa_viirs_fire_alerts_max_date():
#     sql = "select max(acq_date) from viirs.v20200224;"
#     async with pool.acquire() as conn:
#         stmt = await conn.prepare(sql)
#         max_date = await stmt.fetchval(timeout=30)
#     return {"max_date": max_date}


class Dataset(str, Enum):
    nasa_viirs_fire_alerts = "nasa_viirs_fire_alerts"


class ViirsVersion(str, Enum):
    v20200224 = "v20200224"
    latest = "latest"


class Implementation(str, Enum):
    default = "default"


@router.get(
    "/nasa_viirs_fire_alerts/{version}/{implementation}/{z}/{x}/{y}.pbf",
    response_class=Response,
    tags=["tiles"],
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
    high_confidence_only: bool = Query(False),
) -> Response:
    fields: Dict[str, Any] = dict()
    fields = sanitize_fields(**fields)
    validate_field_types(**fields)
    validate_dates(start_date, end_date)

    bbox = to_bbox(x, y, z)
    validate_bbox(*bbox.bounds)

    ff = [
        await geometry_filter(geostore_id, bbox),
        confidence_filter(high_confidence_only),
        date_filter(start_date, end_date),
    ] + contextual_filter(**fields)

    filters: List[TableClause] = list()
    values: Dict[str, Any] = dict()
    for f in ff:
        if f is not None:
            filters.append(f[0])
            values.update(f[1])

    if implementation == "default" and z >= 6:
        return await nasa_viirs_fire_alerts.get_tile(
            version, bbox.bounds, *filters, **values
        )
    elif implementation == "default" and z < 6:
        return await nasa_viirs_fire_alerts.get_aggregated_tile(
            version, bbox.bounds, *filters, **values
        )
    else:
        raise HTTPException(
            status_code=400, detail=f"Unknown Implementation {implementation}."
        )


@router.get(
    "/{dataset}/{version}/{implementation}/{z}/{x}/{y}.pbf",
    response_class=Response,
    tags=["tiles"],
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
) -> Response:
    bbox = to_bbox(x, y, z)
    validate_bbox(*bbox.bounds)

    filters: List[TableClause] = list()
    values: Dict[str, Any] = dict()

    f = await geometry_filter(geostore_id, bbox.bounds)

    if f is not None:
        filters.append(f[0])
        values.update(f[1])

    if implementation == "default":
        query, values = get_mvt_table(
            f"{dataset}.{version}", bbox, list(), *filters, **values
        )

        return await vector_tiles.get_tile(query, **values)

    raise HTTPException(
        status_code=400, detail=f"Unknown implementation {implementation}"
    )
