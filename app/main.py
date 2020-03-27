import logging
import os
from typing import Optional

from asyncpg.pool import Pool
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from app import get_pool
from app.routers import tile_server

app = FastAPI()
ENV: str = os.environ["ENV"]
LOGGER = logging.Logger(__name__)
POOL: Optional[Pool] = None

app.include_router(tile_server.router)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.on_event("startup")
async def startup():

    global POOL
    POOL = await get_pool()


@app.on_event("shutdown")
async def shutdown():

    global POOL
    POOL.terminate()


app.mount("/static", StaticFiles(directory="/app/app/static"), name="static")
