from typing import Optional, Tuple

from aenum import Enum, extend_enum
from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query, Response

from ...crud.sync_db.tile_cache_assets import get_versions
from ...models.enumerators.tile_caches import TileCacheType
from .. import DATE_REGEX, optional_implementation_dependency, raster_xyz
from ..raster_tiles import (
    get_cached_response,
    get_dynamic_raster_tile,
    hash_query_params,
)

router = APIRouter()

dataset = "umd_glad_alerts"


class UmdGladVersions(str, Enum):
    """UMD Glad Alerts versions. When using `latest` call will be redirected (307) to version tagged as latest."""

    latest = "latest"


_versions = get_versions(dataset, TileCacheType.raster_tile_cache)
for _version in _versions:
    extend_enum(UmdGladVersions, _version, _version)


@router.get(
    f"/{dataset}/{{version}}/dynamic/{{z}}/{{x}}/{{y}}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def umd_glad_alerts_raster_tile(
    *,
    version: UmdGladVersions = Path(..., description=UmdGladVersions.__doc__),
    xyz: Tuple[int, int, int] = Depends(raster_xyz),
    start_date: Optional[str] = Query(
        None,
        regex=DATE_REGEX,
        description="Only show alerts for given date and after",
    ),
    end_date: Optional[str] = Query(
        None, regex=DATE_REGEX, description="Only show alerts until given date."
    ),
    confirmed_only: Optional[bool] = Query(
        None, description="Only show confirmed alerts"
    ),
    implementation: str = Depends(optional_implementation_dependency),
    background_tasks: BackgroundTasks,
) -> Response:
    """
    UMD GLAD alerts raster tiles.
    """
    x, y, z = xyz

    payload = {
        "dataset": dataset,
        "version": version,
        "implementation": implementation,
        "x": x,
        "y": y,
        "z": z,
    }

    if implementation:
        return await get_dynamic_raster_tile(payload, implementation, background_tasks)

    else:
        payload.update(
            implementation="default",
            start_date=start_date,
            end_date=end_date,
            confirmed_only=confirmed_only,
            filter_type="deforestation_alerts",
            source="tilecache",
        )
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "confirmed_only": confirmed_only,
        }
        query_hash = hash_query_params(params)
        return await get_cached_response(payload, query_hash, background_tasks)
