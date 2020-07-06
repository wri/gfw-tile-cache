from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import ORJSONResponse

from ...crud.async_db.vector_tiles import nasa_viirs_fire_alerts
from ...crud.async_db.vector_tiles.filters import (
    contextual_filter,
    date_filter,
    geometry_filter,
)
from ...crud.async_db.vector_tiles.max_date import get_max_date
from ...error import RecordNotFoundError
from ...models.enumerators.dynamic_enumerators import Versions, get_dynamic_versions
from ...models.pydantic.nasa_viirs_fire_alerts import MaxDateResponse
from ...responses import VectorTileResponse
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
    if version == "latest":
        raise HTTPException(
            status_code=400,
            detail="You must list version name explicitly for this operation.",
        )
    return version


@router.get(
    "/nasa_viirs_fire_alerts/{version}/dynamic/{z}/{x}/{y}.pbf",
    response_class=VectorTileResponse,
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
) -> VectorTileResponse:
    """
    NASA VIIRS fire alerts vector tiles.
    This dataset holds the full archive of NASA VIIRS fire alerts, starting in 2012. Latest version is updated daily.
    Check `Max Date` endpoint to retrieve latest date in dataset.
    You can query fire alerts for any time period of up to 90 days. By default, the last 7 days are displayed.
    Use additional query parameters to further filter alerts.
    Vector tiles for zoom level 6 and lower will aggregate adjacent alerts into a single point.
    """
    bbox, _, extent = bbox_z
    validate_dates(start_date, end_date, force_date_range)

    filters = [
        await geometry_filter(geostore_id, bbox),
        nasa_viirs_fire_alerts.confidence_filter(high_confidence_only),
        date_filter("alert__date", start_date, end_date),
    ] + contextual_filter(**contextual_filters)

    # Remove empty filters
    filters = [f for f in filters if f is not None]

    return await nasa_viirs_fire_alerts.get_aggregated_tile(
        version, bbox, extent, include_attribute, *filters
    )


@router.get(
    "/nasa_viirs_fire_alerts/{version}/max_alert__date",
    response_class=ORJSONResponse,
    response_model=MaxDateResponse,
    response_description="Max alert date in selected dataset",
    deprecated=True,
    tags=["Dynamic Vector Tiles"],
)
async def max_date(
    *, version: str = Depends(nasa_viirs_fire_alerts_version),
) -> MaxDateResponse:
    """
    Retrieve max alert date for NASA VIIRS fire alerts for a given version
    """
    try:
        data = await get_max_date(version)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return MaxDateResponse(data=data)
