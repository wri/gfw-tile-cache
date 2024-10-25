import os
from typing import Optional, Tuple

from aenum import Enum, extend_enum
from fastapi import APIRouter, Depends, Query, Response
from titiler.core.resources.enums import ImageType
from titiler.core.utils import render_image

from ...crud.sync_db.tile_cache_assets import get_versions
from ...models.enumerators.tile_caches import TileCacheType
from ...models.enumerators.titiler import IntegratedAlertConfidence, RenderType
from .. import DATE_REGEX, optional_implementation_dependency, raster_xyz
from .algorithms.integrated_alerts import IntegratedAlerts
from .readers import AlertsReader

DATA_LAKE_BUCKET = os.environ.get("DATA_LAKE_BUCKET")

router = APIRouter()

dataset = "gfw_integrated_alerts"


class GfwIntegratdAlertsVersions(str, Enum):
    """GFW Integrated Alerts versions.

    When using `latest` call will be redirected (307) to version tagged
    as latest.
    """

    latest = "latest"


_versions = get_versions(dataset, TileCacheType.cog)
for _version in _versions:
    extend_enum(GfwIntegratdAlertsVersions, _version, _version)
# TODO: add version validation


# will turn this on when we're ready to replace tile cache service
# @router.get(
#     f"/{dataset}/{{version}}/dynamic/{{z}}/{{x}}/{{y}}.png",
#     response_class=Response,
#     tags=["Raster Tiles"],
#     response_description="PNG Raster Tile",
# )
@router.get(
    f"/{dataset}/{{version}}/titiler/{{z}}/{{x}}/{{y}}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def gfw_integrated_alerts_raster_tile(
    *,
    version,
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
    implementation: str = Depends(optional_implementation_dependency),
) -> Response:
    """GFW Integrated Alerts raster tiles."""

    bands = ["default", "intensity"]
    folder: str = f"s3://{DATA_LAKE_BUCKET}/{dataset}/{version}/raster/epsg-4326/cog"
    with AlertsReader(input=folder) as reader:
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
