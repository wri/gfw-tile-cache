import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..crud.sync_db.tile_cache_assets import get_dataset_tile_caches

router = APIRouter()

template_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, "templates"
)
templates = Jinja2Templates(directory=template_dir)


@router.get(
    "/{dataset}/{version}/{implementation}/preview", response_class=HTMLResponse
)
async def get_tile_caches(
    *, request: Request, dataset: str, version: str, implementation
):
    """Map preview of availabe tile caches for a dataset."""

    tile_caches = get_dataset_tile_caches(dataset, version, implementation)

    return templates.TemplateResponse(
        "tile_preview.html", context={"tiles": tile_caches, "request": request}
    )
