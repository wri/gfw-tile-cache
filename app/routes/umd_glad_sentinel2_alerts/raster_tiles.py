from typing import Optional, Tuple

from aenum import Enum, extend_enum
from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query, Response

from ...crud.sync_db.tile_cache_assets import get_versions
from ...models.enumerators.tile_caches import TileCacheType
from .. import DATE_REGEX, optional_implementation_dependency, raster_xyz
from ..dynamic_deforestation_alerts_tile import get_dynamic_deforestation_alert_tile

router = APIRouter()

dataset = "umd_glad_sentinel2_alerts"


class UmdGladSentinel2Versions(str, Enum):
    """UMD Glad Alerts versions. When using `latest` call will be redirected (307) to version tagged as latest."""

    latest = "latest"


_versions = get_versions(dataset, TileCacheType.raster_tile_cache)
for _version in _versions:
    extend_enum(UmdGladSentinel2Versions, _version, _version)


@router.get(
    f"/{dataset}/{{version}}/dynamic/{{z}}/{{x}}/{{y}}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def umd_glad_alerts_raster_tile(
    *,
    version: UmdGladSentinel2Versions = Path(
        ..., description=UmdGladSentinel2Versions.__doc__
    ),
    xyz: Tuple[int, int, int] = Depends(raster_xyz),
    start_date: Optional[str] = Query(
        None,
        regex=DATE_REGEX,
        description="Only show alerts for given date and after",
    ),
    end_date: Optional[str] = Query(
        None, regex=DATE_REGEX, description="Only show alerts until given date."
    ),
    confirmed_only: Optional[bool] = Query(
        None, description="Only show confirmed alerts"
    ),
    implementation: str = Depends(optional_implementation_dependency),
    background_tasks: BackgroundTasks,
) -> Response:
    """
    UMD GLAD Sentinel 2 alerts raster tiles.
    """

    return await get_dynamic_deforestation_alert_tile(
        dataset,
        version,
        implementation,
        xyz,
        start_date,
        end_date,
        confirmed_only,
        background_tasks,
    )
