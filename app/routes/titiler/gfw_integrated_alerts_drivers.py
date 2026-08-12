import os
from typing import Optional, Tuple

from fastapi import APIRouter, Depends, Query, Response, Path, HTTPException
from rio_tiler.errors import TileOutsideBounds
from titiler.core.resources.enums import ImageType
from titiler.core.utils import render_image

from app.routes.titiler.algorithms.integrated_alerts_drivers import IntegratedAlertsDrivers

from ...crud.sync_db.tile_cache_assets import get_latest_versions
from ...models.enumerators.titiler import IntegratedAlertConfidence, RenderType
from .. import DATE_REGEX, raster_xyz
from .readers import AlertsReader
from rio_tiler.io import COGReader

DATA_LAKE_BUCKET = os.environ.get("DATA_LAKE_BUCKET")

router = APIRouter()

drivers_route_name = "gfw_integrated_alerts_drivers"
drivers_dataset = "wur_integration_alert_drivers_class"
integrated_alerts_dataset = "gfw_integrated_alerts"

# We don't set a fixed set of versions that can be used, since we want to be able
# to serve any new drivers version created since this server started.

@router.get(
    f"/{drivers_route_name}/{{drivers_version}}/dynamic/{{z}}/{{x}}/{{y}}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def gfw_integrated_alerts_drivers_raster_tile(
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
    alert_confidence: Optional[IntegratedAlertConfidence] = Query(
        IntegratedAlertConfidence.low,
        description="Show alerts with at least this confidence level",
    ),
) -> Response:
    """GFW Integrated Alerts raster tiles."""

    # this should be cached, get latest version of integrated alerts
    integrated_alerts_version = None

    latest_versions = get_latest_versions()
    for latest_version in latest_versions:
        if latest_version["dataset"] == integrated_alerts_dataset:
            integrated_alerts_version = latest_version["version"]
            break

    if integrated_alerts_version is None:
        raise RuntimeError("No latest version set for gfw_integrated_alerts.")

    bands = ["default", "intensity"]
    folder: str = f"s3://{DATA_LAKE_BUCKET}/{integrated_alerts_dataset}/{integrated_alerts_version}/raster/epsg-4326/cog"
    with AlertsReader(input=folder) as reader:
        tile_x, tile_y, zoom = xyz
        try:
            image_data = reader.tile(tile_x, tile_y, zoom, bands=bands)
        except TileOutsideBounds:
            raise HTTPException(status_code=404, detail="Tile outside of bounds of this dataset")

    integrated_alerts_drivers = IntegratedAlertsDrivers(
        start_date=start_date,
        end_date=end_date,
        render_type=render_type,
        alert_confidence=alert_confidence,
    )

    with COGReader(
        f"s3://{DATA_LAKE_BUCKET}/{drivers_dataset}/{drivers_version}/raster/epsg-4326/cog/class.tif"
    ) as reader:
        try:
            integrated_alerts_drivers.alert_drivers = reader.tile(tile_x, tile_y, zoom).data[0]
        except TileOutsideBounds:
            raise HTTPException(status_code=404, detail="Tile outside of bounds of this dataset")

    processed_image = integrated_alerts_drivers(image_data)

    content, media_type = render_image(
        processed_image,
        output_format=ImageType("png"),
        add_mask=False,
    )

    return Response(content, media_type=media_type)
