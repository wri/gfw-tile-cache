import hashlib
from typing import Dict, Any


async def get_vector_tile_server(
    dataset: str, implementation: str, version: str, query_params: str, levels=1
) -> Dict[str, Any]:
    resolution = 78271.51696401172
    scale = 295829355.45453244
    min = -20037508.342787
    max = 20037508.342787
    spatial_reference = {"wkid": 102100, "latestWkid": 3857}
    extent = {
        "xmin": min,
        "ymin": min,
        "xmax": max,
        "ymax": max,
        "spatialReference": spatial_reference,
    }
    name = f"{dataset} - {implementation} - {version}"

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
            "origin": {"x": min, "y": max},
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
