import hashlib
from typing import Any, Dict, List, Optional, Tuple

import pendulum
from fastapi import APIRouter, Depends, Path, Query

from ..models.pydantic.esri import VectorTileService
from . import (
    DATE_REGEX,
    dynamic_version_dependency,
    include_attributes,
    static_version_dependency,
)
from .nasa_viirs_fire_alerts import (
    nasa_viirs_fire_alerts_filters,
    nasa_viirs_fire_alerts_version,
)

router = APIRouter()
NOW = pendulum.now()

DEFAULT_START = NOW.subtract(weeks=1).to_date_string()
DEFAULT_END = NOW.to_date_string()

Geometry = Dict[str, Any]
Bounds = Tuple[float, float, float, float]


@router.get(
    "/nasa_viirs_fire_alerts/{version}/dynamic/{start_date}/{end_date}/VectorTileServer",
    tags=["ESRI Vector Tile Service"],
    response_model=VectorTileService,
)
async def nasa_viirs_fire_alerts_esri_vector_tile_service_dates(
    *,
    version: str = Depends(nasa_viirs_fire_alerts_version),  # type: ignore
    start_date: str = Path(
        ..., regex=DATE_REGEX, title="Only show alerts for given date and after",
    ),
    end_date: str = Path(
        ..., regex=DATE_REGEX, title="Only show alerts until given date."
    ),
    geostore_id: Optional[str] = Query(None),
    force_date_range: Optional[bool] = Query(
        False,
        title="Bypass the build in limitation to query more than 90 days at a time. Use cautiously!",
    ),
    high_confidence_only: Optional[bool] = Query(
        False, title="Only show high confidence alerts"
    ),
    include_attribute: List[str] = Depends(include_attributes),
    contextual_filters: dict = Depends(nasa_viirs_fire_alerts_filters),
):
    """
    Mock ESRI Vector Tile Server for NASA VIIRS fire alerts.
    When using ESRI JS API, point your root.json to this URL.
    URL Parameters will be forwarded to tile cache.
    """

    fields: Dict[str, Any] = contextual_filters

    fields["geostore_id"] = geostore_id
    fields["start_date"] = start_date
    fields["end_date"] = end_date
    fields["high_confidence_only"] = high_confidence_only
    fields["force_date_range"] = force_date_range
    # fields["include_attribute"] = include_attribute

    params = [f"{key}={value}" for key, value in fields.items() if value is not None]

    for attribute in include_attribute:
        params.append(f"include_attribute={attribute}")

    query_params: str = "&".join(params)

    # TODO: add scale factor to tile url
    return await get_vector_tile_server(
        "nasa_viirs_fire_alerts", version, "default", query_params, levels=3
    )


@router.get(
    "/nasa_viirs_fire_alerts/{version}/dynamic/VectorTileServer",
    tags=["ESRI Vector Tile Service"],
    response_model=VectorTileService,
)
async def nasa_viirs_fire_alerts_esri_vector_tile_service(
    *,
    version: str = Depends(nasa_viirs_fire_alerts_version),  # type: ignore
    geostore_id: Optional[str] = Query(None),
    start_date: str = Query(
        DEFAULT_START,
        regex=DATE_REGEX,
        title="Only show alerts for given date and after",
    ),
    end_date: str = Query(
        DEFAULT_END, regex=DATE_REGEX, title="Only show alerts until given date."
    ),
    force_date_range: Optional[bool] = Query(
        False,
        title="Bypass the build in limitation to query more than 90 days at a time. Use cautiously!",
    ),
    high_confidence_only: Optional[bool] = Query(
        False, title="Only show high confidence alerts"
    ),
    include_attribute: List[str] = Depends(include_attributes),
    contextual_filters: dict = Depends(nasa_viirs_fire_alerts_filters),
):
    """
    Mock ESRI Vector Tile Server for NASA VIIRS fire alerts.
    When using ESRI JS API, point your root.json to this URL.
    URL Parameters will be forwarded to tile cache.
    """

    fields: Dict[str, Any] = contextual_filters

    fields["geostore_id"] = geostore_id
    fields["start_date"] = start_date
    fields["end_date"] = end_date
    fields["high_confidence_only"] = high_confidence_only
    fields["force_date_range"] = force_date_range
    # fields["include_attribute"] = include_attribute

    params = [f"{key}={value}" for key, value in fields.items() if value is not None]

    for attribute in include_attribute:
        params.append(f"include_attribute={attribute}")

    query_params: str = "&".join(params)

    # TODO: add scale factor to tile url
    return await get_vector_tile_server(
        "nasa_viirs_fire_alerts", version, "default", query_params
    )


@router.get(
    "/{dataset}/{version}/dynamic/VectorTileServer",
    tags=["ESRI Vector Tile Service"],
    response_model=VectorTileService,
)
async def dynamic_esri_vector_tile_service(
    *,
    dv: Tuple[str, str] = Depends(dynamic_version_dependency),
    geostore_id: Optional[str] = Query(None),
):
    """
    Generic Mock ESRI Vector Tile Server.
    When using ESRI JS API, point your root.json to this URL.
    URL Parameters will be forwarded to tile cache.
    """

    dataset, version = dv
    query_params: str = f"geostore_id={geostore_id}" if geostore_id else ""

    return await get_vector_tile_server(dataset, version, "dynamic", query_params)


@router.get(
    "/{dataset}/{version}/default/VectorTileServer",
    tags=["ESRI Vector Tile Service"],
    response_model=VectorTileService,
)
async def esri_vector_tile_service(
    *, dv: Tuple[str, str] = Depends(static_version_dependency),
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
