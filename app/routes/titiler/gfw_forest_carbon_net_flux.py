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
from .algorithms.carbon_net_flux import CarbonNetFlux
from .readers import AlertsReader

DATA_LAKE_BUCKET = os.environ.get("DATA_LAKE_BUCKET")

router = APIRouter()

dataset = "gfw_forest_carbon_net_flux"


class GfwForestCarbonNetFlux(str, Enum):
    latest = "v20240402"


_versions = get_versions(dataset, TileCacheType.cog)
for _version in _versions:
    extend_enum(GfwForestCarbonNetFlux, _version, _version)


@router.get(
    f"/{dataset}/{{version}}/dynamic/{{z}}/{{x}}/{{y}}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def global_forest_carbon_net_flux_raster_tile(
    *,
    version: GfwForestCarbonNetFlux,
    xyz: Tuple[int, int, int] = Depends(raster_xyz),
    tree_cover_density_threshold: int = Query(
        ge=30,
        le=100,
        description="Show alerts in pixels with tree cover density (in percent) greater than or equal to this threshold. `umd_tree_cover_density_2000` is used for this masking.",
    )
) -> Response:
    """Forest Carbon Net Flux raster tiles."""

    tile_x, tile_y, zoom = xyz
    bands = ["default", "intensity"]
    folder: str = f"s3://{DATA_LAKE_BUCKET}/{dataset}/{version}/raster/epsg-4326/cog"
    with AlertsReader(input=folder, default_band="default") as reader:
        # NOTE: the bands in the output `image_data` array will be in the order of
        # the input `bands` list
        image_data = reader.tile(tile_x, tile_y, zoom, bands=bands)

    carbon_net_flux = CarbonNetFlux(
        tree_cover_density_mask=tree_cover_density_threshold,
        tree_cover_gain_from_height_mask=0,
        mangrove_stock_2000_mask=0.0,
    )

    filter_datasets = GLOBALS.carbon_flux_filters

    filter_dataset = filter_datasets["tree_cover_density"]
    with COGReader(
            f"s3://{DATA_LAKE_BUCKET}/{filter_dataset['dataset']}/{filter_dataset['version']}/raster/epsg-4326/cog/default.tif"
    ) as reader:
        if reader.tile_exists(tile_x, tile_y, zoom):
            carbon_net_flux.tree_cover_density_data = reader.tile(tile_x, tile_y, zoom)
        else:
            print("Non-existent tile, tree_cover_density")
            carbon_net_flux.tree_cover_density_data = None

    filter_dataset = filter_datasets["tree_cover_gain_from_height"]
    with COGReader(
        f"s3://{DATA_LAKE_BUCKET}/{filter_dataset['dataset']}/{filter_dataset['version']}/raster/epsg-4326/cog/default.tif"
    ) as reader:
        if reader.tile_exists(tile_x, tile_y, zoom):
            carbon_net_flux.tree_cover_gain_from_height_data = reader.tile(tile_x, tile_y, zoom)
        else:
            print("Non-existent tile, tree_cover_gain_from_height")
            carbon_net_flux.tree_cover_gain_from_height_data = None

    filter_dataset = filter_datasets["mangrove_stock_2000"]
    with COGReader(
        f"s3://{DATA_LAKE_BUCKET}/{filter_dataset['dataset']}/{filter_dataset['version']}/raster/epsg-4326/cog/default.tif"
    ) as reader:
        if reader.tile_exists(tile_x, tile_y, zoom):
            carbon_net_flux.mangrove_stock_2000_data = reader.tile(tile_x, tile_y, zoom)
        else:
            print("Non-existent tile, mangrove")
            carbon_net_flux.mangrove_stock_2000_data = None

    processed_image = carbon_net_flux(image_data)

    content, media_type = render_image(
        processed_image,
        output_format=ImageType("png"),
        add_mask=False,
    )

    return Response(content, media_type=media_type)
