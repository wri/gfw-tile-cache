from datetime import date, time
from typing import Dict, Any, List

import pendulum
from fastapi import HTTPException

from app.models.nasa_viirs_fire_alerts import NasaViirsFireAlertsExtended

supported_fields = NasaViirsFireAlertsExtended.schema()["properties"]


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
    if left < -180 or bottom < -90 or right > 180 or top > 90:
        raise HTTPException(status_code=400, detail="Tile index is out of bounds")


def validate_field_types(**fields: Any) -> None:
    for field, value in fields.items():
        if value is not None and type(value) not in _get_types(supported_fields[field]):
            raise HTTPException(
                status_code=400,
                detail=f"Field {field} must be of type {_get_types(supported_fields[field])}",
            )


def sanitize_fields(**fields: Any) -> Dict[str, Any]:
    for field, value in fields.items():
        if field not in supported_fields.keys():
            fields.pop(field)
    return fields


def _get_types(value: Dict[str, Any]) -> List[Any]:
    types: Dict[str, List[Any]] = {
        "number": [int, float],
        "string": [str, date, time],  # TODO find better way to validate data/time
        "boolean": [bool],
    }

    return types[value["type"]]
