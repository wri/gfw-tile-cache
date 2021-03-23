"""

    isort:skip_file
"""
import json
import logging

from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.logger import logger
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from .middleware import no_cache_response_header, TileCacheCORSMiddleware
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
from .routes.umd_tree_cover_loss import raster_tiles as umd_tree_cover_loss_raster_tiles
from .routes.umd_glad_alerts import raster_tiles as umd_glad_alerts_raster_tiles
from .routes.wur_radd_alerts import raster_tiles as wur_radd_alerts_raster_tiles
from .routes.planet import raster_tiles as planet_raster_tiles
from .routes import wmts

gunicorn_logger = logging.getLogger("gunicorn.error")
logger.handlers = gunicorn_logger.handlers

####################
## Routers
####################

ROUTERS = (
    viirs_vector_tiles.router,
    dynamic_vector_tiles.router,
    vector_tiles.router,
    umd_tree_cover_loss_raster_tiles.router,
    umd_glad_alerts_raster_tiles.router,
    wur_radd_alerts_raster_tiles.router,
    planet_raster_tiles.router,
    raster_tiles.router,
    wmts.router,
    viirs_esri_vector_tile_server.router,
    esri_vector_tile_server.router,
    helpers.router,
)

for r in ROUTERS:
    app.include_router(r)

#####################
## Middleware
#####################

gfw_apps = [
    "https://www.globalforestwatch.org",
    "https://pro.globalforestwatch.org",
    "https://forestwatcher.globalforestwatch.org",
    "https://my.gfw-mapbuilder.org",
    "cmr.forest-atlas.org",
    "cmr.atlas-forestier.org",
    "cmr.forestatlas.org",
    "cmr.atlasforestier.org",
    "caf.forest-atlas.org",
    "caf.atlas-forestier.org",
    "caf.forestatlas.org",
    "caf.atlasforestier.org",
    "rca.atlas-forestier.org",
    "rca.atlasforestier.org",
    "cod.forest-atlas.org",
    "drc.forest-atlas.org",
    "rdc.atlas-forestier.org",
    "cod.atlas-forestier.org",
    "cod.forestatlas.org",
    "drc.forestatlas.org",
    "rdc.atlasforestier.org",
    "cod.atlasforestier.org",
    "gnq.forest-atlas.org",
    "gnq.atlas-forestier.org",
    "gnq.atlas-forestal.org",
    "gnq.forestatlas.org",
    "gnq.atlasforestier.org",
    "cog.forest-atlas.org",
    "cog.atlas-forestier.org",
    "cog.forestatlas.org",
    "cog.atlasforestier.org",
    "gab.forest-atlas.org",
    "gab.atlas-forestier.org",
    "gab.forestatlas.org",
    "gab.atlasforestier.org",
    "atlas.mepa.gov.ge",
    "geo.forest-atlas.org",
    "geo.forestatlas.org",
    "lbr.forest-atlas.org",
    "lbr.forestatlas.org",
    "mdg.forest-atlas.org",
    "mdg.atlas-forestier.org",
    "mdg.forestatlas.org",
    "mdg.atlasforestier.org",
    "www.tierrasindigenas.org",
    "tierrasindigenas.org",
    "ind.restorationatlas.org",
    "ind.restoration-atlas.org",
    "india.restorationatlas.org",
    "india.restoration-atlas.org",
    "www.india.restorationatlas.org",
    "sidhi.restorationatlas.org",
    "sidhi.restoration-atlas.org",
    "vp.restorationatlas.org",
    "vp.restoration-atlas.org",
    "eth.restorationatlas.org",
    "eth.restoration-atlas.org",
    "cmr.amenagement-territoire.org",
    "cog.amenagement-territoire.org",
    "cog.reddregistry.org",
    "cog.registre-redd.org",
    "www.restauracaovaledoparaiba.org.br",
    "forum-florestal.doesntexist.org",
    "monitoramentobahia.dialogoflorestal.org.br",
]


app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    TileCacheCORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    exclude_routes=[r"\/planet\/.*"],
)
app.add_middleware(
    TileCacheCORSMiddleware,
    allow_origins=gfw_apps,
    allow_methods=["*"],
    allow_headers=["*"],
    include_routes=[r"\/planet\/.*"],
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
