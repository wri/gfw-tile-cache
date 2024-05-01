from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException
from shapely.geometry import box, shape
from sqlalchemy.sql.elements import TextClause

from ....application import db
from ....models.types import Bounds


async def geometry_filter(
    bounds: Bounds, geometry: Dict[str, Any] | None
) -> Optional[TextClause]:
    if geometry:
        envelope = shape(geometry).envelope
        if not envelope.intersects(box(*bounds)):
            raise HTTPException(
                status_code=404, detail="Tile does not intersect with geostore"
            )

        f = filter_intersects("t.geom", geometry)  # TODO avoid having to use t.
        return f
    return None


def contextual_filter(**fields: Union[str, bool]) -> List[TextClause]:
    filters: List[TextClause] = list()
    for field, value in fields.items():
        if value is not None:
            f = filter_eq(field, value)
            filters.append(f)

    return filters


def date_filter(date_field: str, start_date: str, end_date: str) -> TextClause:
    f: TextClause = db.text(
        f"{date_field} BETWEEN TO_TIMESTAMP(:start_date,'YYYY-MM-DD') AND TO_TIMESTAMP(:end_date,'YYYY-MM-DD')"
    )
    values: Dict[str, Any] = {"start_date": start_date, "end_date": end_date}
    f = f.bindparams(**values)
    return f


def filter_eq(field: str, value: Any) -> TextClause:
    f: TextClause = db.text(f"{field} = :{field}")
    values: Dict[str, Any] = {f"{field}": value}
    f = f.bindparams(**values)

    return f


def filter_between(field, low, high) -> TextClause:
    f: TextClause = db.text(f"{field} BETWEEN :low AND :high")
    values: Dict[str, Any] = {"low": low, "high": high}
    f = f.bindparams(**values)
    return f


def filter_gt(field: str, value: Any) -> TextClause:
    f: TextClause = db.text(f"{field} <= :{field}")
    values: Dict[str, Any] = {f"{field}": value}
    f = f.bindparams(**values)

    return f


def filter_intersects(field, geometry) -> TextClause:
    f: TextClause = db.text(
        f"ST_Intersects({field}, ST_SetSRID(ST_GeomFromGeoJSON(:geometry),4326))"
    )
    values: Dict[str, Any] = {"geometry": f"{geometry}"}
    f = f.bindparams(**values)

    return f
