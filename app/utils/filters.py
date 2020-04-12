import logging
from typing import Optional, Union, List, Any, Dict, Tuple

from fastapi import HTTPException
from shapely.geometry import box
from sqlalchemy import text
from sqlalchemy.sql.elements import TextClause

from app.utils.geostore import get_geostore_geometry

Filter = Tuple[TextClause, Dict[str, Any]]
Bounds = Tuple[float, float, float, float]

LOGGER = logging.Logger(__name__)


async def geometry_filter(
    geostore_id: Optional[str], bounds: Bounds
) -> Optional[TextClause]:
    if isinstance(geostore_id, str):
        geometry, envelope = await get_geostore_geometry(geostore_id)
        if not envelope.intersects(box(*bounds)):
            raise HTTPException(
                status_code=404, detail="Tile does not intersect with geostore"
            )

        f = filter_intersects("t.geom", geometry)  # TODO avoid having to use t.
        return f
    return None


def confidence_filter(high_confidence_only: Optional[bool]) -> Optional[TextClause]:
    if high_confidence_only:
        # TODO make sure fire data are normalized
        return text("(confidence__cat = 'high' OR confidence__cat = 'h')")
    return None


def contextual_filter(**fields: Union[str, bool]) -> List[TextClause]:
    filters = list()
    for field, value in fields.items():
        if value is not None:
            f = filter_eq(field, value)
            filters.append(f)

    return filters


def date_filter(start_date: str, end_date: str) -> TextClause:
    f = text(
        "alert__date BETWEEN TO_TIMESTAMP(:start_date,'YYYY-MM-DD') AND TO_TIMESTAMP(:end_date,'YYYY-MM-DD')"
    )
    value = {"start_date": start_date, "end_date": end_date}
    f = f.bindparams(**value)
    return f


def filter_eq(field: str, value: Any) -> TextClause:
    f = text(f"{field} = :{field}")
    v = {f"{field}": value}
    f = f.bindparams(**v)

    return f


def filter_between(field, low, high) -> TextClause:
    f = text(f"{field} BETWEEN :low AND :high")
    value = {"low": low, "high": high}
    f = f.bindparams(**value)
    return f


def filter_intersects(field, geometry) -> TextClause:
    f = text(f"ST_Intersects({field}, ST_SetSRID(ST_GeomFromGeoJSON(:geometry),4326))")
    value = {"geometry": f"{geometry}"}
    f = f.bindparams(**value)

    return f
