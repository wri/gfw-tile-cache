import logging
from typing import Optional

from asyncpg.pool import Pool
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware

# from fastapi.staticfiles import StaticFiles

from app.database import a_get_pool
from app.routers import tile_server, features


app = FastAPI(
    title="GFW Vector Tile Cache API",
    description="This API allows to request vector tiles for selected GFW data layers.",
    version="0.1.0",
)
A_POOL: Optional[Pool] = None

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

app.include_router(tile_server.router)
app.include_router(features.router)


@app.on_event("startup")
async def startup():
    global A_POOL
    logging.debug("TEST TEST TEST")
    A_POOL = await a_get_pool()


@app.on_event("shutdown")
async def shutdown():
    global A_POOL
    A_POOL.terminate()


@app.get("/")
async def read_root():
    message = f"GFW Tile Cache API"
    return {"message": message}


# app.mount("/static", StaticFiles(directory="/app/app/static"), name="static")
