from typing import Any, Dict

from fastapi import APIRouter, Depends, Path, Response

from ...crud.sync_db.tile_cache_assets import default_end, default_start
from ...models.pydantic.esri import VectorTileService
from ...routes import DATE_REGEX
from ...routes.esri_vector_tile_server import _get_vector_tile_server
from ...routes.umd_modis_burned_areas.vector_tiles import (
    dataset,
    default_duration,
    umd_modis_burned_areas_version,
)

router = APIRouter()


@router.get(
    f"/{dataset}/{{version}}/dynamic/{{start_dates}}/{{end_date}}/VectorTileServer",
    tags=["ESRI Vector Tile Service"],
    response_model=VectorTileService,
)
async def umd_modis_burned_areas_esri_vector_tile_service_dates(
    *,
    response: Response,
    version: str = Depends(umd_modis_burned_areas_version),
    start_date: str = Path(
        ...,
        regex=DATE_REGEX,
        description="Only show alerts for given date and after",
    ),
    end_date: str = Path(
        ..., regex=DATE_REGEX, description="Only show alerts until given date."
    ),
):
    """
    Mock ESRI Vector Tile Server for NASA VIIRS fire alerts.
    When using ESRI JS API, point your root.json to this URL.
    URL Parameters will be forwarded to tile cache.
    """

    fields: Dict[str, Any] = dict()

    fields["start_date"] = start_date
    fields["end_date"] = end_date

    params = [f"{key}={value}" for key, value in fields.items() if value is not None]

    query_params: str = "&".join(params)

    # If one of the default dates is used, we cannot cache the response for long,
    # as content might change after next update. For non-default values we can be certain,
    # that response will always be the same b/c we only add newer dates
    # and users are not allowed to query future dates
    if start_date == default_start(
        dataset, default_duration
    ) or end_date == default_end(dataset):
        response.headers["Cache-Control"] = "max-age=7200"  # 2h
    else:
        response.headers["Cache-Control"] = "max-age=31536000"  # 1 year

    # TODO: add scale factor to tile url
    return await _get_vector_tile_server(
        dataset, version, "dynamic", query_params, levels=3
    )


@router.get(
    f"/{dataset}/{{version}}/dynamic/VectorTileServer",
    tags=["ESRI Vector Tile Service"],
    response_model=VectorTileService,
)
async def umd_modis_burned_areas_esri_vector_tile_service(
    *,
    version: str = Depends(umd_modis_burned_areas_version),
):
    """
    Mock ESRI Vector Tile Server for NASA VIIRS fire alerts.
    When using ESRI JS API, point your root.json to this URL.
    URL Parameters will be forwarded to tile cache.
    """

    # TODO: add scale factor to tile url
    return await _get_vector_tile_server(dataset, version, "dynamic")
