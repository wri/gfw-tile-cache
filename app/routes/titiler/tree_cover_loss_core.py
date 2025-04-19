"""Function for generating Tree Cover Loss and Tree Cover Loss from Fires
raster tiles."""

import os
from typing import Optional, Tuple, Type

from fastapi import Response
from fastapi.logger import logger
from rio_tiler.io import COGReader
from titiler.core.algorithm import BaseAlgorithm
from titiler.core.resources.enums import ImageType
from titiler.core.utils import render_image

from ...models.enumerators.titiler import RenderType
from ...settings.globals import GLOBALS
from .readers import AlertsReader

DATA_LAKE_BUCKET = os.environ.get("DATA_LAKE_BUCKET")


async def tree_cover_loss_core(
    *,
    dataset: str,
    version: str,
    algorithm: Type[BaseAlgorithm],
    xyz: Tuple[int, int, int],
    start_year: Optional[int],
    end_year: Optional[int],
    render_type: RenderType,
    tcd: Optional[int],
    bands: list[str] = ["default", "intensity"],
) -> Response:
    tile_x, tile_y, zoom = xyz
    folder: str = f"s3://{DATA_LAKE_BUCKET}/{dataset}/{version}/raster/epsg-4326/cog"

    with AlertsReader(input=folder) as reader:
        image_data = reader.tile(tile_x, tile_y, zoom, bands=bands)

    tree_cover_loss = algorithm(
        start_year=start_year,
        end_year=end_year,
        render_type=render_type,
        tree_cover_density_threshold=tcd,
        zoom=zoom,
    )

    filter_datasets = GLOBALS.tree_cover_loss_filters
    filter_dataset = filter_datasets["tree_cover_density"]

    if tcd is not None:
        with COGReader(
            f"s3://{DATA_LAKE_BUCKET}/{filter_dataset['dataset']}/{filter_dataset['version']}/raster/epsg-4326/cog/default.tif"
        ) as reader:
            if reader.tile_exists(tile_x, tile_y, zoom):
                tree_cover_loss.tree_cover_density_data = reader.tile(
                    tile_x, tile_y, zoom
                )
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
