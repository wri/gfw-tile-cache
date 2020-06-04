from typing import Optional

from asyncpg import Connection
from sqlalchemy import table, select, literal_column, column
from geojson import Point, Polygon
from fastapi.logger import logger

from app.utils.filters import filter_eq, filter_intersects, date_filter
from app.utils.geostore import geodesic_point_buffer
from app.utils.metadata import get_fields
from app.utils.sql import compile_sql


async def get_feature(db: Connection, dataset, version, feature_id):
    t = table(version)  # TODO validate version
    t.schema = dataset

    columns = [literal_column("*")]
    sql = select(columns).select_from(t).where(filter_eq("objectid", feature_id))
    sql = compile_sql(sql)

    sql = await db.prepare(str(sql))
    feature = await sql.fetchrow(timeout=30)

    return feature


async def get_features_by_location(
    db: Connection,
    dataset: str,
    version: str,
    lat: float,
    lng: float,
    zoom: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    # pool: Pool = await a_get_pool()
    t = table(version)  # TODO validate version
    t.schema = dataset

    buffer_distance = _get_buffer_distance(zoom)
    if buffer_distance:
        geometry = Polygon(geodesic_point_buffer(lat, lng, buffer_distance))
    else:
        geometry = Point((lat, lng))

    fields = get_fields(dataset, version)

    columns = [column(field["name"]) for field in fields if field["is_feature_info"]]

    sql = select(columns).select_from(t).where(filter_intersects("geom", str(geometry)))
    if start_date and end_date:
        sql = sql.where(date_filter(start_date, end_date))

    logger.info(str(sql))
    sql = compile_sql(sql)

    sql = await db.prepare(str(sql))
    features = await sql.fetch(timeout=30)

    return features


def _get_buffer_distance(zoom: int) -> int:
    zoom_buffer = {
        "z0": 10000,
        "z1": 5000,
        "z2": 2500,
        "z3": 1250,
        "z4": 600,
        "z5": 300,
        "z6": 500,
        "z7": 80,
        "z8": 40,
        "z9": 20,
    }

    try:
        return zoom_buffer[f"z{zoom}"]
    except KeyError:
        return 0
