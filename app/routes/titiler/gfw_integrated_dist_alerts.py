import os
from typing import Optional, Tuple

from fastapi import APIRouter, Depends, Query, Response, Path
from rio_tiler.io import COGReader
from titiler.core.resources.enums import ImageType
from titiler.core.utils import render_image

from ...models.enumerators.titiler import IntegratedAlertConfidence, RenderType
from ...settings.globals import GLOBALS
from .. import DATE_REGEX, raster_xyz
from .algorithms.integrated_alerts import IntegratedAlerts
from .readers import AlertsReader

DATA_LAKE_BUCKET = os.environ.get("DATA_LAKE_BUCKET")

router = APIRouter()

dataset = "gfw_integrated_dist_alerts"

# We don't set a fixed set of versions that can be used, since we want to be able
# to serve any new gfw_integrated_dist_alerts version created since this server started.


@router.get(
    f"/{dataset}/{{version}}/default/{{z}}/{{x}}/{{y}}.png",
    response_class=Response,
    response_description="PNG Raster Tile",
)
@router.get(
    f"/{dataset}/{{version}}/dynamic/{{z}}/{{x}}/{{y}}.png",
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
    tree_cover_density_threshold: Optional[int] = Query(
        None,
        ge=0,
        le=100,
        description="Show alerts in pixels with tree cover density (in percent) greater than or equal to this threshold. `umd_tree_cover_density_2010` is used for this masking.",
    ),
    tree_cover_height_threshold: Optional[int] = Query(
        None,
        description="Show alerts in pixels with tree cover height (in meters) greater than or equal to this threshold. `umd_tree_cover_height_2020` dataset in the API is used for this masking.",
    ),
    tree_cover_loss_threshold: Optional[int] = Query(
        None,
        ge=2021,
        description="""This filter is to be used in conjunction with `tree_cover_density_threshold` and `tree_cover_height_threshold` filters to detect only alerts in forests, by masking out pixels that have had tree cover loss prior to the alert.""",
    ),
) -> Response:
    """GFW Integrated Disturbance Alerts raster tiles."""

    tile_x, tile_y, zoom = xyz

    # These VRTs for the split int-dist COGs are created in the datapump by commands
    # like:
    # 
    # gdalbuildvrt intdist.vrt /vsis3/gfw-data-lake/gfw_integrated_dist_alerts/v20260228/raster/epsg-4326/cog/nonoverlap.tif /vsis3/gfw-data-lake/gfw_integrated_dist_alerts/v20260228/raster/epsg-4326/cog/overlap.tif
    #
    # gdalbuildvrt intdistintensity.vrt /vsis3/gfw-data-lake/gfw_integrated_dist_alerts/v20260228/raster/epsg-4326/cog/nonoverlapintensity.tif /vsis3/gfw-data-lake/gfw_integrated_dist_alerts/v20260228/raster/epsg-4326/cog/overlapintensity.tif
    bands = ["intdist.vrt", "intdistintensity.vrt"]

    folder: str = f"s3://{DATA_LAKE_BUCKET}/{dataset}/{version}/raster/epsg-4326/cog"
    with AlertsReader(input=folder, default_band=bands[0]) as reader:
        image_data = reader.tile(tile_x, tile_y, zoom, bands=bands)

    int_dist_alert = IntegratedAlerts(
        start_date=start_date,
        end_date=end_date,
        render_type=render_type,
        alert_confidence=alert_confidence,
        tree_cover_density_mask=tree_cover_density_threshold,
        tree_cover_height_mask=tree_cover_height_threshold,
        tree_cover_loss_mask=tree_cover_loss_threshold,
    )

    filter_datasets = GLOBALS.dist_alerts_forest_filters
    if tree_cover_density_threshold:
        filter_dataset = filter_datasets["tree_cover_density"]
        with COGReader(
            f"s3://{DATA_LAKE_BUCKET}/{filter_dataset['dataset']}/{filter_dataset['version']}/raster/epsg-4326/cog/default.tif"
        ) as reader:
            int_dist_alert.tree_cover_density_data = reader.tile(tile_x, tile_y, zoom)

    if tree_cover_height_threshold:
        filter_dataset = filter_datasets["tree_cover_height"]
        with COGReader(
            f"s3://{DATA_LAKE_BUCKET}/{filter_dataset['dataset']}/{filter_dataset['version']}/raster/epsg-4326/cog/default.tif"
        ) as reader:
            int_dist_alert.tree_cover_height_data = reader.tile(tile_x, tile_y, zoom)

    if tree_cover_loss_threshold:
        filter_dataset = filter_datasets["tree_cover_loss"]
        with COGReader(
            f"s3://{DATA_LAKE_BUCKET}/{filter_dataset['dataset']}/{filter_dataset['version']}/raster/epsg-4326/cog/default.tif"
        ) as reader:
            int_dist_alert.tree_cover_loss_data = reader.tile(tile_x, tile_y, zoom)

    processed_image = int_dist_alert(image_data)

    content, media_type = render_image(
        processed_image,
        output_format=ImageType("png"),
        add_mask=False,
    )

    return Response(content, media_type=media_type)
