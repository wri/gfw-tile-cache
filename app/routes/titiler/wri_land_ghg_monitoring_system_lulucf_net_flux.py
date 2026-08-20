import os
from typing import Tuple

from cogeo_mosaic.backends import MosaicBackend
from cogeo_mosaic.errors import NoAssetFoundError
from rio_tiler.errors import EmptyMosaicError
from fastapi import APIRouter, Depends, Response
from titiler.core.resources.enums import ImageType
from titiler.core.utils import render_image

from .. import raster_xyz
from .algorithms.lulucf_net_flux import LulucfNetFlux

DATA_LAKE_BUCKET = os.environ.get("DATA_LAKE_BUCKET")

router = APIRouter()

# this doesn't actually match the dataset name in Data API/data lake which is wri_land_ghg_monitoring_system. This is a subset of that dataset.
dataset = "wri_land_ghg_monitoring_system_lulucf_net_flux"
VERSION = "v1.0.3"

MOSAIC_URL = f"s3://{DATA_LAKE_BUCKET}/wri_land_ghg_monitoring_system/{VERSION}/raster/epsg-4326/cog/mosaic.json"


@router.get(
    f"/{dataset}/{VERSION}/dynamic/{{z}}/{{x}}/{{y}}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def wri_land_ghg_monitoring_system_lulucf_net_flux_raster_tile(
    *,
    xyz: Tuple[int, int, int] = Depends(raster_xyz),
) -> Response:
    """LULUCF (2016-2024 average) net GHG flux raster tiles."""

    tile_x, tile_y, zoom = xyz
    try:
        with MosaicBackend(MOSAIC_URL) as mosaic:
            image_data, _ = mosaic.tile(tile_x, tile_y, zoom)
    except (NoAssetFoundError, EmptyMosaicError):
        return Response(b"", media_type="image/png")

    processed_image = LulucfNetFlux()(image_data)

    content, media_type = render_image(
        processed_image,
        output_format=ImageType("png"),
        add_mask=False,
    )

    return Response(content, media_type=media_type)
