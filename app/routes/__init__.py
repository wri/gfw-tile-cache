import os
from typing import Optional, Tuple, Union

import mercantile
import pendulum
from fastapi import Depends, HTTPException, Path, Query, Request, status
from fastapi.logger import logger
from shapely.geometry import box

from ..crud.sync_db.tile_cache_assets import get_versions
from ..models.enumerators.datasets import (
    COGDatasets,
    DynamicVectorTileCacheDatasets,
    RasterTileCacheDatasets,
    StaticVectorTileCacheDatasets,
)
from ..models.enumerators.tile_caches import TileCacheType
from ..models.enumerators.versions import Versions
from ..models.types import Bounds

DATE_REGEX = r"^\d{4}\-(0?[1-9]|1[012])\-(0?[1-9]|[12][0-9]|3[01])$"
VERSION_REGEX = r"^v\d{1,8}(\.\d{1,3}){0,2}?$|^latest$"
XYZ_REGEX = r"^\d+(@(2|0.5|0.25)x)?$"
VERSION_REGEX_NO_LATEST = r"^v\d{1,8}(\.\d{1,3}){0,2}?$"

DATA_LAKE_BUCKET = os.environ.get("DATA_LAKE_BUCKET")


def to_bbox(x: int, y: int, z: int) -> Bounds:
    logger.debug(f"Coordinates (X, Y, Z): {x},{y},{z}")
    left, bottom, right, top = mercantile.xy_bounds(x, y, z)
    logger.debug(f"Bounds (Left, Bottom, Right, Top): {left},{bottom},{right},{top}")
    return box(left, bottom, right, top).bounds


async def vector_xyz(
    z: int = Path(..., description="Zoom level", ge=0, le=22),
    x: int = Path(..., description="Tile grid column", ge=0),
    y: Union[int, str] = Path(
        ...,
        description="Tile grid row (integer >= 0) and optional scale factor (either @2x, @0.5x or @0.25x)",
        regex=XYZ_REGEX,
    ),
) -> Tuple[Bounds, int, int]:
    if isinstance(y, str) and "@" in y:
        __y, _scale = y.split("@")
        _y: int = int(__y)
        scale: float = float(_scale[:-1])
    elif isinstance(y, int):
        _y = y
        scale = 1.0
    else:
        raise HTTPException(
            400,
            detail="Y value must be either integer of combination and integer and scale factor",
        )

    extent: int = int(4096 * scale)
    bbox: Bounds = to_bbox(x, _y, z)
    validate_bbox(*bbox)
    return bbox, z, extent


async def raster_xyz(
    z: int = Path(..., description="Zoom level", ge=0, le=22),
    x: int = Path(..., description="Tile grid column", ge=0),
    y: int = Path(..., description="Tile grid row", ge=0),
) -> Tuple[int, int, int]:

    bbox: Bounds = to_bbox(x, y, z)
    validate_bbox(*bbox)
    return x, y, z


async def dynamic_dataset_dependency(dataset: DynamicVectorTileCacheDatasets) -> str:  # type: ignore
    return dataset


async def static_dataset_dependency(dataset: StaticVectorTileCacheDatasets) -> str:  # type: ignore
    return dataset


async def version_dependency(
    version: str = Path(..., description=Versions.__doc__, regex=VERSION_REGEX)
) -> str:
    return version


async def dynamic_vector_tile_cache_version_dependency(
    *,
    dataset: DynamicVectorTileCacheDatasets = Path(  # type: ignore
        ..., description=DynamicVectorTileCacheDatasets.__doc__
    ),
    version: str = Depends(version_dependency),
) -> Tuple[str, str]:
    # Middleware should have redirected GET requests to latest version already.
    # Any other request method should not use `latest` keyword.
    if version == "latest":
        raise HTTPException(
            status_code=400,
            detail="You must list version name explicitly for this operation.",
        )
    validate_tile_cache_version(
        dataset, version, TileCacheType.dynamic_vector_tile_cache
    )
    return dataset, version


