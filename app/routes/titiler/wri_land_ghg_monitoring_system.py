import os
from typing import Tuple

from cogeo_mosaic.backends import MosaicBackend
from cogeo_mosaic.errors import NoAssetFoundError
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from rio_tiler.errors import EmptyMosaicError, TileOutsideBounds
from rio_tiler.io import COGReader
from rio_tiler.models import ImageData
from titiler.core.resources.enums import ImageType
from titiler.core.utils import render_image

from ...models.enumerators.titiler import LgmsFluxType, LgmsLayer
from ...models.pydantic.lgms import LgmsAsset, UnsupportedLayerFlux, resolve_assets
from ...utils.rasters import sum_tiles
from .. import raster_xyz
from .algorithms.ghg_flux import GhgFlux

DATA_LAKE_BUCKET = os.environ.get("DATA_LAKE_BUCKET")

router = APIRouter()

dataset = "wri_land_ghg_monitoring_system"
VERSION = "v1.0.3"

COG_FOLDER = f"s3://{DATA_LAKE_BUCKET}/{dataset}/{VERSION}/raster/epsg-4326/cog"


@router.get(
    f"/{dataset}/{VERSION}/dynamic/{{z}}/{{x}}/{{y}}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
def wri_land_ghg_monitoring_system_raster_tile(
    *,
    xyz: Tuple[int, int, int] = Depends(raster_xyz),
    layer: LgmsLayer = Query(..., description="Sector to render"),
    flux_type: LgmsFluxType = Query(..., description="Flux type to render"),
) -> Response:
    """Land GHG Monitoring System (2016-2024 average) GHG flux raster tiles.

    A layer with no raster of its own is the sum of its children's rasters.
    """

    try:
        assets = resolve_assets(layer, flux_type)
    except UnsupportedLayerFlux as error:
        raise HTTPException(status_code=422, detail=str(error))

    tile_x, tile_y, zoom = xyz
    try:
        images = [read_asset(asset, tile_x, tile_y, zoom) for asset in assets]
    except (TileOutsideBounds, NoAssetFoundError, EmptyMosaicError):
        raise HTTPException(status_code=404, detail="No data for this tile")

    processed_image = GhgFlux()(sum_tiles(images))

    content, media_type = render_image(
        processed_image,
        output_format=ImageType("png"),
        add_mask=False,
    )

    return Response(content, media_type=media_type)


def read_asset(asset: LgmsAsset, tile_x: int, tile_y: int, zoom: int) -> ImageData:
    url = f"{COG_FOLDER}/{asset.file_name}"

    if asset.kind == "mosaic":
        with MosaicBackend(url) as mosaic:
            image_data, _ = mosaic.tile(tile_x, tile_y, zoom)
            return image_data

    with COGReader(url) as cog:
        return cog.tile(tile_x, tile_y, zoom)
