import os
from typing import Optional, Tuple

from aenum import Enum, extend_enum
from fastapi import APIRouter, Depends, Query, Response

from ...crud.sync_db.tile_cache_assets import get_versions
from ...models.enumerators.tile_caches import TileCacheType
from ...models.enumerators.titiler import RenderType, TCLTreeCoverDensityThreshold
from .. import raster_xyz
from .algorithms.tree_cover_loss import TreeCoverLoss
from .tree_cover_loss_core import tree_cover_loss_core

DATA_LAKE_BUCKET = os.environ.get("DATA_LAKE_BUCKET")

router = APIRouter()

DATASET = "umd_tree_cover_loss"


class UmdTreeCoverLossVersions(str, Enum):
    latest = "latest"


_versions = get_versions(DATASET, TileCacheType.cog)
for _version in _versions:
    extend_enum(UmdTreeCoverLossVersions, _version, _version)


@router.get(
    f"/{DATASET}/{{version}}/dynamic/{{z}}/{{x}}/{{y}}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def umd_tree_cover_loss_raster_tile(
    *,
    version: UmdTreeCoverLossVersions,
    xyz: Tuple[int, int, int] = Depends(raster_xyz),
    start_year: Optional[int] = Query(
        2001, ge=2001, le=2024, description="Only show loss for given year and after"
    ),
    end_year: Optional[int] = Query(
        2025, ge=2002, le=2025, description="Only show loss until given year."
    ),
    render_type: RenderType = Query(
        RenderType.encoded, description="Render true color or encoded tiles"
    ),
    tree_cover_density_threshold: Optional[TCLTreeCoverDensityThreshold] = Query(
        None,
        description="Show tree cover loss in pixels with tree cover density (in percent) greater than or equal to this threshold. `umd_tree_cover_density_2000` is used for this masking.",
    ),
    tcd: Optional[TCLTreeCoverDensityThreshold] = Query(
        None,
        description="Same as `tree_cover_density_threshold`",
        include_in_schema=False,
    ),
) -> Response:
    """UMD Tree Cover Loss raster tiles."""

    return await tree_cover_loss_core(
        dataset="umd_tree_cover_loss",
        version=version,
        algorithm=TreeCoverLoss,
        xyz=xyz,
        start_year=start_year,
        end_year=end_year,
        render_type=render_type,
        tcd=tree_cover_density_threshold or tcd,
    )
