from datetime import datetime
from typing import Optional, Tuple

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response

from ...models.enumerators.attributes import TcdEnum
from ...models.enumerators.tile_caches import TileCacheType
from ...models.enumerators.versions import get_versions_enum
from .. import optional_implementation_dependency, raster_xyz
from ..raster_tiles import (
    get_cached_response,
    get_dynamic_raster_tile,
    hash_query_params,
)

router = APIRouter()


@router.get(
    "/umd_tree_cover_loss/{version}/dynamic/{z}/{x}/{y}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def umd_tree_cover_loss_raster_tile(
    *,
    version: get_versions_enum(
        "umd_tree_cover_loss", TileCacheType.raster_tile_cache  # noqa: F821
    ),
    xyz: Tuple[int, int, int] = Depends(raster_xyz),
    start_year: Optional[int] = Query(
        None, description="Start Year.", ge=2000, le=datetime.now().year - 1
    ),
    end_year: Optional[int] = Query(
        None, description="End Year.", ge=2000, le=datetime.now().year - 1
    ),
    tcd: TcdEnum = Query(TcdEnum.thirty, description="Tree Cover Density threshold."),
    implementation: str = Depends(optional_implementation_dependency),
    background_tasks: BackgroundTasks,
) -> Response:
    """
    UMD tree cover loss raster tile.
    """

    dataset = "umd_tree_cover_loss"
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
            implementation=f"tcd_{tcd}",
            start_year=start_year,
            end_year=end_year,
            filter_type="annual_loss",
        )

        params = {"start_year": start_year, "end_year": end_year, "tcd": tcd}
        query_hash = hash_query_params(params)

        return await get_cached_response(payload, query_hash, background_tasks)
