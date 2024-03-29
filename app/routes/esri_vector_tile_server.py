"""
ESRI JS API requires tile to come from a ESRI VectorTileServer.
This endpoint mocks the responds of such server and routes the web client to the correct tiles.

The mocked Dynamic Vector Tile Server will also forward any query parameters in the URL to the tile cache.
However, currently, ESRI JS API does not support the use of query parameters and removed them before making the request.
Hence this feature might not work in a ESRI applications.
"""

import hashlib
from typing import Any, Dict, Optional, Tuple

from fastapi import APIRouter, Depends, Query

from ..models.pydantic.esri import RootJson, VectorTileService
from . import (
    dynamic_vector_tile_cache_version_dependency,
    static_vector_tile_cache_version_dependency,
)

router = APIRouter()


@router.get(
    "/{dataset}/{version}/dynamic/VectorTileServer",
    tags=["ESRI Vector Tile Service"],
    response_model=VectorTileService,
)
async def dynamic_esri_vector_tile_service(
    *,
    dv: Tuple[str, str] = Depends(dynamic_vector_tile_cache_version_dependency),
    geostore_id: Optional[str] = Query(None),
):
    """
    Generic Mock ESRI Vector Tile Server.
    When using ESRI JS API, point your root.json to this URL.
    URL Parameters will be forwarded to tile cache.
    """

    dataset, version = dv
    query_params: str = f"geostore_id={geostore_id}" if geostore_id else ""

    return await _get_vector_tile_server(dataset, version, "dynamic", query_params)


@router.get(
    "/{dataset}/{version}/default/VectorTileServer",
    tags=["ESRI Vector Tile Service"],
    response_model=VectorTileService,
)
async def esri_vector_tile_service(
    *,
    dv: Tuple[str, str] = Depends(static_vector_tile_cache_version_dependency),
):
    """
    Generic Mock ESRI Vector Tile Server.
    When using ESRI JS API, point your root.json to this URL.
    URL Parameters will be forwarded to tile cache.
    """
    # This endpoint is not implemented and only exist for documentation purposes
    # Default vector layers are stored on S3.
    # If tile is not found, Cloud Front will redirect request to dynamic endpoint.
    # Hence, this function should never be called.

    raise NotImplementedError


@router.get(
    "/{dataset}/{version}/default/root.json",
    tags=["ESRI Vector Tile Service"],
    response_model=RootJson,
)
async def esri_root_json(
    *,
    dv: Tuple[str, str] = Depends(static_vector_tile_cache_version_dependency),
):
    """
    ESRI root.json file with default layer style for use with ESRI JS API.
    """
    # This endpoint is not implemented and only exist for documentation purposes
    # Default vector layers are stored on S3. root.json files are static and are created in data-api.

    raise NotImplementedError


async def _get_vector_tile_server(
    dataset: str, version: str, implementation: str, query_params: str = None, levels=1
) -> Dict[str, Any]:
    resolution = 78271.51696401172
    scale = 295829355.45453244
    _min = -20037508.342787
    _max = 20037508.342787
    spatial_reference = {"wkid": 102100, "latestWkid": 3857}
    extent = {
        "xmin": _min,
        "ymin": _min,
        "xmax": _max,
        "ymax": _max,
        "spatialReference": spatial_reference,
    }
    name = f"{dataset} - {version} - {implementation}"

    levels_down = list()
    for i in range(levels):
        levels_down.append("..")

    prefix = "/".join(levels_down)

    response = {
        "currentVersion": 10.7,
        "name": name,
        "copyrightText": "",
        "capabilities": "TilesOnly",
        "type": "indexedVector",
        "defaultStyles": "resources/styles",
        "tiles": [
            prefix
            + "/{z}/{x}/{y}@0.25x.pbf"
            + (f"?{query_params}" if query_params else "")
        ],
        "exportTilesAllowed": False,
        "initialExtent": extent,
        "fullExtent": extent,
        "minScale": 0,
        "maxScale": 0,
        "tileInfo": {
            "rows": 512,
            "cols": 512,
            "dpi": 96,
            "format": "pbf",
            "origin": {"x": _min, "y": _max},
            "spatialReference": spatial_reference,
            "lods": [
                {
                    "level": i,
                    "resolution": resolution / (2 ** i),
                    "scale": scale / (2 ** i),
                }
                for i in range(0, 23)
            ],
        },
        "maxzoom": 22,
        "minLOD": 0,
        "maxLOD": 16,
        "resourceInfo": {
            "styleVersion": 8,
            "tileCompression": "gzip",
            "cacheInfo": {
                "storageInfo": {"packetSize": 128, "storageFormat": "compactV2"}
            },
        },
        "serviceItemId": hashlib.md5(name.encode()).hexdigest(),
    }
    return response
