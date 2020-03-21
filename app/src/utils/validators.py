from typing import Dict, Any

import pendulum
from fastapi import HTTPException


supported_fields = {
    "is__regional_primary_forest": bool,
    "is__alliance_for_zero_extinction_site": bool,
    "is__key_biodiversity_area": bool,
    "is__landmark": bool,
    "gfw_plantation__type": str,
    "is__gfw_mining": bool,
    "is__gfw_logging": bool,
    "rspo_oil_palm__certification_status": str,
    "is__gfw_wood_fiber": bool,
    "is__peat_land": bool,
    "is__idn_forest_moratorium": bool,
    "is__gfw_oil_palm": bool,
    "idn_forest_area__type": str,
    "per_forest_concession__type": str,
    "is__gfw_oil_gas": bool,
    "is__mangroves_2016": bool,
    "is__intact_forest_landscapes_2016": bool,
    "bra_biome__name": str,
}


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
        if type(value) is not supported_fields[field]:
            raise HTTPException(
                status_code=400,
                detail=f"Field {field} must be of type {supported_fields[field]}",
            )


def sanitize_fields(**fields: Any) -> Dict[str, Any]:
    for field, value in fields.items():
        if field not in supported_fields.keys():
            fields.pop(field)
    return fields
