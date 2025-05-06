import os
from typing import Tuple

from aenum import Enum, extend_enum
from fastapi import APIRouter, Depends, Query, Response
from rio_tiler.io import COGReader
from titiler.core.resources.enums import ImageType
from titiler.core.utils import render_image

from ...crud.sync_db.tile_cache_assets import get_versions
from ...models.enumerators.tile_caches import TileCacheType
from .. import raster_xyz
from ...settings.globals import GLOBALS
from .algorithms.tree_cover_loss_drivers import TreeCoverLossDrivers
from .readers import AlertsReader

DATA_LAKE_BUCKET = os.environ.get("DATA_LAKE_BUCKET")

router = APIRouter()

dataset = "wri_google_tree_cover_loss_drivers"


class WriTreeCoverLossDrivers(str, Enum):
    latest = "v20241224"


_versions = get_versions(dataset, TileCacheType.cog)
for _version in _versions:
    extend_enum(WriTreeCoverLossDrivers, _version, _version)


@router.get(
    f"/{dataset}/{{version}}/dynamic/{{z}}/{{x}}/{{y}}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def tree_cover_loss_drivers_raster_tile(
    *,
    version: WriTreeCoverLossDrivers,
    xyz: Tuple[int, int, int] = Depends(raster_xyz),
    tree_cover_density_threshold: int = Query(
        ge=10,
        le=100,
        description="Show drivers in pixels with tree cover density (in percent) greater than or equal to this threshold. `umd_tree_cover_density_2000` is used for this masking.",
    )
) -> Response:
    """Tree cover loss drivers raster tiles."""

    tile_x, tile_y, zoom = xyz
    bands = ["default"]
    folder: str = f"s3://{DATA_LAKE_BUCKET}/{dataset}/{version}/raster/epsg-4326/cog"
    with AlertsReader(input=folder, default_band="default") as reader:
        # NOTE: the bands in the output `image_data` array will be in the order of
        # the input `bands` list
        image_data = reader.tile(tile_x, tile_y, zoom, bands=bands)

    tree_cover_loss_drivers = TreeCoverLossDrivers(
        tree_cover_density_mask=tree_cover_density_threshold, zoom=zoom
    )

    filter_datasets = GLOBALS.tree_cover_loss_drivers_filters

    filter_dataset = filter_datasets["tree_cover_loss"]
    with COGReader(
            f"s3://{DATA_LAKE_BUCKET}/{filter_dataset['dataset']}/{filter_dataset['version']}/raster/epsg-4326/cog/intensity__tcd{tree_cover_density_threshold}_2000.tif"
    ) as reader:
        if reader.tile_exists(tile_x, tile_y, zoom):
            tree_cover_loss_drivers.tree_cover_loss_intensity_data = reader.tile(tile_x, tile_y, zoom)
        else:
            print("Non-existent tile, tree_cover_density")
            tree_cover_loss_drivers.tree_cover_intensity_data = None

    processed_image = tree_cover_loss_drivers(image_data)

    content, media_type = render_image(
        processed_image,
        output_format=ImageType("png"),
        add_mask=False,
    )

    return Response(content, media_type=media_type)
