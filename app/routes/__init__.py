from typing import Tuple, Union

import mercantile
import pendulum
from fastapi import Depends, HTTPException, Path
from fastapi.logger import logger
from shapely.geometry import box

from ..crud.sync_db.vector_tile_assets import get_dynamic_versions, get_static_versions
from ..models.enumerators.dynamic_enumerators import (
    get_dynamic_datasets,
    get_static_datasets,
)
from ..models.types import Bounds

DATE_REGEX = "^\d{4}\-(0?[1-9]|1[012])\-(0?[1-9]|[12][0-9]|3[01])$"  # mypy: ignore
VERSION_REGEX = r"^v\d{1,8}\.?\d{1,3}\.?\d{1,3}$|^latest$"
NOW = pendulum.now()
DEFAULT_START = NOW.subtract(weeks=1).to_date_string()
DEFAULT_END = NOW.to_date_string()


def to_bbox(x: int, y: int, z: int) -> Bounds:
    logger.debug(f"{x},{y},{z}")
    left, bottom, right, top = mercantile.xy_bounds(x, y, z)
    logger.debug(f"{left},{bottom},{right},{top}")
    return box(left, bottom, right, top).bounds


async def xyz(
    z: int = Path(..., title="Zoom level", ge=0, le=22),
    x: int = Path(..., title="Tile grid column", ge=0),
    y: Union[int, str] = Path(
        ...,
        title="Tile grid row (integer >= 0) and optional scale factor (either @2x, @0.5x or @0.25x)",
        regex="^\d+(@(2|0.5|0.25)x)?$",
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


async def dynamic_dataset_dependency(dataset: get_dynamic_datasets()) -> str:  # type: ignore
    return dataset


async def static_dataset_dependency(dataset: get_static_datasets()) -> str:  # type: ignore
    return dataset


async def dynamic_version_dependency(
    dataset: str = Depends(dynamic_dataset_dependency),
    version: str = Path(..., title="Dataset version", regex=VERSION_REGEX),
) -> Tuple[str, str]:
    # Middleware should have redirected GET requests to latest version already.
    # Any other request method should not use `latest` keyword.
    if version == "latest":
        raise HTTPException(
            status_code=400,
            detail="You must list version name explicitly for this operation.",
        )
    validate_dynamic_version(dataset, version)
    return dataset, version


async def static_version_dependency(
    dataset: str = Depends(static_dataset_dependency),
    version: str = Path(..., title="Dataset version", regex=VERSION_REGEX),
) -> Tuple[str, str]:
    # Middleware should have redirected GET requests to latest version already.
    # Any other request method should not use `latest` keyword.
    if version == "latest":
        raise HTTPException(
            status_code=400,
            detail="You must list version name explicitly for this operation.",
        )
    validate_static_version(dataset, version)
    return dataset, version


def validate_dynamic_version(dataset, version) -> None:
    existing_versions = list()
    versions = get_dynamic_versions(dataset)
    for row in versions:
        existing_versions.append(row.version)
        if row.version == version:
            return

    raise HTTPException(
        status_code=400,
        detail=f"Unknown version number. Dataset {dataset} has versions {existing_versions}",
    )


def validate_static_version(dataset, version) -> None:
    existing_versions = list()
    static_versions = get_static_versions(dataset)
    for static_version in static_versions:
        existing_versions.append(static_version)
        if static_version == version:
            return

    raise HTTPException(
        status_code=400,
        detail=f"Unknown version number. Dataset {dataset} has versions {existing_versions}",
    )


def validate_dates(start_date: str, end_date: str, force_date_range) -> None:
    _start_date = pendulum.from_format(start_date, "YYYY-MM-DD")
    _end_date = pendulum.from_format(end_date, "YYYY-MM-DD")

    if _start_date > _end_date:
        raise HTTPException(
            status_code=403, detail="Start date must be smaller or equal to end date"
        )

    if not force_date_range:
        diff = _end_date - _start_date
        if diff.in_days() > 90:
            raise HTTPException(
                status_code=403, detail="Date range cannot exceed 90 days"
            )


def validate_bbox(left: float, bottom: float, right: float, top: float) -> None:
    """
    Tile should be within WebMercator extent
    """
    min_left, min_bottom, max_right, max_top = mercantile.xy_bounds(0, 0, 0)

    if left < min_left or bottom < min_bottom or right > max_right or top > max_top:
        raise HTTPException(status_code=400, detail="Tile index is out of bounds")
