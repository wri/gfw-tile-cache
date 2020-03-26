from typing import Optional, Union, List, Any, Dict, Tuple

from fastapi import HTTPException
from shapely.geometry import box
from sqlalchemy import text
from sqlalchemy.sql.elements import TextClause

from app.utils.geostore import get_geostore_geometry
from app.utils.decorators import LogDecorator

Filter = Tuple[TextClause, Dict[str, Any]]


@LogDecorator()
async def geometry_filter(
    geostore_id: Optional[str], tile_bounds: box
) -> Optional[Filter]:
    if isinstance(geostore_id, str):
        geometry, envelope = await get_geostore_geometry(geostore_id)
        if not envelope.intersects(tile_bounds):
            raise HTTPException(
                status_code=404, detail="Tile does not intersect with geostore"
            )

        f = text(
            f"ST_Intersects(t.geom, ST_SetSRID(ST_GeomFromGeoJSON(:geometry),4326))"
        )
        value = {"geometry": f"{geometry}"}
        f = f.bindparams(**value)
        return f, value
    return None


@LogDecorator()
def confidence_filter(high_confidence_only: bool) -> Optional[Filter]:
    if high_confidence_only:
        return text("confidence__cat = :confidence"), {"confidence": "h"}
    return None


@LogDecorator()
def contextual_filter(**fields: Union[str, bool]) -> List[Filter]:
    filters = list()
    for field, value in fields.items():
        if value is not None:
            f = text(f"{field} = :{field}")
            v = {f"{field}": value}
            f = f.bindparams(**v)
            filters.append((f, v))

    return filters


@LogDecorator()
def date_filter(start_date: str, end_date: str) -> Filter:
    f = text(
        "alert__date BETWEEN TO_TIMESTAMP(:start_date,'YYYY-MM-DD') AND TO_TIMESTAMP(:end_date,'YYYY-MM-DD')"
    )
    value = {"start_date": start_date, "end_date": end_date}
    f = f.bindparams(**value)
    return f, value
