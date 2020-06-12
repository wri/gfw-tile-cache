"""

    isort:skip_file
"""
import logging

from fastapi.logger import logger
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .application import app
from .middleware import redirect_latest
from .routes import esri_vector_tile_server, raster_tiles, vector_tiles
from .routes.nasa_viirs_fire_alerts import (
    esri_vector_tile_server as viirs_esri_vector_tile_server,
)
from .routes.nasa_viirs_fire_alerts import vector_tiles as viirs_vector_tiles

gunicorn_logger = logging.getLogger("gunicorn.error")
logger.handlers = gunicorn_logger.handlers


####################
## Routers
####################

ROUTERS = (
    viirs_vector_tiles.router,
    vector_tiles.router,
    raster_tiles.router,
    viirs_esri_vector_tile_server.router,
    esri_vector_tile_server.router,
)

for r in ROUTERS:
    app.include_router(r)


#####################
## Middleware
#####################

MIDDLEWARE = (redirect_latest,)

for m in MIDDLEWARE:
    app.add_middleware(BaseHTTPMiddleware, dispatch=m)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


@app.get("/")
async def read_root():
    message = "GFW Tile Cache API"
    return {"message": message}


# app.mount("/static", StaticFiles(directory="/app/app/static"), name="static")

if __name__ == "__main__":
    import uvicorn

    logger.setLevel(logging.DEBUG)
    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="info")
else:
    logger.setLevel(gunicorn_logger.level)
