"""
Static raster tiles are pre-rendered for faster access. While performance for this tiles will be better,
you will not be able to filter data or change tile resolution.
Any of this operations will have to happen on the frontend.
If tiles for a given zoom level are not present for a selected dataset,
the server will redirect the request to the dynamic service and will attempt to generate it here
"""
import base64
import io
import json
from typing import Optional, Tuple

import aioboto3
import httpx
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Path,
    Query,
    Response,
)
from fastapi.logger import logger
from starlette.responses import StreamingResponse

from ..models.enumerators.wmts import WmtsRequest
from ..settings.globals import AWS_REGION, BUCKET, RASTER_TILER_LAMBDA_NAME
from ..utils.aws import invoke_lambda
from . import raster_tile_cache_version_dependency, raster_xyz

router = APIRouter()


@router.get(
    "/{dataset}/{version}/{implementation}/{z}/{x}/{y}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def raster_tile(
    *,
    dv: Tuple[str, str] = Depends(raster_tile_cache_version_dependency),
    implementation: str = Path("default", description="Tile cache implementation name"),
    xyz: Tuple[int, int, int] = Depends(raster_xyz),
    background_tasks: BackgroundTasks,
) -> Response:
    """
    Generic raster tile.
    """

    dataset, version = dv
    x, y, z = xyz

    payload = {
        "dataset": dataset,
        "version": version,
        "implementation": implementation,
        "x": x,
        "y": y,
        "z": z,
    }

    try:
        response = await invoke_lambda(RASTER_TILER_LAMBDA_NAME, payload)
    except httpx.ReadTimeout as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")

    data = json.loads(response.text)

    if data.get("status") == "success":
        png_data = base64.b64decode(data.get("data"))
        background_tasks.add_task(
            copy_tile,
            png_data,
            f"{dataset}/{version}/{implementation}/{z}/{x}/{y}.png",  # FIXME need to write to default?
        )
        return StreamingResponse(io.BytesIO(png_data), media_type="image/png")
    elif data.get("status") == "error" and data.get("message") == "Tile not found":
        raise HTTPException(status_code=404, detail=data.get("message"))
    elif data.get("errorMessage"):
        logger.error(f"Lambda Function exited with error: {data['errorMessage']}")
        raise HTTPException(status_code=500, detail="Internal server error")
    else:
        logger.error(
            f"An unknown error occurred. Data received from Lambda function: {data}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def copy_tile(data, key):
    async with aioboto3.client("s3", region_name=AWS_REGION) as s3_client:

        png_file_obj = io.BytesIO()
        _: int = png_file_obj.write(data)
        await s3_client.upload_fileobj(
            png_file_obj,
            BUCKET,
            key,
            ExtraArgs={"ContentType": "image/png", "CacheControl": "max-age=31536000"},
        )


@router.get(
    "/{dataset}/{version}/default/wmts",
    response_class=Response,
    tags=["Raster Tiles"],
    # response_description="PNG Raster Tile",
)
async def wmts(
    *,
    dv: Tuple[str, str] = Depends(raster_tile_cache_version_dependency),
    SERVICE: str = Query("WMTS"),
    VERSION: str = Query("1.0.0"),
    REQUEST: WmtsRequest = Query(...),
    tileMatrixSet: Optional[str] = Query(None, description="Projection of tiles"),
    tileMatrix: Optional[int] = Query(None, description="z index"),
    tileRow: Optional[int] = Query(None, description="y index"),
    tileCol: Optional[int] = Query(None, description="x index"),
) -> Response:
    """
    WMTS Service
    """
    # dataset = dv[0]
    # version = dv[1]
    if REQUEST == WmtsRequest.get_capabilities:
        pass
    elif REQUEST == WmtsRequest.get_tiles:
        pass
