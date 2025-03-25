import os
from typing import Tuple, Optional

from aenum import Enum, extend_enum
from fastapi import APIRouter, Depends, Query, Response
from rio_tiler.io import COGReader
from rio_tiler.models import ImageData
from titiler.core.resources.enums import ImageType
from titiler.core.utils import render_image

from ...crud.sync_db.tile_cache_assets import get_versions
from ...models.enumerators.tile_caches import TileCacheType
from .. import raster_xyz
from ...settings.globals import GLOBALS
from .algorithms.carbon_gross_removals import CarbonGrossRemovals
from .readers import AlertsReader

DATA_LAKE_BUCKET = os.environ.get("DATA_LAKE_BUCKET")

router = APIRouter()

dataset = "gfw_forest_carbon_gross_removals"


class GfwForestCarbonGrossRemovals(str, Enum):
    latest = "v20240308"


_versions = get_versions(dataset, TileCacheType.cog)
for _version in _versions:
    extend_enum(GfwForestCarbonGrossRemovals, _version, _version)


@router.get(
    f"/{dataset}/{{version}}/dynamic/{{z}}/{{x}}/{{y}}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def global_forest_carbon_gross_removals_raster_tile(
    *,
    version: GfwForestCarbonGrossRemovals,
    xyz: Tuple[int, int, int] = Depends(raster_xyz),
    tree_cover_density_threshold: int = Query(
        ge=30,
        le=100,
        description="Show data in pixels with tree cover density (in percent) greater than or equal to this threshold. `umd_tree_cover_density_2000` is used for this masking.",
    )
) -> Response:
    """Forest Carbon Gross Removals raster tiles."""

    tile_x, tile_y, zoom = xyz
    bands = ["removals", "intensity"]
    folder: str = f"s3://{DATA_LAKE_BUCKET}/{dataset}/{version}/raster/epsg-4326/cog"
    with AlertsReader(input=folder, default_band="removals") as reader:
        # NOTE: the bands in the output `image_data` array will be in the order of
        # the input `bands` list
        image_data = reader.tile(tile_x, tile_y, zoom, bands=bands)

    carbon_gross_removals = CarbonGrossRemovals(
        tree_cover_density_mask=tree_cover_density_threshold,
        tree_cover_gain_from_height_mask=0,
        mangrove_stock_2000_mask=0.0,
    )

    filter_datasets = GLOBALS.carbon_flux_filters

    for filter_name, details in filter_datasets.items():
        with COGReader(
            f"s3://{DATA_LAKE_BUCKET}/{details['dataset']}/{details['version']}/raster/epsg-4326/cog/default.tif"
        ) as reader:
            filter_data: Optional[ImageData] = None

            if reader.tile_exists(tile_x, tile_y, zoom):
                filter_data = reader.tile(tile_x, tile_y, zoom)
            else:
                print(f"Non-existent tile for filter {filter_name} at z={zoom}, x={tile_x}, y={tile_y}")

            setattr(
                carbon_gross_removals,
                f"{filter_name}_data",
                filter_data
            )

    processed_image = carbon_gross_removals(image_data)

    content, media_type = render_image(
        processed_image,
        output_format=ImageType("png"),
        add_mask=False,
    )

    return Response(content, media_type=media_type)
