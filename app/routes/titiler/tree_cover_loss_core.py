"""Function for generating Tree Cover Loss and Tree Cover Loss from Fires
raster tiles."""

import os
from typing import Optional, Tuple, Type

from fastapi import Response, Query
from titiler.core.algorithm import BaseAlgorithm
from titiler.core.resources.enums import ImageType
from titiler.core.utils import render_image

from ...models.enumerators.titiler import RenderType, TCLTreeCoverDensityThreshold
from .readers import AlertsReader

DATA_LAKE_BUCKET = os.environ.get("DATA_LAKE_BUCKET")


async def tree_cover_loss_core(
    dataset: str,
    version: str,
    algorithm: Type[BaseAlgorithm],
    xyz: Tuple[int, int, int],
    start_year: Optional[int],
    end_year: Optional[int],
    render_type: RenderType,
    tcd: Optional[TCLTreeCoverDensityThreshold] = Query(
        None,
        description="Show tree cover loss in pixels with tree cover density (in percent) greater than or equal to this threshold. `umd_tree_cover_density_2000` is used for this masking."
    ),
    bands: list[str] = ["default", "intensity"],
) -> Response:
    tile_x, tile_y, zoom = xyz
    folder: str = f"s3://{DATA_LAKE_BUCKET}/{dataset}/{version}/raster/epsg-4326/cog"

    if tcd is not None:
        bands = [f"year__tcd{tcd}_2000", f"intensity__tcd{tcd}_2000"]
    else: # tcd is None
        bands = ["default", "intensity"]

    with AlertsReader(input=folder) as reader:
        image_data = reader.tile(tile_x, tile_y, zoom, bands=bands)

    tree_cover_loss = algorithm(
        start_year=start_year,
        end_year=end_year,
        render_type=render_type,
        tree_cover_density_threshold=tcd,
        zoom=zoom,
    )

    processed_image = tree_cover_loss(image_data)
    content, media_type = render_image(
        processed_image,
        output_format=ImageType("png"),
        add_mask=False,
    )

    return Response(content, media_type=media_type)
