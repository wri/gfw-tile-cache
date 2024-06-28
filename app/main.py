"""isort:skip_file."""

import logging

from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.logger import logger
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.requests import Request
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from asyncio.exceptions import TimeoutError as AsyncTimeoutError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.errors import http_error_handler
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
from .routes.umd_modis_burned_areas import vector_tiles as burned_areas_tiles
from .routes.umd_tree_cover_loss import raster_tiles as umd_tree_cover_loss_raster_tiles
from .routes.umd_glad_landsat_alerts import (
    raster_tiles as umd_glad_landsat_alerts_raster_tiles,
)
from .routes.umd_glad_sentinel2_alerts import (
    raster_tiles as umd_glad_sentinel2_alerts_raster_tiles,
)
from .routes.wur_radd_alerts import raster_tiles as wur_radd_alerts_raster_tiles
from .routes.planet import raster_tiles as planet_raster_tiles
from .routes import wmts
from .routes import preview

from .routes.titiler import routes as titiler_routes

gunicorn_logger = logging.getLogger("gunicorn.error")
logger.handlers = gunicorn_logger.handlers

####################
## Routers
####################

ROUTERS = (
    viirs_vector_tiles.router,
    burned_areas_tiles.router,
    dynamic_vector_tiles.router,
    vector_tiles.router,
    umd_tree_cover_loss_raster_tiles.router,
    umd_glad_landsat_alerts_raster_tiles.router,
    umd_glad_sentinel2_alerts_raster_tiles.router,
    wur_radd_alerts_raster_tiles.router,
    planet_raster_tiles.router,
    raster_tiles.router,
    wmts.router,
    viirs_esri_vector_tile_server.router,
    esri_vector_tile_server.router,
    helpers.router,
    preview.router,
)

for r in ROUTERS:
    app.include_router(r)


# titiler routes
app.include_router(
    titiler_routes.cog.router, prefix="/cog/basic", tags=["Single COG Tiles"]
)
app.include_router(
    titiler_routes.mosaic.router, prefix="/cog/mosaic", tags=["Mosaic Tiles"]
)
app.include_router(
    titiler_routes.custom.router, prefix="/cog/custom", tags=["Custom Tiles"]
)


#####################
## Middleware
#####################

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(BaseHTTPMiddleware, dispatch=no_cache_response_header)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


################
# ERRORS
################


@app.exception_handler(AsyncTimeoutError)
async def timeout_error_handler(
    request: Request, exc: AsyncTimeoutError
) -> ORJSONResponse:
    """Use JSEND protocol for validation errors."""
    return ORJSONResponse(
        status_code=524,
        content={
            "status": "error",
            "message": "A timeout occurred while processing the request. Request canceled.",
        },
    )


@app.exception_handler(HTTPException)
async def httpexception_error_handler(
    request: Request, exc: HTTPException
) -> ORJSONResponse:
    """Use JSEND protocol for HTTP exceptions."""
    return http_error_handler(exc)


# Correctly formats 404 responses
@app.exception_handler(StarletteHTTPException)
async def starlettehttpexception_error_handler(
    request: Request, exc: StarletteHTTPException
) -> ORJSONResponse:
    """Use JSEND protocol for HTTP exceptions."""
    return http_error_handler(exc)


@app.exception_handler(RequestValidationError)
async def rve_error_handler(
    request: Request, exc: RequestValidationError
) -> ORJSONResponse:
    """Use JSEND protocol for validation errors."""
    return ORJSONResponse(
        status_code=422,
        content={"status": "failed", "message": exc.errors()},
    )


@app.exception_handler(Exception)
async def catch_all_handler(request: Request, exc: Exception) -> ORJSONResponse:
    """Use JSEND protocol for validation errors."""
    # FixMe: While the exception is correctly formatted, this still throws the actual exception.
    #  this might be related to https://github.com/tiangolo/fastapi/issues/2750
    #  other ways to catch any uncaught exception did not work
    #  - creating a custom router resulting in catching any exception, even 422 errors
    #  - adding an extra piece of middleware to catch exceptions interferes with background tasks.
    #  While not perfect the current implementation does it job. The user gets a correctly parsed response,
    #  and there is no need to log the error, since the exception is thrown anyways
    return ORJSONResponse(
        status_code=500, content={"status": "error", "message": "Internal Server Error"}
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
    {"name": "Dynamic COG Tiles", "description": titiler_routes.__doc__},
    {
        "name": "ESRI Vector Tile Service",
        "description": esri_vector_tile_server.__doc__,
    },
    {"name": "Tile Cache Preview", "description": preview.__doc__},
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
        {
            "name": "Titiler COG Tiles",
            "tags": ["Single COG Tiles", "Mosaic Tiles", "Custom Tiles"],
        },
        {"name": "ESRI Vector Tile Server API", "tags": ["ESRI Vector Tile Service"]},
        {"name": "Map Preview", "tags": ["Tile Cache Preview"]},
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
