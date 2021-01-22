"""

    isort:skip_file
"""
import json
import logging

from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.logger import logger
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware


from .middleware import no_cache_response_header
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
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(BaseHTTPMiddleware, dispatch=no_cache_response_header)

#####################
# Errors
#####################


@app.exception_handler(HTTPException)
async def httpexception_error_handler(request: Request, exc: HTTPException):
    if exc.status_code < 500:
        status = "failed"
    else:
        status = "error"
    return JSONResponse(
        status_code=exc.status_code, content={"status": status, "message": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def rve_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422, content={"status": "failed", "message": json.loads(exc.json())}
    )


#################
# STATIC FILES
#################

app.mount("/static", StaticFiles(directory="/app/app/static"), name="static")


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
    )

    openapi_schema["tags"] = tags_metadata
    openapi_schema["info"]["x-logo"] = {"url": "/static/gfw-tile-cache.png"}
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
