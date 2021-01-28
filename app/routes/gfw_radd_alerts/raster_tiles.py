import io
from typing import Optional, Tuple

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query, Response
from starlette.responses import StreamingResponse

from ...models.enumerators.versions import Versions
from .. import DATE_REGEX, VERSION_REGEX, raster_xyz
from ..raster_tiles import copy_tile, get_dynamic_tile, hash_query_params

router = APIRouter()


@router.get(
    "/gfw_radd_alerts/{version}/dynamic/{z}/{x}/{y}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def gfw_radd_alerts_raster_tile(
    *,
    version: str = Path(..., description=Versions.__doc__, regex=VERSION_REGEX),
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
    background_tasks: BackgroundTasks,
) -> Response:
    """
    GFW RADD alerts raster tiles.

    Sourced from University of Wageningen and Sateligence.
    """
    dataset = "gfw_radd_alerts"
    x, y, z = xyz

    payload = {
        "dataset": dataset,
        "version": version,
        "implementation": "dynamic",
        "x": x,
        "y": y,
        "z": z,
    }

    print("START_DATE: ", start_date)
    print("END_DATE: ", end_date)
    print("CONFIRMED_ONLY: ", confirmed_only)
    if start_date is not None or end_date is not None or confirmed_only is not None:
        payload.update(
            start_date=start_date,
            end_date=end_date,
            confirmed_only=confirmed_only,
            filter_type="deforestation_alerts",
            source="datalake",
        )
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "confirmed_only": confirmed_only,
        }
        implementation = hash_query_params(params)
    else:
        implementation = "default"

    print("PAYLOAD: ", payload)
    png_data = await get_dynamic_tile(payload)

    background_tasks.add_task(
        copy_tile,
        png_data,
        f"{dataset}/{version}/{implementation}/{z}/{x}/{y}.png",
    )
    return StreamingResponse(io.BytesIO(png_data), media_type="image/png")
