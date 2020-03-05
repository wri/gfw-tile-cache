import os
from typing import Optional

from asyncpg.pool import Pool
from fastapi import FastAPI
from app import get_pool, get_module_logger
from app.routers import tile_server

app = FastAPI()
POOL: Optional[Pool] = None
ENV: str = os.environ["ENV"]
LOGGER = get_module_logger(__name__)

app.include_router(tile_server.router)


@app.on_event("startup")
async def startup():
    global POOL
    POOL = await get_pool()


@app.on_event("shutdown")
async def shutdown():
    global POOL
    LOGGER.info("Closing DB connection pool")
    POOL.close()
