from typing import Optional, Tuple
from uuid import UUID

import pendulum
from aenum import Enum, extend_enum
from asyncpg import QueryCanceledError
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response

from ...application import db
from ...crud.async_db.vector_tiles import get_mvt_table, get_tile
from ...crud.async_db.vector_tiles.filters import (
    date_filter,
    filter_gt,
    geometry_filter,
)
from ...crud.sync_db.tile_cache_assets import default_end, default_start, get_versions
from ...models.enumerators.geostore import GeostoreOrigin
from ...models.enumerators.tile_caches import TileCacheType
from ...models.enumerators.versions import Versions
from ...responses import VectorTileResponse
from ...routes import DATE_REGEX, Bounds, validate_dates, vector_xyz

router = APIRouter()

dataset = "umd_modis_burned_areas"
default_duration = pendulum.duration(months=3)


class UmdModisBurnedAreas(str, Enum):
    """MODIS burned areas versions. When using `latest` call will be redirected (307) to version tagged as latest."""

    latest = "latest"


_versions = get_versions(dataset, TileCacheType.dynamic_vector_tile_cache)
for _version in _versions:
    extend_enum(UmdModisBurnedAreas, _version, _version)


async def umd_modis_burned_areas_version(
    version: UmdModisBurnedAreas = Path(..., description=UmdModisBurnedAreas.__doc__),
) -> Versions:
    if version == "latest":
        raise HTTPException(
            status_code=400,
            detail="You must list version name explicitly for this operation.",
        )
    return version


@router.get(
    f"/{dataset}/{{version}}/dynamic/{{z}}/{{x}}/{{y}}.pbf",
    response_class=VectorTileResponse,
    tags=["Dynamic Vector Tiles"],
    response_description="PBF Vector Tile",
)
async def umd_modis_burned_areas_tile(
    response: Response,
    version: UmdModisBurnedAreas = Path(..., description=UmdModisBurnedAreas.__doc__),
    bbox_z: Tuple[Bounds, int, int] = Depends(vector_xyz),
    geostore_id: Optional[UUID] = Query(
        None, description="Only show fire alerts within selected geostore area"
    ),
    geostore_origin: GeostoreOrigin = Query(
        "gfw", description="Origin service of geostore ID"
    ),
    start_date: str = Query(
        default_start(dataset, default_duration),
        regex=DATE_REGEX,
        description="Only show alerts for given date and after",
    ),
    end_date: str = Query(
        default_end(dataset),
        regex=DATE_REGEX,
        description="Only show alerts until given date. End date cannot be in the future.",
    ),
    force_date_range: Optional[bool] = Query(
        False,
        description="Bypass the build in limitation to query more than 90 days at a time. Use cautiously!",
    ),
) -> VectorTileResponse:
    """"""
    bbox, z, extent = bbox_z
    validate_dates(start_date, end_date, default_end(dataset), force_date_range)

    filters = [
        await geometry_filter(geostore_id, bbox, geostore_origin),
        date_filter("alert__date", start_date, end_date),
    ]

    if z < 7:
        filters += [filter_gt("gfw_area__ha", 25)]

    # Remove empty filters
    filters = [f for f in filters if f is not None]

    # If one of the default dates is used, we cannot cache the response for long,
    # as content might change after next update. For non-default values we can be certain,
    # that response will always be the same b/c we only add newer dates
    # and users are not allowed to query future dates
    if start_date == default_start(
        dataset, default_duration
    ) or end_date == default_end(dataset):
        response.headers["Cache-Control"] = "max-age=86400"  # 1d
    else:
        response.headers["Cache-Control"] = "max-age=31536000"  # 1 year

    try:
        schema = "umd_modis_burned_areas"
        columns = [db.column("alert__date")]
        query = get_mvt_table(schema, version, bbox, extent, columns, filters, columns)
        tile = await get_tile(query, schema, extent)
    except QueryCanceledError:
        raise HTTPException(
            status_code=524,
            detail="A timeout occurred while processing the request. Request canceled.",
        )
    else:
        return tile
