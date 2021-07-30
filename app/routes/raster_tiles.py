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
from hashlib import md5
from typing import Any, Dict, Tuple

import aioboto3
import httpx
from botocore.exceptions import ClientError
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
from fastapi.responses import RedirectResponse, StreamingResponse

from ..crud.sync_db.tile_cache_assets import get_max_zoom
from ..models.enumerators.tile_caches import TileCacheType
from ..settings.globals import GLOBALS
from ..utils.aws import invoke_lambda
from . import raster_tile_cache_version_dependency, raster_xyz

router = APIRouter()


@router.get(
    "/{dataset}/{version}/dynamic/{z}/{x}/{y}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def dynamic_raster_tile(
    *,
    dv: Tuple[str, str] = Depends(raster_tile_cache_version_dependency),
    xyz: Tuple[int, int, int] = Depends(raster_xyz),
    implementation: str = Query(
        "default",
        description="Tile cache implementation name for which dynamic tile should be rendered.",
    ),
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
        "over_zoom": get_max_zoom(
            dataset, version, implementation, TileCacheType.raster_tile_cache
        ),
    }

    return await get_dynamic_raster_tile(payload, implementation, background_tasks)


@router.get(
    "/{dataset}/{version}/{implementation}/{z}/{x}/{y}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def static_raster_tile(
    *,
    dv: Tuple[str, str] = Depends(raster_tile_cache_version_dependency),
    implementation: str = Path(
        "default", description="Tile cache implementation name."
    ),
    xyz: Tuple[int, int, int] = Depends(raster_xyz),
    background_tasks: BackgroundTasks,
) -> Response:
    """
    Generic raster tile.
    """
    # This route is only here for documentation purposes. Static raster tiles are served directly via cloud front.
    pass


async def get_dynamic_raster_tile(
    payload, implementation, background_tasks: BackgroundTasks
) -> StreamingResponse:

    dataset = payload.get("dataset")
    version = payload.get("version")
    x = payload.get("x")
    y = payload.get("y")
    z = payload.get("z")

    # As per cloud front settings only `dynamic` implementations should make it to this endpoint.
    png_data = await get_lambda_tile(payload)

    # Copy dynamically created tile to tile cache for later reuse.
    background_tasks.add_task(
        copy_tile,
        png_data,
        f"{dataset}/{version}/{implementation}/{z}/{x}/{y}.png",
    )
    return StreamingResponse(io.BytesIO(png_data), media_type="image/png")


async def get_lambda_tile(payload: Dict[str, Any]):
    """
    Invoke Lambda function to generate raster tile dynamically.
    """
    try:
        response = await invoke_lambda(GLOBALS.raster_tiler_lambda_name, payload)
    except httpx.ReadTimeout as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")

    logger.debug(response.text)

    data = json.loads(response.text)
    if data.get("status") == "success":
        return base64.b64decode(data.get("data"))
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


def hash_query_params(params: Dict[str, Any]) -> str:
    """Hash query parameters in alphabetic order.

    This way we can store tile as its own implementation and
    later read it them from file instead of dynamically create them over and over again.
    """

    sorted_params = {
        key: params[key] for key in sorted(params) if params[key] is not None
    }
    return md5(json.dumps(sorted_params).encode()).hexdigest()


async def copy_tile(data, key):
    """Copy tile to S3"""

    session = aioboto3.Session()
    async with session.client(
        "s3", region_name=GLOBALS.aws_region, endpoint_url=GLOBALS.aws_endpoint_uri
    ) as s3_client:
        logger.info(f"Uploading to S3 bucket: {GLOBALS.bucket} key: {key}")

        png_file_obj = io.BytesIO()
        _: int = png_file_obj.write(data)
        png_file_obj.seek(0)
        await s3_client.upload_fileobj(
            png_file_obj,
            GLOBALS.bucket,
            key,
            ExtraArgs={"ContentType": "image/png", "CacheControl": "max-age=31536000"},
        )


async def get_cached_response(payload, query_hash, background_tasks):

    dataset = payload.get("dataset")
    version = payload.get("version")
    x = payload.get("x")
    y = payload.get("y")
    z = payload.get("z")
    key = f"{dataset}/{version}/{query_hash}/{z}/{x}/{y}.png"

    session = aioboto3.Session()
    async with session.client(
        "s3", region_name=GLOBALS.aws_region, endpoint_url=GLOBALS.aws_endpoint_uri
    ) as s3_client:
        try:
            await s3_client.head_object(Bucket=GLOBALS.bucket, Key=key)
        except ClientError:
            logger.debug(f"No cached tile found for key {key}, call lambda function.")
            return await get_dynamic_raster_tile(payload, query_hash, background_tasks)
        else:
            logger.debug(f"Redirecting to cached response {key}.")
            return RedirectResponse(f"{GLOBALS.tile_cache_url}/{key}")
