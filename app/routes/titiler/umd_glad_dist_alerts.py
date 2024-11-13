import os
from datetime import date
from typing import Optional, Tuple

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, Query, Response
from rio_tiler.io import COGReader
from titiler.core.resources.enums import ImageType
from titiler.core.utils import render_image

from ...models.enumerators.titiler import AlertConfidence, RenderType
from ...settings.globals import GLOBALS
from .. import DATE_REGEX, raster_xyz
from .algorithms.dist_alerts import DISTAlerts
from .readers import AlertsReader

DATA_LAKE_BUCKET = os.environ.get("DATA_LAKE_BUCKET")

router = APIRouter()

DATASET = "umd_glad_dist_alerts"

today = date.today()


@router.get(
    f"/{DATASET}/{{version}}/dynamic/{{z}}/{{x}}/{{y}}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
@router.get(
    "/{dataset}/{version}/titiler/{z}/{x}/{y}.png",  # for testing datasets - hidden from docs.
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
    include_in_schema=False,
)
async def glad_dist_alerts_raster_tile(
    *,
    dataset: str = DATASET,
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
        RenderType.encoded,
        description=(
            "Render true color or encoded tiles. Encoded tiles have the alert "
            "date, confidence and intensity (value for use in alpha/transparency channel to fade out isolated alert pixels at low zoom levels) "
            "packed in the image RGB channels for front-end interactive use, "
            "such as date filtering with supported technologies. "
            "Decoding instructions: Alert Date is calculated as `red * 255 + green`, "
            "representing days since 2020-12-31. Confidence is calculated as `floor(blue / 100)`, "
            "with values of `2` (high) or `1` (low). Intensity is calculated as `mod(blue, 100)`, "
            "with a maximum value of `55`. "
            "For example, a pixel RGB value of `(3, 26, 255)` would decode to: "
            "**alert date**: `3 * 255 + 26 = 791` (or 2023-03-02), "
            "**confidence**: `floor(255, 100) = 2` (high), and "
            "**intensity**: `mod(255, 100) = 55`"
        ),
    ),
    alert_confidence: Optional[AlertConfidence] = Query(
        AlertConfidence.low,
        description="Show alerts that are at least of this confidence level",
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
    """UMD GLAD DIST alerts raster tiles."""

    tile_x, tile_y, zoom = xyz
    bands = ["default", "intensity"]
    folder: str = f"s3://{DATA_LAKE_BUCKET}/{dataset}/{version}/raster/epsg-4326/cog"
    with AlertsReader(input=folder) as reader:
        # NOTE: the bands in the output `image_data` array will be in the order of
        # the input `bands` list
        image_data = reader.tile(tile_x, tile_y, zoom, bands=bands)

    dist_alert = DISTAlerts(
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
            dist_alert.tree_cover_density_data = reader.tile(tile_x, tile_y, zoom)

    if tree_cover_height_threshold:
        filter_dataset = filter_datasets["tree_cover_height"]
        with COGReader(
            f"s3://{DATA_LAKE_BUCKET}/{filter_dataset['dataset']}/{filter_dataset['version']}/raster/epsg-4326/cog/default.tif"
        ) as reader:
            dist_alert.tree_cover_height_data = reader.tile(tile_x, tile_y, zoom)

    if tree_cover_loss_threshold:
        filter_dataset = filter_datasets["tree_cover_loss"]
        with COGReader(
            f"s3://{DATA_LAKE_BUCKET}/{filter_dataset['dataset']}/{filter_dataset['version']}/raster/epsg-4326/cog/default.tif"
        ) as reader:
            dist_alert.tree_cover_loss_data = reader.tile(tile_x, tile_y, zoom)

    processed_image = dist_alert(image_data)

    content, media_type = render_image(
        processed_image,
        output_format=ImageType("png"),
        add_mask=False,
    )

    return Response(content, media_type=media_type)
