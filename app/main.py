import os
from typing import Optional

from databases import Database
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from app import get_database, get_module_logger
from app.routers import tile_server

app = FastAPI()
DATABASE: Optional[Database] = None
ENV: str = os.environ["ENV"]
LOGGER = get_module_logger(__name__)

app.include_router(tile_server.router)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.on_event("startup")
async def startup():
    global DATABASE
    DATABASE = await get_database()
    await DATABASE.connect()
    # global POOL
    # POOL = await get_pool()


@app.on_event("shutdown")
async def shutdown():
    # global POOL
    global DATABASE
    LOGGER.info("Closing DB connection pool")
    DATABASE.close()
    # POOL.close()


# app.mount("/static", StaticFiles(directory="/app/app/static"), name="static")
