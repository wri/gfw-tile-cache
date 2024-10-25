import os
from datetime import date
from typing import Optional, Tuple

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, Query, Response
from titiler.core.resources.enums import ImageType
from titiler.core.utils import render_image

from ...models.enumerators.titiler import AlertConfidence, RenderType
from .. import DATE_REGEX, optional_implementation_dependency, raster_xyz
from .algorithms.dist_alerts import DISTAlerts
from .readers import AlertsReader

DATA_LAKE_BUCKET = os.environ.get("DATA_LAKE_BUCKET")

router = APIRouter()

# TODO: update to the actual dataset when ready
dataset = "dan_test"

today = date.today()


@router.get(
    f"/{dataset}/{{version}}/dynamic/{{z}}/{{x}}/{{y}}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def glad_dist_alerts_raster_tile(
    *,
    version,
    xyz: Tuple[int, int, int] = Depends(raster_xyz),
    start_date: Optional[str] = Query(
        (today - relativedelta(days=180)).strftime("%Y-%m-%d"),
        regex=DATE_REGEX,
        description="Only show alerts for given date and after",
    ),
    end_date: Optional[str] = Query(
        today.strftime("%Y-%m-%d"),
        regex=DATE_REGEX,
        description="Only show alerts until given date.",
    ),
    render_type: RenderType = Query(
        RenderType.true_color, description="Render true color or encoded tiles"
    ),
    alert_confidence: Optional[bool] = Query(
        AlertConfidence.low,
        description="Show alerts that are at least of this confidence level",
    ),
    implementation: str = Depends(optional_implementation_dependency),
) -> Response:
    """UMD GLAD DIST alerts raster tiles."""

    bands = ["default", "intensity"]
    folder: str = f"s3://{DATA_LAKE_BUCKET}/{dataset}/{version}/raster/epsg-4326/cog"
    with AlertsReader(input=folder) as reader:
        tile_x, tile_y, zoom = xyz
        image_data = reader.tile(tile_x, tile_y, zoom, bands=bands)

    processed_image = DISTAlerts(
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
