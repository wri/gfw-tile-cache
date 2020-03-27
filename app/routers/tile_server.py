import logging
from enum import Enum
from typing import Optional, Any, Dict, List, Tuple

import pendulum
from fastapi import APIRouter, Path, Query, HTTPException, Response
from sqlalchemy.sql import TableClause

from app.routers import DATE_REGEX, VERSION_REGEX
from app.services.vector_tiles import get_mvt_table, nasa_viirs_fire_alerts
from app.utils.tiles import to_bbox
from app.utils.filters import (
    geometry_filter,
    confidence_filter,
    date_filter,
    contextual_filter,
)
from app.utils.validators import (
    validate_dates,
    validate_bbox,
    validate_field_types,
    sanitize_fields,
)
from app.services import vector_tiles

LOGGER = logging.Logger(__name__)
router = APIRouter()
NOW = pendulum.now()

DEFAULT_START = NOW.subtract(weeks=1).to_date_string()
DEFAULT_END = NOW.to_date_string()

Geometry = Dict[str, Any]
Bounds = Tuple[float, float, float, float]


class Dataset(str, Enum):
    nasa_viirs_fire_alerts = "nasa_viirs_fire_alerts"


class ViirsVersion(str, Enum):
    v20200224 = "v202003"
    latest = "latest"


class Implementation(str, Enum):
    default = "default"


@router.get(
    "/nasa_viirs_fire_alerts/{version}/{implementation}/{z}/{x}/{y}.pbf",
    response_class=Response,
    tags=["tiles"],
)
async def nasa_viirs_fire_alerts_tile(
    version: ViirsVersion,
    implementation: Implementation,
    x: int = Path(..., title="Tile grid column", ge=0),
    y: int = Path(..., title="Tile grid row", ge=0),
    z: int = Path(..., title="Zoom level", ge=0, le=22),
    geostore_id: Optional[str] = Query(None),
    start_date: str = Query(DEFAULT_START, regex=DATE_REGEX),
    end_date: str = Query(DEFAULT_END, regex=DATE_REGEX),
    high_confidence_only: Optional[bool] = Query(False),
    is__regional_primary_forest: Optional[bool] = Query(None),
    is__alliance_for_zero_extinction_site: Optional[bool] = Query(None),
    is__key_biodiversity_area: Optional[bool] = Query(None),
    is__landmark: Optional[bool] = Query(None),
    gfw_plantation__type: Optional[str] = Query(None),
    is__gfw_mining: Optional[bool] = Query(None),
    is__gfw_logging: Optional[bool] = Query(None),
    rspo_oil_palm__certification_status: Optional[str] = Query(None),
    is__gfw_wood_fiber: Optional[bool] = Query(None),
    is__peat_land: Optional[bool] = Query(None),
    is__idn_forest_moratorium: Optional[bool] = Query(None),
    is__gfw_oil_palm: Optional[bool] = Query(None),
    idn_forest_area__type: Optional[str] = Query(None),
    per_forest_concession__type: Optional[str] = Query(None),
    is__gfw_oil_gas: Optional[bool] = Query(None),
    is__mangroves_2016: Optional[bool] = Query(None),
    is__intact_forest_landscapes_2016: Optional[bool] = Query(None),
    bra_biome__name: Optional[str] = Query(None),
) -> Response:
    """
    Router for VIIRS fire data
    """

    # TODO: There must be a better way!
    fields: Dict[str, Any] = {
        "is__regional_primary_forest": is__regional_primary_forest,
        "is__alliance_for_zero_extinction_site": is__alliance_for_zero_extinction_site,
        "is__key_biodiversity_area": is__key_biodiversity_area,
        "is__landmark": is__landmark,
        "gfw_plantation__type": gfw_plantation__type,
        "is__gfw_mining": is__gfw_mining,
        "is__gfw_logging": is__gfw_logging,
        "rspo_oil_palm__certification_status": rspo_oil_palm__certification_status,
        "is__gfw_wood_fiber": is__gfw_wood_fiber,
        "is__peat_land": is__peat_land,
        "is__idn_forest_moratorium": is__idn_forest_moratorium,
        "is__gfw_oil_palm": is__gfw_oil_palm,
        "idn_forest_area__type": idn_forest_area__type,
        "per_forest_concession__type": per_forest_concession__type,
        "is__gfw_oil_gas": is__gfw_oil_gas,
        "is__mangroves_2016": is__mangroves_2016,
        "is__intact_forest_landscapes_2016": is__intact_forest_landscapes_2016,
        "bra_biome__name": bra_biome__name,
    }

    fields = sanitize_fields(**fields)
    validate_field_types(**fields)
    validate_dates(start_date, end_date)

    bbox = to_bbox(x, y, z)
    validate_bbox(*bbox)

    filters = [
        await geometry_filter(geostore_id, bbox),
        confidence_filter(high_confidence_only),
        date_filter(start_date, end_date),
    ] + contextual_filter(**fields)

    filters = [f for f in filters if f is not None]

    if implementation == "default" and z >= 6:
        return await nasa_viirs_fire_alerts.get_tile(version, bbox, *filters)
    elif implementation == "default" and z < 6:
        return await nasa_viirs_fire_alerts.get_aggregated_tile(version, bbox, *filters)
    else:
        raise HTTPException(
            status_code=400, detail=f"Unknown Implementation {implementation}."
        )


