from typing import Dict, Any, Optional

import mercantile
from shapely.geometry import box

from app import get_pool
from asyncpg.pool import Pool
from starlette.responses import Response

Geometry = Dict[str, Any]


async def get_aggregated_tile(
    tile_bounds: box,
    start_date: str,
    end_date: str,
    confidence_filter: str,
    geometry_filter: str,
) -> Response:
    pool: Pool = await get_pool()
    left, bottom, right, top = tile_bounds

    sql = f"""
                WITH
                bounds AS (
                    SELECT ST_MakeEnvelope({left}, {bottom}, {right}, {top}, 3857) AS geom
                ),
                mvtgeom AS (
                    SELECT ST_AsMVTGeom(t.geom_wm, bounds.geom::box2d) AS geom,
                            bright_ti4, bright_ti5, frp
                    FROM viirs.v20200224 t, bounds
                    WHERE ST_Intersects(t.geom_wm, bounds.geom) AND acq_date BETWEEN '{start_date}'::timestamp
                                 AND '{end_date}'::timestamp {confidence_filter} {geometry_filter}
                ),
                mvtgroup AS (
                    SELECT geom, count(*) as count, avg(bright_ti4) as bright_ti4, avg(bright_ti5) as bright_ti5, sum(frp) as frp FROM mvtgeom
                    GROUP BY geom
                    )

                 SELECT ST_AsMVT(mvtgroup.*) FROM mvtgroup;
                """
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchval(sql)

    return Response(
        content=row,
        status_code=200,
        headers={
            "Content-Type": "application/x-protobuf",
            "Access-Control-Allow-Origin": "*",
        },
    )


async def get_tile(
    tile_bounds: box,
    start_date: str,
    end_date: str,
    confidence_filter: str,
    geometry_filter: str,
) -> Response:
    pool: Pool = await get_pool()

    left, bottom, right, top = tile_bounds

    sql = f"""
                    WITH
                    bounds AS (
                        SELECT ST_MakeEnvelope({left}, {bottom}, {right}, {top}, 3857) AS geom
                    ),
                    mvtgeom AS (
                        SELECT ST_AsMVTGeom(t.geom_wm, bounds.geom::box2d) AS geom,
                                latitude, longitude, acq_date, acq_time, confidence, bright_ti4, bright_ti5, frp
                        FROM viirs.v20200224 t, bounds
                        WHERE ST_Intersects(t.geom_wm, bounds.geom) AND acq_date BETWEEN '{start_date}'::timestamp
                                     AND '{end_date}'::timestamp {confidence_filter} {geometry_filter}
                    )

                     SELECT ST_AsMVT(mvtgeom.*) FROM mvtgeom;
                    """
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchval(sql)

    return Response(
        content=row,
        status_code=200,
        headers={
            "Content-Type": "application/x-protobuf",
            "Access-Control-Allow-Origin": "*",
        },
    )
