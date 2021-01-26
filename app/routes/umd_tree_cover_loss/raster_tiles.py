import io
from datetime import datetime
from typing import Optional, Tuple

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query, Response
from starlette.responses import StreamingResponse

from ...models.enumerators.attributes import TcdEnum
from ...models.enumerators.versions import Versions
from .. import VERSION_REGEX, raster_xyz
from ..raster_tiles import copy_tile, get_dynamic_tile, hash_query_params

router = APIRouter()


@router.get(
    "/umd_tree_cover_loss/{version}/dynamic/{z}/{x}/{y}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def umd_tree_cover_loss_raster_tile(
    *,
    version: str = Path(..., description=Versions.__doc__, regex=VERSION_REGEX),
    xyz: Tuple[int, int, int] = Depends(raster_xyz),
    start_year: Optional[int] = Query(
        None, description="Start Year.", ge=2000, le=datetime.now().year - 1
    ),
    end_year: Optional[int] = Query(
        None, description="End Year.", ge=2000, le=datetime.now().year - 1
    ),
    tcd: TcdEnum = Query(TcdEnum.thirty, description="Tree Cover Density threshold."),
    background_tasks: BackgroundTasks,
) -> Response:
    """
    Generic raster tile.
    """

    dataset = "umd_tree_cover_loss"
    x, y, z = xyz

    payload = {
        "dataset": dataset,
        "version": version,
        "implementation": f"tcd_{tcd}",
        "x": x,
        "y": y,
        "z": z,
        "start_year": start_year,
        "end_year": end_year,
        "filter_type": "annual_loss",
        "source": "tilecache",
    }

    png_data = await get_dynamic_tile(payload)

    params = {"start_year": start_year, "end_year": end_year, "tcd": tcd}
    query_hash = hash_query_params(params)

    background_tasks.add_task(
        copy_tile,
        png_data,
        f"{dataset}/{version}/{query_hash}/{z}/{x}/{y}.png",
    )
    return StreamingResponse(io.BytesIO(png_data), media_type="image/png")
