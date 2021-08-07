import json
import os

import aioboto3
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..crud.sync_db.tile_cache_assets import get_dataset_tile_caches
from ..settings.globals import GLOBALS

router = APIRouter()

template_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, "templates"
)
templates = Jinja2Templates(directory=template_dir)


@router.get(
    "/{dataset}/{version}/{implementation}/preview", response_class=HTMLResponse
)
async def get_tile_cache_preview(
    *, request: Request, dataset: str, version: str, implementation
):
    """Map preview of availabe tile caches for a dataset."""

    tile_caches = get_dataset_tile_caches(dataset, version, implementation)
    sources = {
        "carto-dark": {
            "type": "raster",
            "tiles": [
                "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
                "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
                "https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
                "https://d.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
            ],
        },
    }

    layers = [
        {
            "id": "carto-dark-layer",
            "type": "raster",
            "source": "carto-dark",
            "minzoom": 0,
            "maxzoom": 22,
        },
    ]
    for tile in tile_caches:
        if tile["asset_type"] == "Static vector tile cache":
            style_specs = await get_static_vector_tile_cache_style_spec(tile)
            layers = [*layers, *style_specs["layers"]]
            sources[dataset] = style_specs["sources"][dataset]
        else:
            mapbox_style = get_default_style_spec(tile)
            sources[dataset] = mapbox_style["source"]
            layers.append(mapbox_style["layer"])

    return templates.TemplateResponse(
        "tile_preview.html",
        context={"sources": sources, "layers": layers, "request": request},
    )


async def get_static_vector_tile_cache_style_spec(tile):
    "Fetch static vector tile cache style specification from s3"
    root_json_key = (
        f"{tile['dataset']}/{tile['version']}/{tile['implementation']}/root.json"
    )
    session = aioboto3.Session()
    async with session.client(
        "s3", region_name=GLOBALS.aws_region, endpoint_url=GLOBALS.aws_endpoint_uri
    ) as s3_client:
        s3_object = await s3_client.get_object(Bucket=GLOBALS.bucket, Key=root_json_key)
        data = await s3_object["Body"].read()

        return json.loads(data)


def get_default_style_spec(tile):
    "Construct default tile source and layer style for Mapbox rendering"
    source = {
        "type": "vector" if "vector" in tile["asset_type"].lower() else "raster",
        "tiles": [tile["asset_uri"]],
    }
    layer = {
        "id": f"{tile['dataset']}-layer",
        "type": "fill" if "vector" in tile["asset_type"].lower() else "raster",
        "source": tile["dataset"],
        "minzoom": tile["min_zoom"],
        "maxzoom": tile["max_zoom"],
        "source-layer": tile["dataset"],
    }

    if "vector" in tile["asset_type"].lower():
        layer["paint"] = {
            "fill-color": "#0080ff",  # blue color fill
            "fill-opacity": 0.5,
        }

    return {"source": source, "layer": layer}
