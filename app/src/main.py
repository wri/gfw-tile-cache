import os
from typing import Optional

# from asyncpg.pool import Pool
from databases import Database
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from app.src import get_databse, get_module_logger  # , get_pool
from app.src.routers import tile_server

app = FastAPI()
# POOL: Optional[Pool] = None
DATABASE: Optional[Database] = None
ENV: str = os.environ["ENV"]
LOGGER = get_module_logger(__name__)

app.include_router(tile_server.router)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.on_event("startup")
async def startup():
    global DATABASE
    DATABASE = await get_databse()
    # global POOL
    # POOL = await get_pool()


@app.on_event("shutdown")
async def shutdown():
    # global POOL
    global DATABASE
    LOGGER.info("Closing DB connection pool")
    DATABASE.close()
    # POOL.close()
