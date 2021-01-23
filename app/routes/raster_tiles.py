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
from datetime import datetime
from hashlib import md5
from typing import Any, Dict, Optional, Tuple

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

from ..models.enumerators.attributes import TcdEnum
from ..models.enumerators.versions import Versions
from ..models.enumerators.wmts import WmtsRequest
from ..settings.globals import (
    AWS_ENDPOINT_URI,
    AWS_REGION,
    BUCKET,
    RASTER_TILER_LAMBDA_NAME,
)
from ..utils.aws import invoke_lambda
from . import (
    DATE_REGEX,
    VERSION_REGEX,
    raster_tile_cache_version_dependency,
    raster_xyz,
)

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

    png_data = await _dynamic_tile(payload, background_tasks)

    params = {"start_year": start_year, "end_year": end_year, "tcd": tcd}
    query_hash = hash_query_params(params)

    background_tasks.add_task(
        copy_tile,
        png_data,
        f"{dataset}/{version}/{query_hash}/{z}/{x}/{y}.png",
    )
    return StreamingResponse(io.BytesIO(png_data), media_type="image/png")


@router.get(
    "/umd_glad_alerts/{version}/dynamic/{z}/{x}/{y}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def umd_glad_alerts_raster_tile(
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
    UMD GLAD alerts raster tiles.
    """
    dataset = "umd_glad_alerts"
    return await _deforestation_alert_tiles(
        dataset, version, xyz, start_date, end_date, confirmed_only, background_tasks
    )


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
    return await _deforestation_alert_tiles(
        dataset, version, xyz, start_date, end_date, confirmed_only, background_tasks
    )


async def _deforestation_alert_tiles(
    dataset: str,
    version: str,
    xyz: Tuple[int, int, int],
    start_date: Optional[str],
    end_date: Optional[str],
    confirmed_only: Optional[bool],
    background_tasks: BackgroundTasks,
) -> Response:
    x, y, z = xyz

    payload = {
        "dataset": dataset,
        "version": version,
        "implementation": "dynamic",
        "x": x,
        "y": y,
        "z": z,
    }

    if start_date or end_date or confirmed_only:
        payload.update(
            {
                "start_date": start_date,
                "end_date": end_date,
                "confirmed_only": confirmed_only,
                "filter_type": "deforestation_alerts",
                "source": "tilecache",
            }
        )
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "confirmed_only": confirmed_only,
        }
        implementation = hash_query_params(params)
    else:
        implementation = "default"

    png_data = await _dynamic_tile(payload, background_tasks)

    background_tasks.add_task(
        copy_tile,
        png_data,
        f"{dataset}/{version}/{implementation}/{z}/{x}/{y}.png",
    )
    return StreamingResponse(io.BytesIO(png_data), media_type="image/png")


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
    png_data = await _dynamic_tile(payload, background_tasks)
    background_tasks.add_task(
        copy_tile,
        png_data,
        f"{dataset}/{version}/default/{z}/{x}/{y}.png",
    )
    return StreamingResponse(io.BytesIO(png_data), media_type="image/png")


async def _dynamic_tile(payload: Dict[str, Any], background_tasks):
    try:
        response = await invoke_lambda(RASTER_TILER_LAMBDA_NAME, payload)
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
    sorted_params = {
        key: params[key] for key in sorted(params) if params[key] is not None
    }
    return md5(json.dumps(sorted_params).encode()).hexdigest()


async def copy_tile(data, key):
    async with aioboto3.client(
        "s3", region_name=AWS_REGION, endpoint_url=AWS_ENDPOINT_URI
    ) as s3_client:
        logger.info(f"Uploading to S3 bucket: {BUCKET} key: {key}")

        png_file_obj = io.BytesIO()
        _: int = png_file_obj.write(data)
        png_file_obj.seek(0)
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
