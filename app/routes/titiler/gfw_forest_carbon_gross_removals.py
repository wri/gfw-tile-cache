import os
from typing import Tuple, Optional

from aenum import Enum, extend_enum
from fastapi import APIRouter, Depends, Query, Response
from titiler.core.resources.enums import ImageType
from titiler.core.utils import render_image

from ...crud.sync_db.tile_cache_assets import get_versions
from ...models.enumerators.tile_caches import TileCacheType
from ...models.enumerators.titiler import TreeCoverDensityThreshold
from .. import raster_xyz
from .algorithms.carbon_gross_removals import CarbonGrossRemovals
from .readers import AlertsReader

DATA_LAKE_BUCKET = os.environ.get("DATA_LAKE_BUCKET")

router = APIRouter()

dataset = "gfw_forest_carbon_gross_removals"


class GfwForestCarbonGrossRemovals(str, Enum):
    latest = "v20260327"


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
    tree_cover_density_threshold: Optional[TreeCoverDensityThreshold] = Query(
        TreeCoverDensityThreshold.tcd_30,
        description="Show gross removals in pixels with tree cover density (in percent) greater than or equal to this threshold. `umd_tree_cover_density_2000` is used for this masking.",
    )
) -> Response:
    """Forest Carbon Gross Removals raster tiles."""

    tile_x, tile_y, zoom = xyz
    bands = [
        f"emission_tcd_{tree_cover_density_threshold}",
        f"intensity_tcd_{tree_cover_density_threshold}",
    ]
    folder: str = f"s3://{DATA_LAKE_BUCKET}/{dataset}/{version}/raster/epsg-4326/cog"
    with AlertsReader(input=folder, default_band=bands[0]) as reader:
        # NOTE: the bands in the output `image_data` array will be in the order of
        # the input `bands` list
        image_data = reader.tile(
            tile_x, tile_y, zoom, bands=bands
        )

    processed_image = CarbonGrossRemovals()(image_data)

    content, media_type = render_image(
        processed_image,
        output_format=ImageType("png"),
        add_mask=False,
    )

    return Response(content, media_type=media_type)
