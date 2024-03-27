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
    UMD Tree Cover Loss raster tile.

    There are two types of TCL tiles available here: True color tiles and encoded tiles.
    The true color tiles have been pre-rendered to appear the same way TCL appears on
    globalforestwatch.org (i.e. the tiles show pink pixels to indicate tree cover loss).
    The caveat with the true color tiles is that ANY tree cover loss over the history of
    the data is shown as a pink pixel. There's no way to filter out pixels which fall in
    or out of a range of years like there is in the map interface, because that
    information is no longer in the data!
    The encoded tiles, on the other hand, still contain the year information but are not
    ready to be displayed as-is. They can/need to be interpreted and rendered according to
    the needs of the consumer of the data.
    Note that both types of tiles are thresholded by Tree Cover Density, which means that
    one needs to know the TCD percentage which one wants to consider necessary to
    indicate tree cover loss of interest. A small example: If one wants data which
    indicates loss in areas that have a tree cover density of 75% or more, one would
    specify a TCD of 75. The allowable thresholds can be seen below in the query
    parameters.
    So if you want

    True color tiles (i.e. pink pixels as they appear on the map at globalforestwatch.org) thresholded by tree cover density
        Specify the style query parameter
        For example: https://tiles.globalforestwatch.org/umd_tree_cover_loss/v1.10/dynamic/1/1/0.png?style=tcd_10

    True color tiles filtered by start and/or end year, thresholded by tree cover density
        Specify the tcd query parameter and optionally the start/end year
        For example: https://tiles.globalforestwatch.org/umd_tree_cover_loss/v1.10/dynamic/1/1/0.png?tcd=10&start_year=2016

    Encoded tiles, so you can filter and style on your own
        Specify the implementation query parameter
        For example: https://tiles.globalforestwatch.org/umd_tree_cover_loss/v1.10/dynamic/1/1/0.png?implementation=tcd_10

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
