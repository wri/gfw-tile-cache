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
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Response
from fastapi.logger import logger
from starlette.responses import StreamingResponse

from ..settings.globals import GLOBALS
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
    implementation: str = Path(
        "default", description="Tile cache implementation name."
    ),
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
    # As per cloud front settings only `dynamic` implementations should make it to this endpoint.
    png_data = await get_dynamic_tile(payload)

    # Copy dynamically created tile o tile cache for later reuse.
    background_tasks.add_task(
        copy_tile,
        png_data,
        f"{dataset}/{version}/default/{z}/{x}/{y}.png",
    )
    return StreamingResponse(io.BytesIO(png_data), media_type="image/png")


async def get_dynamic_tile(payload: Dict[str, Any]):
    """
    Invoke Lambda function to generate raster tile dynamically.
    """
    try:
        response = await invoke_lambda(GLOBALS.raster_tiler_lambda_name, payload)
    except httpx.ReadTimeout as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")

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
    async with aioboto3.client(
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
