from typing import Optional, Tuple

from fastapi import BackgroundTasks

from app.crud.sync_db.tile_cache_assets import get_max_zoom
from app.models.enumerators.tile_caches import TileCacheType
from app.routes.raster_tiles import (
    get_cached_response,
    get_dynamic_raster_tile,
    hash_query_params,
)


async def get_dynamic_deforestation_alert_tile(
    dataset: str,
    version: str,
    implementation: str,
    xyz: Tuple[int, int, int],
    start_date: Optional[str],
    end_date: Optional[str],
    confirmed_only: Optional[bool],
    background_tasks: BackgroundTasks,
):

    x, y, z = xyz

    payload = {
        "dataset": dataset,
        "version": version,
        "implementation": implementation,
        "x": x,
        "y": y,
        "z": z,
        "over_zoom": get_max_zoom(
            dataset, version, implementation, TileCacheType.raster_tile_cache
        ),
    }

    if implementation:
        return await get_dynamic_raster_tile(payload, implementation, background_tasks)

    else:
        payload.update(
            implementation="default",
            start_date=start_date,
            end_date=end_date,
            confirmed_only=confirmed_only,
            filter_type="deforestation_alerts",
            source="datalake",
            over_zoom=get_max_zoom(
                dataset, version, "default", TileCacheType.raster_tile_cache
            ),
        )
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "confirmed_only": confirmed_only,
        }
        query_hash = hash_query_params(params)

        return await get_cached_response(payload, query_hash, background_tasks)
