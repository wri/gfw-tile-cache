import os
from typing import Optional, Tuple

from aenum import Enum, extend_enum
from fastapi import APIRouter, Depends, Query, Response
from fastapi.logger import logger
from rio_tiler.io import COGReader
from titiler.core.resources.enums import ImageType
from titiler.core.utils import render_image

from ...crud.sync_db.tile_cache_assets import get_versions
from ...models.enumerators.tile_caches import TileCacheType
from ...models.enumerators.titiler import RenderType
from .. import raster_xyz
from ...settings.globals import GLOBALS
from .algorithms.tree_cover_loss import TreeCoverLoss
from .readers import AlertsReader

DATA_LAKE_BUCKET = os.environ.get("DATA_LAKE_BUCKET")

router = APIRouter()

DATASET = "umd_tree_cover_loss"

class UmdTreeCoverLossVersions(str, Enum):
    latest = "v1.11"

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
    start_year: Optional[int] = Query(2001, ge=2001, le=2022, description="Only show loss for given year and after"),
    end_year: Optional[int] = Query(2023, ge=2002, le=2023, description="Only show loss until given year."),
    style: RenderType = Query(RenderType.encoded, description="Render true color or encoded tiles"),
    tcd: Optional[int] = Query(None, ge=0, le=100)
) -> Response:
    """UMD Tree Cover Loss raster tiles."""

    tile_x, tile_y, zoom = xyz
    bands = ["default", "intensity"]
    folder: str = f"s3://{DATA_LAKE_BUCKET}/{DATASET}/{version}/raster/epsg-4326/cog"
    with AlertsReader(input=folder) as reader:
        image_data = reader.tile(tile_x, tile_y, zoom, bands=bands)  # Single band for lossyear

    tree_cover_loss = TreeCoverLoss(
        start_year=start_year,
        end_year=end_year,
        render_type=style,
        tree_cover_density_threshold=tcd,
        zoom=zoom
    )

    filter_datasets = GLOBALS.tree_cover_loss_filters
    filter_dataset = filter_datasets["tree_cover_density"]

    # Skip if no TCD threshold is set
    if tcd is not None:
        with COGReader(f"s3://{DATA_LAKE_BUCKET}/{filter_dataset['dataset']}/{filter_dataset['version']}/raster/epsg-4326/cog/default.tif") as reader:
            if reader.tile_exists(tile_x, tile_y, zoom):
                tree_cover_loss.tree_cover_density_data = reader.tile(tile_x, tile_y, zoom)
            else:
                logger.warning(f"TCD tile does not exist at {tile_x}, {tile_y}, {zoom}")
                tree_cover_loss.tree_cover_density_data = None

    processed_image = tree_cover_loss(image_data)
    content, media_type = render_image(
        processed_image,
        output_format=ImageType("png"),
        add_mask=False,
    )

    return Response(content, media_type=media_type)
