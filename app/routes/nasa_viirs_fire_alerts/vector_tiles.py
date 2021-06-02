from typing import List, Optional, Tuple
from uuid import UUID

from aenum import Enum, extend_enum
from asyncpg import QueryCanceledError
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from fastapi.responses import ORJSONResponse

from ...crud.async_db.vector_tiles import nasa_viirs_fire_alerts
from ...crud.async_db.vector_tiles.filters import (
    contextual_filter,
    date_filter,
    geometry_filter,
)
from ...crud.async_db.vector_tiles.max_date import get_max_date
from ...crud.sync_db.tile_cache_assets import get_versions
from ...errors import RecordNotFoundError
from ...models.enumerators.geostore import GeostoreOrigin
from ...models.enumerators.tile_caches import TileCacheType
from ...models.enumerators.versions import Versions
from ...models.pydantic.nasa_viirs_fire_alerts import MaxDateResponse
from ...responses import VectorTileResponse
from ...routes import DATE_REGEX, Bounds, validate_dates, vector_xyz
from . import (
    default_end,
    default_start,
    include_attributes,
    nasa_viirs_fire_alerts_filters,
)

router = APIRouter()

dataset = "nasa_viirs_fire_alerts"


class NasaViirsVersions(str, Enum):
    """NASA Viirs Fire Alerts versions. When using `latest` call will be redirected (307) to version tagged as latest."""

    latest = "latest"


_versions = get_versions(dataset, TileCacheType.dynamic_vector_tile_cache)
for _version in _versions:
    extend_enum(NasaViirsVersions, _version, _version)


async def nasa_viirs_fire_alerts_version(
    version: NasaViirsVersions = Path(..., description=NasaViirsVersions.__doc__),
) -> Versions:
    if version == "latest":
        raise HTTPException(
            status_code=400,
            detail="You must list version name explicitly for this operation.",
        )
    return version


@router.get(
    f"/{dataset}/{{version}}/dynamic/{{z}}/{{x}}/{{y}}.pbf",
    response_class=VectorTileResponse,
    tags=["Dynamic Vector Tiles"],
    response_description="PBF Vector Tile",
)
async def nasa_viirs_fire_alerts_tile(
    response: Response,
    version: NasaViirsVersions = Path(..., description=NasaViirsVersions.__doc__),
    bbox_z: Tuple[Bounds, int, int] = Depends(vector_xyz),
    geostore_id: Optional[UUID] = Query(
        None, description="Only show fire alerts within selected geostore area"
    ),
    geostore_origin: GeostoreOrigin = Query(
        "gfw", description="Origin service of geostore ID"
    ),
    start_date: str = Query(
        default_start(),
        regex=DATE_REGEX,
        description="Only show alerts for given date and after",
    ),
    end_date: str = Query(
        default_end(),
        regex=DATE_REGEX,
        description="Only show alerts until given date. End date cannot be in the future.",
    ),
    force_date_range: Optional[bool] = Query(
        False,
        description="Bypass the build in limitation to query more than 90 days at a time. Use cautiously!",
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
    validate_dates(start_date, end_date, default_end(), force_date_range)

    filters = [
        await geometry_filter(geostore_id, bbox, geostore_origin),
        nasa_viirs_fire_alerts.confidence_filter(high_confidence_only),
        date_filter("alert__date", start_date, end_date),
    ] + contextual_filter(**contextual_filters)

    # Remove empty filters
    filters = [f for f in filters if f is not None]

    # If one of the default dates is used, we cannot cache the response for long,
    # as content might change after next update. For non-default values we can be certain,
    # that response will always be the same b/c we only add newer dates
    # and users are not allowed to query future dates
    if start_date == default_start() or end_date == default_end():
        response.headers["Cache-Control"] = "max-age=7200"  # 2h
    else:
        response.headers["Cache-Control"] = "max-age=31536000"  # 1 year

    try:
        tile = await nasa_viirs_fire_alerts.get_aggregated_tile(
            version, bbox, extent, include_attribute, filters
        )
    except QueryCanceledError:
        raise HTTPException(
            status_code=524,
            detail="A timeout occurred while processing the request. Request canceled.",
        )
    else:
        return tile


@router.get(
    f"/{dataset}/{{version}}/max_alert__date",
    response_class=ORJSONResponse,
    response_model=MaxDateResponse,
    response_description="Max alert date in selected dataset",
    deprecated=True,
    tags=["Dynamic Vector Tiles"],
)
async def max_date(
    response: Response,
    version: NasaViirsVersions = Path(..., description=NasaViirsVersions.__doc__),
) -> MaxDateResponse:
    """
    Retrieve max alert date for NASA VIIRS fire alerts for a given version
    """
    try:
        data = await get_max_date(version)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))

    response.headers["Cache-Control"] = "max-age=900"  # 15min
    return MaxDateResponse(data=data)
