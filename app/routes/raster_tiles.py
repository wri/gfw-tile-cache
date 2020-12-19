"""
Static raster tiles are pre-rendered for faster access. While performance for this tiles will be better,
you will not be able to filter data or change tile resolution.
Any of this operations will have to happen on the frontend.
If tiles for a given zoom level are not present for a selected dataset,
the server will redirect the request to the dynamic service and will attempt to generate it here
"""
import io
import json
from typing import Optional, Tuple

import aioboto3
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    Response,
)
from fastapi.logger import logger

from ..models.enumerators.wmts import WmtsRequest
from ..responses import RasterTileResponse
from ..settings.globals import AWS_REGION, BUCKET, RASTER_TILER_LAMBDA_NAME
from . import raster_tile_cache_version_dependency, raster_xyz

router = APIRouter()

#
# @router.get(
#     "/{dataset}/{version}/default/{z}/{x}/{y}.png",
#     response_class=Response,
#     tags=["Raster Tiles"],
#     response_description="PNG Raster Tile",
# )
# async def static_raster_tile(
#     *,
#     dv: Tuple[str, str] = Depends(raster_tile_cache_version_dependency),
#     xyz: Tuple[int, int, int] = Depends(raster_xyz),
# ) -> Response:
#     """
#     Generic raster tile
#     """
#     # This endpoint is not implemented and only exist for documentation purposes
#     # Default vector layers are stored on S3.
#     # If tile is not found, Cloud Front will redirect request to dynamic endpoint.
#     # Hence, this function should never be called.
#     raise NotImplementedError


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
    request: Request,
) -> Response:
    """
    Generic raster tile.
    """

    print("REQUEST HEADERS: ", request.headers)

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

    # Tile requests are routed to S3 first and only hit the tile cache app if S3 returns a 404.
    # We then try to dynamically create the PNG using a lambda function, return the result and store the PNG on S3 for future use.
    async with aioboto3.client("lambda", region_name=AWS_REGION) as lambda_client:
        response = await lambda_client.invoke(
            FunctionName=RASTER_TILER_LAMBDA_NAME,
            InvocationType="RequestResponse",
            Payload=bytes(json.dumps(payload), "utf-8"),
        )

    data_encoded = await response["Payload"].read()
    data = json.loads(data_encoded.decode())

    if data.get("status") == "success":
        # background_tasks.add_task(
        #     copy_tile,
        #     f"{dataset}/{version}/{implementation}/{z}/{x}/{y}.png",  # FIXME need to write to default?
        # )
        return data
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


async def copy_tile(tile, key):
    async with aioboto3.client("s3", region_name=AWS_REGION) as s3_client:

        data = io.StringIO().write(tile)
        await s3_client.upload_fileobj(
            data,
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
