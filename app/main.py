import json
import os
import logging
from typing import Optional

import mercantile
import asyncpg
from fastapi import FastAPI, Path, Query
from starlette.responses import HTMLResponse, Response

app = FastAPI()
POOL: Optional[asyncpg.pool.Pool] = None
# POOL = None
ENV = "dev"


def get_module_logger(name):
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    sh = logging.StreamHandler()
    sh.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.addHandler(sh)
    if ENV != "production":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    return logger


LOGGER = get_module_logger("gfw-tile-cache")


@app.on_event("startup")
async def startup():
    global POOL
    LOGGER.info("Create DB connection pool")
    POOL = await asyncpg.create_pool(
        database=os.environ["POSTGRES_NAME"],
        user=os.environ["POSTGRES_USERNAME"],
        password=os.environ["POSTGRES_PASSWORD"],
        port=os.environ["POSTGRES_PORT"],
        host=os.environ["POSTGRES_HOST"],
    )


@app.on_event("shutdown")
async def shutdown():
    global POOL
    LOGGER.info("Closing DB connection pool")
    POOL.close()


@app.get("/")
async def root():
    LOGGER.info("Root request")
    return {"message": "Hello World"}


@app.get("/nasa_viirs_fire_alerts/latest/mapbox.html", response_class=HTMLResponse)
async def mapbox():
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, "static/mapbox.html"), "r") as myfile:
        html_content = myfile.read()
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/nasa_viirs_fire_alerts/latest/esri.html", response_class=HTMLResponse)
async def esri():
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, "static/esri.html"), "r") as myfile:
        html_content = myfile.read()
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/nasa_viirs_fire_alerts/latest/root.json")
async def root_json():
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, "static/root.json"), "r") as myfile:
        json_content = json.loads(myfile.read())
    return json_content


@app.get(
    "/nasa_viirs_fire_alerts/latest/default/{z}/{x}/{y}.pbf", response_class=Response
)
async def nasa_viirs_fire_alerts(
    x: int = Path(..., title="Tile grid column", ge=0),
    y: int = Path(..., title="Tile grid row", ge=0),
    z: int = Path(..., title="Zoom level", ge=0),
    start_date: str = Query("2018-01-01"),
    end_date: str = Query("2018-01-08"),
    high_confidence_only: bool = Query(False),
) -> Response:
    LOGGER.info(f"Get tile {z}/{x}/{y}")
    LOGGER.info(f"Date range set to {start_date} - {end_date}")

    if z >= 6:
        return await get_tile(x, y, z, start_date, end_date, high_confidence_only)
    else:
        return await get_aggregated_tile(
            x, y, z, start_date, end_date, high_confidence_only
        )


@app.get("/nasa_viirs_fire_alerts/latest/default/VectorTileServer")
async def vector_tile_server():
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, "static/VectorTileServer.json"), "r") as myfile:
        json_content = json.loads(myfile.read())
    return json_content


async def get_aggregated_tile(
    x: int, y: int, z: int, start_date: str, end_date: str, high_confidence_only: bool
) -> Response:

    global POOL
    if isinstance(POOL, asyncpg.pool.Pool):

        left, bottom, right, top = mercantile.xy_bounds(x, y, z)

        if high_confidence_only:
            confidence_filter = "AND confidence = 'h'"
        else:
            confidence_filter = ""

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
                                 AND '{end_date}'::timestamp {confidence_filter}
                ),
                mvtgroup AS (
                    SELECT geom, count(*) as count, avg(bright_ti4) as bright_ti4, avg(bright_ti5) as bright_ti5, sum(frp) as frp FROM mvtgeom
                    GROUP BY geom
                    )

                 SELECT ST_AsMVT(mvtgroup.*) FROM mvtgroup;
                """
        async with POOL.acquire() as conn:
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
    else:
        raise ConnectionError("No Database connection")


async def get_tile(
    x: int, y: int, z: int, start_date: str, end_date: str, high_confidence_only: bool
) -> Response:

    # POOL: asyncpg.pool

    global POOL
    if isinstance(POOL, asyncpg.pool.Pool):

        left, bottom, right, top = mercantile.xy_bounds(x, y, z)

        if high_confidence_only:
            confidence_filter = "AND confidence = 'h'"
        else:
            confidence_filter = ""

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
                                     AND '{end_date}'::timestamp {confidence_filter}
                    )

                     SELECT ST_AsMVT(mvtgeom.*) FROM mvtgeom;
                    """
        async with POOL.acquire() as conn:
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
    else:
        raise ConnectionError("No database connection")
