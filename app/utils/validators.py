from datetime import date, time
from typing import Dict, Any, List

import mercantile
import pendulum
from fastapi import HTTPException

# from app.schemas.nasa_viirs_fire_alerts import NasaViirsFireAlertsExtended
from app.utils.metadata import get_versions

# supported_fields = NasaViirsFireAlertsExtended.schema()["properties"]


def validate_version(dataset, version) -> None:

    if version == "latest":
        return
    existing_versions = list()
    versions = get_versions(dataset)
    for row in versions:
        existing_versions.append(row.version)
        if row.version == version:
            return

    raise HTTPException(
        status_code=400,
        detail=f"Unknown version number. Dataset {dataset} has versions {existing_versions}",
    )


def validate_dates(start_date: str, end_date: str) -> None:
    _start_date = pendulum.from_format(start_date, "YYYY-MM-DD")
    _end_date = pendulum.from_format(end_date, "YYYY-MM-DD")

    if _start_date > _end_date:
        raise HTTPException(
            status_code=403, detail="Start date must be smaller or equal to end date"
        )

    diff = _end_date - _start_date
    if diff.in_days() > 90:
        raise HTTPException(status_code=403, detail="Date range cannot exceed 90 days")


def validate_bbox(left: float, bottom: float, right: float, top: float) -> None:
    """
    Tile should be within WebMercator extent
    """
    min_left, min_bottom, max_right, max_top = mercantile.xy_bounds(0, 0, 0)

    if left < min_left or bottom < min_bottom or right > max_right or top > max_top:
        raise HTTPException(status_code=400, detail="Tile index is out of bounds")


# def validate_field_types(**fields: Any) -> None:
#     for field, value in fields.items():
#         if value is not None and type(value) not in _get_types(supported_fields[field]):
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Field {field} must be of type {_get_types(supported_fields[field])}",
#             )
#
#
# def sanitize_fields(**fields: Any) -> Dict[str, Any]:
#     for field, value in fields.items():
#         if field not in supported_fields.keys():
#             fields.pop(field)
#     return fields
#
#
# def _get_types(value: Dict[str, Any]) -> List[Any]:
#     types: Dict[str, List[Any]] = {
#         "number": [int, float],
#         "string": [str, date, time],  # TODO find better way to validate data/time
#         "boolean": [bool],
#     }
#
#     return types[value["type"]]
