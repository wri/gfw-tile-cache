import os
from typing import Optional, Tuple

from fastapi import APIRouter, Depends, Query, Response, Path
from titiler.core.resources.enums import ImageType
from titiler.core.utils import render_image

from ...models.enumerators.titiler import IntegratedAlertConfidence, RenderType
from .. import DATE_REGEX, raster_xyz
from .algorithms.integrated_alerts import IntegratedAlerts
from .readers import AlertsReader

DATA_LAKE_BUCKET = os.environ.get("DATA_LAKE_BUCKET")

router = APIRouter()

# Integrated disturbance alerts are generated within the gfw_integrated_alerts Data
# API dataset, but we have a distinct route name to access them in titiler.
route_name = "gfw_integrated_dist_alerts"
dataset = "gfw_integrated_alerts"

# We don't set a fixed set of versions that can be used, since we want to be able
# to serve any new integrated_alerts version created since this server started.


@router.get(
    f"/{route_name}/{{version}}/default/{{z}}/{{x}}/{{y}}.png",
    response_class=Response,
    response_description="PNG Raster Tile",
)
@router.get(
    f"/{route_name}/{{version}}/dynamic/{{z}}/{{x}}/{{y}}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def gfw_integrated_alerts_raster_tile(
    *,
    version: str = Path(..., description="Version name of dataset. Either 'latest' or version string beginning with 'v'"),
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
    """GFW Integrated Disturbance Alerts raster tiles."""

    bands = ["intdist", "intdistintensity"]
    folder: str = f"s3://{DATA_LAKE_BUCKET}/{dataset}/{version}/raster/epsg-4326/cog"
    with AlertsReader(input=folder, default_band=bands[0]) as reader:
        tile_x, tile_y, zoom = xyz
        image_data = reader.tile(tile_x, tile_y, zoom, bands=bands)

    processed_image = IntegratedAlerts(
        start_date=start_date,
        end_date=end_date,
        render_type=render_type,
        alert_confidence=alert_confidence,
    )(image_data)

    content, media_type = render_image(
        processed_image,
        output_format=ImageType("png"),
        add_mask=False,
    )

    return Response(content, media_type=media_type)
