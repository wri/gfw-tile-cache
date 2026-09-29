import os
from typing import Optional, Tuple

from fastapi import APIRouter, Depends, Query, Response, Path, HTTPException
from fastapi.logger import logger
from rio_tiler.errors import TileOutsideBounds
from titiler.core.resources.enums import ImageType
from titiler.core.utils import render_image

from app.routes.titiler.algorithms.alerts_drivers import AlertsDrivers

from ...models.enumerators.titiler import RenderType
from .. import DATE_REGEX, raster_xyz
from .readers import AlertsReader
from rio_tiler.io import COGReader

DATA_LAKE_BUCKET = os.environ.get("DATA_LAKE_BUCKET")

router = APIRouter()

drivers_class_dataset = "wur_integration_alert_drivers_class"
drivers_dataset = "wur_alert_drivers"

# We don't set a fixed set of versions that can be used, since we want to be able
# to serve any new drivers version created since this server started.

@router.get(
    f"/{drivers_dataset}/{{drivers_version}}/dynamic/{{z}}/{{x}}/{{y}}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def gfw_alerts_drivers_raster_tile(
    *,
    drivers_version: str = Path(..., description="Version name of dataset. Either 'latest' or version string beginning with 'v'"),
    xyz: Tuple[int, int, int] = Depends(raster_xyz),
    start_date: Optional[str] = Query(
        None,
        regex=DATE_REGEX,
        description="Only show alerts for given date and after",
    ),
    end_date: Optional[str] = Query(
        None, regex=DATE_REGEX, description="Only show alerts until given date."
    ),
    render_type: RenderType = Query(
        RenderType.encoded, description="Render true color or encoded tiles"
    ),
) -> Response:
    """WUR alert drivers raster tiles."""

    # drivers_dataset has the COGs with the dates in them.
    bands = ["default", "intensity"]
    folder: str = f"s3://{DATA_LAKE_BUCKET}/{drivers_dataset}/{drivers_version}/raster/epsg-4326/cog"
    with AlertsReader(input=folder) as reader:
        tile_x, tile_y, zoom = xyz
        try:
            dates_image_data = reader.tile(tile_x, tile_y, zoom, bands=bands)
        except TileOutsideBounds:
            logger.debug(f"Out of bounds on {drivers_dataset}")
            raise HTTPException(status_code=404, detail="YTile outside of bounds of this dataset")

    alerts_drivers = AlertsDrivers(
        start_date=start_date,
        end_date=end_date,
        render_type=render_type,
    )

    with COGReader(
        f"s3://{DATA_LAKE_BUCKET}/{drivers_class_dataset}/{drivers_version}/raster/epsg-4326/cog/class.tif"
    ) as reader:
        try:
            alerts_drivers.alert_drivers_class = reader.tile(tile_x, tile_y, zoom).data[0]
        except TileOutsideBounds:
            logger.debug(f"Out of bounds on {drivers_class_dataset}")
            raise HTTPException(status_code=404, detail="XTile outside of bounds of this dataset")

    processed_image = alerts_drivers(dates_image_data)

    content, media_type = render_image(
        processed_image,
        output_format=ImageType("png"),
        add_mask=False,
    )

    return Response(content, media_type=media_type)
