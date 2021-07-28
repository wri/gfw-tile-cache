import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..crud.sync_db.tile_cache_assets import get_dataset_tile_caches
# from . import raster_tile_cache_version_dependency

router = APIRouter()

template_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, "templates"
)
templates = Jinja2Templates(directory=template_dir)


@router.get("/{dataset}/{version}/{implementation}/preview", response_class=HTMLResponse)
async def get_tile_caches(
    *,
    request: Request,
    dataset: str,
    version: str,
    # dv: Depends(raster_tile_cache_version_dependency),
    implementation
):
    """Map preview of availabe tile caches for a dataset."""

    # dataset, version = dv
    tile_caches = get_dataset_tile_caches(dataset, version)

    return templates.TemplateResponse(
        "tile_preview.html", context={"tiles": tile_caches, "request": request}
    )
