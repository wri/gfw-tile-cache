import os
from typing import Optional, Tuple

from aenum import Enum, extend_enum
from fastapi import APIRouter, Depends, Query, Response
from titiler.core.resources.enums import ImageType
from titiler.core.utils import render_image

from ...crud.sync_db.tile_cache_assets import get_versions
from ...models.enumerators.tile_caches import TileCacheType
from ...models.enumerators.titiler import RenderType
from .. import raster_xyz
from .algorithms.tree_cover_loss import TreeCoverLoss
from .readers import AlertsReader

DATA_LAKE_BUCKET = os.environ.get("DATA_LAKE_BUCKET")

router = APIRouter()

dataset = "umd_tree_cover_loss"

class UmdTreeCoverLossVersions(str, Enum):
    latest = "v1.11"

_versions = get_versions(dataset, TileCacheType.cog)
for _version in _versions:
    extend_enum(UmdTreeCoverLossVersions, _version, _version)

@router.get(
    f"/{dataset}/{{version}}/dynamic/{{z}}/{{x}}/{{y}}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def umd_tree_cover_loss_raster_tile(
    *,
    version: UmdTreeCoverLossVersions,
    xyz: Tuple[int, int, int] = Depends(raster_xyz),
    start_year: Optional[str] = Query(2001, description="Only show loss for given year and after"),
    end_year: Optional[str] = Query(2023, description="Only show loss until given year."),
    render_type: RenderType = Query(RenderType.encoded, description="Render true color or encoded tiles")
) -> Response:
    """UMD Tree Cover Loss raster tiles."""

    bands = ["default", "intensity"]
    folder: str = f"s3://{DATA_LAKE_BUCKET}/{dataset}/{version}/raster/epsg-4326/cog"
    with AlertsReader(input=folder) as reader:
        tile_x, tile_y, zoom = xyz
        image_data = reader.tile(tile_x, tile_y, zoom, bands=bands)  # Single band for lossyear

    processed_image = TreeCoverLoss(
        start_date=start_year,
        end_date=end_year,
        render_type=render_type,
    )(image_data)
    
    content, media_type = render_image(
        processed_image,
        output_format=ImageType("png"),
        add_mask=False,
    )

    return Response(content, media_type=media_type)
