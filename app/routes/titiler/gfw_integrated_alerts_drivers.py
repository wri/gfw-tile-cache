import os
from typing import Optional, Tuple

from aenum import Enum, extend_enum
from fastapi import APIRouter, Depends, Query, Response
from titiler.core.resources.enums import ImageType
from titiler.core.utils import render_image

from app.routes.titiler.algorithms.integrated_alerts_drivers import IntegratedAlertsDrivers

from ...crud.sync_db.tile_cache_assets import get_latest_versions, get_versions
from ...models.enumerators.tile_caches import TileCacheType
from ...models.enumerators.titiler import IntegratedAlertConfidence, RenderType
from .. import DATE_REGEX, raster_xyz
from .readers import AlertsReader
from rio_tiler.io import COGReader

DATA_LAKE_BUCKET = os.environ.get("DATA_LAKE_BUCKET")

router = APIRouter()

dataset = "gfw_integrated_alerts"


class GfwIntegratdAlertsVersions(str, Enum):
    """GFW Integrated Alerts versions.

    When using `latest` call will be redirected (307) to version tagged
    as latest.
    """

    latest = "v20250925"


_versions = get_versions(dataset, TileCacheType.cog)
for _version in _versions:
    extend_enum(GfwIntegratdAlertsVersions, _version, _version)


@router.get(
    f"/{dataset}_drivers/{{version}}/dynamic/{{z}}/{{x}}/{{y}}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def gfw_integrated_alerts_drivers_raster_tile(
    *,
    version: GfwIntegratdAlertsVersions,
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
        if latest_version["dataset"] == "gfw_integrated_alerts":
            integrated_alerts_version = latest_version["version"]
            break

    if integrated_alerts_version is None:
        raise RuntimeError("No latest version set for gfw_integrated_alerts.")
     
    bands = ["default", "intensity"]
    folder: str = f"s3://{DATA_LAKE_BUCKET}/gfw_integrated_alerts/{integrated_alerts_version}/raster/epsg-4326/cog"
    with AlertsReader(input=folder) as reader:
        tile_x, tile_y, zoom = xyz
        image_data = reader.tile(tile_x, tile_y, zoom, bands=bands)

    integrated_alerts_drivers = IntegratedAlertsDrivers(
        start_date=start_date,
        end_date=end_date,
        render_type=render_type,
        alert_confidence=alert_confidence,
    )

    with COGReader(
        f"s3://{DATA_LAKE_BUCKET}/wur_integration_alert_drivers_class/{version}/raster/epsg-4326/cog/class.tif"
    ) as reader:
        if reader.tile_exists(tile_x, tile_y, zoom):
            integrated_alerts_drivers.alert_drivers = reader.tile(tile_x, tile_y, zoom).data[0]
        else:
            print("Non-existent tile, wur_integration_alert_drivers_class")
            integrated_alerts_drivers.alert_drivers = None

    processed_image = integrated_alerts_drivers(image_data)

    content, media_type = render_image(
        processed_image,
        output_format=ImageType("png"),
        add_mask=False,
    )

    return Response(content, media_type=media_type)