async def static_vector_tile_cache_version_dependency(
    dataset: StaticVectorTileCacheDatasets = Path(  # type: ignore
        ..., description=StaticVectorTileCacheDatasets.__doc__
    ),
    version: str = Depends(version_dependency),
) -> Tuple[str, str]:
    # Middleware should have redirected GET requests to latest version already.
    # Any other request method should not use `latest` keyword.
    if version == "latest":
        raise HTTPException(
            status_code=400,
            detail="You must list version name explicitly for this operation.",
        )
    validate_tile_cache_version(
        dataset, version, TileCacheType.static_vector_tile_cache
    )
    return dataset, version


async def raster_tile_cache_version_dependency(
    dataset: RasterTileCacheDatasets = Path(  # type: ignore
        ..., description=RasterTileCacheDatasets.__doc__
    ),
    version: str = Depends(version_dependency),
) -> Tuple[str, str]:
    # Middleware should have redirected GET requests to latest version already.
    # Any other request method should not use `latest` keyword.
    if version == "latest":
        raise HTTPException(
            status_code=400,
            detail="You must list version name explicitly for this operation.",
        )
    validate_tile_cache_version(dataset, version, TileCacheType.raster_tile_cache)
    return dataset, version


async def cog_asset_dependency(
    request: Request,
    dataset: Optional[COGDatasets] = Query(None, description=COGDatasets.__doc__),  # type: ignore
    version: Optional[str] = Query(
        None, description="Data API dataset version.", regex=VERSION_REGEX_NO_LATEST
    ),
    url: Optional[str] = Query(
        None,
        description="Dataset path. This needs to be set if `dataset` and `version` query parameters for a Data API dataset are not set.",
    ),
) -> Optional[str]:

    if dataset is None and version is None and url is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Need to pass either `url` or `dataset` and `version` pair for Data API dataset.",
        )

    if dataset and version and url:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Need to pass either `url` or `dataset` and `version` pair, not both.",
        )

    if dataset and version:
        folder: str = (
            f"s3://{DATA_LAKE_BUCKET}/{dataset}/{version}/raster/epsg-4326/cog"
        )
        if "bands" in request.query_params:
            return folder

        return f"{folder}/default.tif"

    return url


async def optional_implementation_dependency(
    implementation: Optional[str] = Query(
        None,
        description="Tile cache implementation name for which dynamic tile should be rendered. "
        "This query parameter is mutually exclusive to all other query parameters. "
        "If set other parameters will be ignored.",
    )
) -> Optional[str]:
    return implementation


def validate_tile_cache_version(dataset, version, tile_cache_type) -> None:

    existing_versions = list()
    versions = get_versions(dataset, tile_cache_type)
    for v in versions:
        existing_versions.append(v)
        if v == version:
            return

    raise HTTPException(
        status_code=400,
        detail=f"Unknown version number. {tile_cache_type} of dataset {dataset} has versions {existing_versions}",
    )


def validate_dates(start_date: str, end_date: str, force_date_range) -> None:
    _start_date = pendulum.from_format(start_date, "YYYY-MM-DD")
    _end_date = pendulum.from_format(end_date, "YYYY-MM-DD")
    if _start_date > _end_date:
        raise HTTPException(
            status_code=403, detail="Start date must be smaller or equal to end date."
        )

    if not force_date_range:
        diff = _end_date - _start_date
        if diff.in_days() > 90:
            raise HTTPException(
                status_code=403, detail="Date range cannot exceed 90 days"
            )


def validate_bbox(left: float, bottom: float, right: float, top: float) -> None:
    """Tile should be within WebMercator extent."""
    min_left, min_bottom, max_right, max_top = mercantile.xy_bounds(0, 0, 0)

    if left < min_left or bottom < min_bottom or right > max_right or top > max_top:
        raise HTTPException(status_code=400, detail="Tile index is out of bounds")
