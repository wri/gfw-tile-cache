from typing import Optional, Tuple

from aenum import Enum, extend_enum
from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query, Response

from ...crud.sync_db.tile_cache_assets import get_versions
from ...models.enumerators.tile_caches import TileCacheType
from .. import DATE_REGEX, optional_implementation_dependency, raster_xyz
from ..dynamic_deforestation_alerts_tile import get_dynamic_deforestation_alert_tile

router = APIRouter()

dataset = "gfw_integrated_alerts"


class GFWIntegratedAlertsVersions(str, Enum):
    """GFW Integrated Alerts versions. When using `latest` call will be redirected (307) to version tagged as latest."""

    latest = "latest"


_versions = get_versions(dataset, TileCacheType.raster_tile_cache)
for _version in _versions:
    extend_enum(GFWIntegratedAlertsVersions, _version, _version)


@router.get(
    f"/{dataset}/{{version}}/dynamic/{{z}}/{{x}}/{{y}}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def gfw_integrated_alerts_raster_tile(
    *,
    version: GFWIntegratedAlertsVersions = Path(..., description=GFWIntegratedAlertsVersions.__doc__),
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
    GFW Integrated alerts raster tiles.
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