@router.get(
    "/{dataset}/{version}/{implementation}/{z}/{x}/{y}.pbf",
    response_class=Response,
    tags=["tiles"],
)
async def tile(
    *,
    dataset: Dataset,
    version: str = Path(..., title="Dataset version", regex=VERSION_REGEX),
    implementation: Implementation,
    x: int = Path(..., title="Tile grid column", ge=0),
    y: int = Path(..., title="Tile grid row", ge=0),
    z: int = Path(..., title="Zoom level", ge=0, le=22),
    geostore_id: Optional[str] = Query(None),
) -> Response:
    """
    Generic router
    """

    bbox = to_bbox(x, y, z)
    validate_bbox(*bbox)

    filters: List[TableClause] = list()

    f = await geometry_filter(geostore_id, bbox)

    if f is not None:
        filters.append(f)

    if implementation == "default":
        query, values = get_mvt_table(dataset, version, bbox, list(), *filters)

        return await vector_tiles.get_tile(query)

    raise HTTPException(
        status_code=400, detail=f"Unknown implementation {implementation}"
    )


@router.get("/{dataset}/{version}/{implementation}/VectorTileServer", tags=["esri"])
async def esri_vector_tile_server(
    *,
    dataset: Dataset,
    version: str = Path(..., title="Dataset version", regex=VERSION_REGEX),
    implementation: Implementation,
    geostore_id: Optional[str] = Query(None),
):
    """
    Mocked ESRI Vector Tile Server
    """

    query_params: Optional[str] = f"geostore_id={geostore_id}" if geostore_id else None

    resolution = 78271.51696401172
    scale = 295829355.45453244

    response = {
        "currentVersion": 10.7,
        "name": f"{dataset} - {implementation} - {version}",
        "copyrightText": "",
        "capabilities": "TilesOnly",
        "type": "indexedVector",
        "defaultStyles": "resources/styles",
        "tiles": ["{z}/{x}/{y}.pbf" + (f"?{query_params}" if query_params else "")],
        "exportTilesAllowed": False,
        "initialExtent": {
            "xmin": -20037508.342787,
            "ymin": -20037508.342787,
            "xmax": 20037508.342787,
            "ymax": 20037508.342787,
            "spatialReference": {"wkid": 102100, "latestWkid": 3857},
        },
        "fullExtent": {
            "xmin": -20037508.342787,
            "ymin": -20037508.342787,
            "xmax": 20037508.342787,
            "ymax": 20037508.342787,
            "spatialReference": {"wkid": 102100, "latestWkid": 3857},
        },
        "minScale": 0,
        "maxScale": 0,
        "tileInfo": {
            "rows": 512,
            "cols": 512,
            "dpi": 96,
            "format": "pbf",
            "origin": {"x": -20037508.342787, "y": 20037508.342787},
            "spatialReference": {"wkid": 102100, "latestWkid": 3857},
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
        "serviceItemId": "274684d7a9d74ca4b87f529776feb3a2",
        # "maxExportTilesCount": 10000
    }
    return response
