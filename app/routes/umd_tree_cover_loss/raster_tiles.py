from datetime import datetime
from typing import Optional, Tuple

from aenum import Enum, extend_enum
from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query, Response

from ...crud.sync_db.tile_cache_assets import get_max_zoom, get_versions
from ...models.enumerators.attributes import TcdEnum, TcdStyleEnum
from ...models.enumerators.tile_caches import TileCacheType
from .. import optional_implementation_dependency, raster_xyz
from ..raster_tiles import (
    get_cached_response,
    get_dynamic_raster_tile,
    hash_query_params,
)

router = APIRouter()

dataset = "umd_tree_cover_loss"


class UmdTclVersions(str, Enum):
    """UMD Tree Cover Loss versions. When using `latest` call will be redirected (307) to version tagged as latest."""

    latest = "latest"


_versions = get_versions(dataset, TileCacheType.raster_tile_cache)
for _version in _versions:
    extend_enum(UmdTclVersions, _version, _version)


@router.get(
    f"/{dataset}/{{version}}/dynamic/{{z}}/{{x}}/{{y}}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def umd_tree_cover_loss_raster_tile(
    *,
    version: UmdTclVersions = Path(..., description=UmdTclVersions.__doc__),
    xyz: Tuple[int, int, int] = Depends(raster_xyz),
    start_year: Optional[int] = Query(
        None, description="Start Year.", ge=2000, le=datetime.now().year - 1
    ),
    end_year: Optional[int] = Query(
        None, description="End Year.", ge=2000, le=datetime.now().year - 1
    ),
    tcd: TcdEnum = Query(TcdEnum.tcd_30, description="Tree Cover Density threshold."),
    style: Optional[TcdStyleEnum] = Query(
        None,
        description="Predefined WMTS style. "
        "This query parameter is mutually exclusive to all other query parameters.",
    ),
    implementation: str = Depends(optional_implementation_dependency),
    background_tasks: BackgroundTasks,
) -> Response:
    """
    UMD tree cover loss raster tile.
    """

    x, y, z = xyz

    payload = {
        "dataset": dataset,
        "version": version,
        "implementation": implementation,
        "x": x,
        "y": y,
        "z": z,
        "over_zoom": get_max_zoom(
            dataset, version, implementation, TileCacheType.raster_tile_cache
        ),
    }

    if implementation:
        return await get_dynamic_raster_tile(payload, implementation, background_tasks)

    else:
        if style:
            tcd = TcdEnum[style]  # type: ignore
            start_year = None
            end_year = None

        payload.update(
            implementation=f"tcd_{tcd}",
            start_year=start_year,
            end_year=end_year,
            filter_type="annual_loss",
            over_zoom=get_max_zoom(
                dataset, version, f"tcd_{tcd}", TileCacheType.raster_tile_cache
            ),
        )

        params = {"start_year": start_year, "end_year": end_year, "tcd": tcd}
        query_hash = hash_query_params(params)

        return await get_cached_response(payload, query_hash, background_tasks)
