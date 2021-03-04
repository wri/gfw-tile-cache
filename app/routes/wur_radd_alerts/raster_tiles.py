from typing import Optional, Tuple, Type

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response

from ...models.enumerators.tile_caches import TileCacheType
from ...models.enumerators.versions import Versions, get_versions_enum
from .. import DATE_REGEX, optional_implementation_dependency, raster_xyz
from ..raster_tiles import (
    get_cached_response,
    get_dynamic_raster_tile,
    hash_query_params,
)

router = APIRouter()
wur_radd_alerts_versions: Type[Versions] = get_versions_enum(
    "wur_radd_alerts", TileCacheType.raster_tile_cache
)


@router.get(
    "/wur_radd_alerts/{version}/dynamic/{z}/{x}/{y}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def gfw_radd_alerts_raster_tile(
    *,
    version: get_versions_enum(
        "wur_radd_alerts", TileCacheType.raster_tile_cache  # noqa: F821
    ),
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
    WUR RADD alerts raster tiles.
    """
    dataset = "wur_radd_alerts"
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
            source="datalake",
        )
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "confirmed_only": confirmed_only,
        }
        query_hash = hash_query_params(params)

        return await get_cached_response(payload, query_hash, background_tasks)
