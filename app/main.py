"""

    isort:skip_file
"""
import logging

from fastapi.logger import logger
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.utils import get_openapi

from .application import app
from .routes import (
    esri_vector_tile_server,
    raster_tiles,
    vector_tiles,
    dynamic_vector_tiles,
    helpers,
)
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
    dynamic_vector_tiles.router,
    vector_tiles.router,
    raster_tiles.router,
    viirs_esri_vector_tile_server.router,
    esri_vector_tile_server.router,
    helpers.router,
)

for r in ROUTERS:
    app.include_router(r)


#####################
## Middleware
#####################

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


#####################
## OpenAPI
#####################

# Trying to add metadata tags directly to app causes a circular import. Hence this monkey patch.

tags_metadata = [
    {"name": "Dynamic Vector Tiles", "description": dynamic_vector_tiles.__doc__},
    {"name": "Vector Tiles", "description": vector_tiles.__doc__},
    {"name": "Raster Tiles", "description": raster_tiles.__doc__},
    {
        "name": "ESRI Vector Tile Service",
        "description": esri_vector_tile_server.__doc__,
    },
]


def custom_openapi(openapi_prefix: str = ""):
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="GFW Tile Cache API",
        version="0.1.0",
        description="Use GFW Tile Cache to retrieve vector and raster tiles.",
        routes=app.routes,
        openapi_prefix=openapi_prefix,
    )

    openapi_schema["tags"] = tags_metadata
    # openapi_schema["info"]["x-logo"] = {"url": "/static/gfw-data-api.png"}
    openapi_schema["x-tagGroups"] = [
        {"name": "Vector Tiles API", "tags": ["Dynamic Vector Tiles", "Vector Tiles"]},
        {"name": "Raster Tiles API", "tags": ["Raster Tiles"]},
        {"name": "ESRI Vector Tile Server API", "tags": ["ESRI Vector Tile Service"]},
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn

    logger.setLevel(logging.DEBUG)
    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="info")
else:
    logger.setLevel(gunicorn_logger.level)
