from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, Query, Response

from app.crud.vector_tiles.filters import (
    confidence_filter,
    contextual_filter,
    date_filter,
    geometry_filter,
)

from ...crud.vector_tiles import nasa_viirs_fire_alerts
from ...models.pydantic.dynamic_enumerators import Versions, get_dynamic_versions
from ...routes import (
    DATE_REGEX,
    DEFAULT_END,
    DEFAULT_START,
    Bounds,
    validate_dates,
    xyz,
)
from . import include_attributes, nasa_viirs_fire_alerts_filters

router = APIRouter()


async def nasa_viirs_fire_alerts_version(
    version: get_dynamic_versions("nasa_viirs_fire_alerts"),  # type: ignore
) -> Versions:

    return version


@router.get(
    "/nasa_viirs_fire_alerts/{version}/dynamic/{z}/{x}/{y}.pbf",
    response_class=Response,
    tags=["Dynamic Vector Tiles"],
    response_description="PBF Vector Tile",
)
async def nasa_viirs_fire_alerts_tile(
    version: str = Depends(nasa_viirs_fire_alerts_version),
    bbox_z: Tuple[Bounds, int, int] = Depends(xyz),
    geostore_id: Optional[str] = Query(
        None, title="Only show fire alerts within selected geostore area"
    ),
    start_date: str = Query(
        DEFAULT_START,
        regex=DATE_REGEX,
        title="Only show alerts for given date and after",
    ),
    end_date: str = Query(
        DEFAULT_END, regex=DATE_REGEX, title="Only show alerts until given date."
    ),
    force_date_range: Optional[bool] = Query(
        False,
        title="Bypass the build in limitation to query more than 90 days at a time. Use cautiously!",
    ),
    high_confidence_only: Optional[bool] = Query(
        False, title="Only show high confidence alerts"
    ),
    include_attribute: List[str] = Depends(include_attributes),
    contextual_filters: dict = Depends(nasa_viirs_fire_alerts_filters),
) -> Response:
    """
    NASA VIIRS fire alerts vector tiles.
    This dataset holds the full archive of NASA VIIRS fire alerts, starting in 2012. Latest version is updated daily.
    Check `Max Date` endpoint to retrieve latest date in dataset.
    You can query fire alerts for any time period of up to 90 days. By default, the last 7 days are displayed.
    Use additional query parameters to further filter alerts.
    Vector tiles for zoom level 6 and lower will aggregate adjacent alerts into a single point.
    """
    bbox, z, extent = bbox_z
    validate_dates(start_date, end_date, force_date_range)

    filters = [
        await geometry_filter(geostore_id, bbox),
        confidence_filter(high_confidence_only),
        date_filter(start_date, end_date),
    ] + contextual_filter(**contextual_filters)

    # Remove empty filters
    filters = [f for f in filters if f is not None]

    return await nasa_viirs_fire_alerts.get_aggregated_tile(
        version, bbox, extent, include_attribute, *filters
    )
