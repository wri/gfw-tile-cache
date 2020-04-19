from typing import Optional, Dict, Any, Tuple, Union

from fastapi import Query, Path

from app.routers import VERSION_REGEX
from app.schemas.dynamic_enumerators import get_dataset, get_viirs_version, Version
from app.utils.filters import geometry_filter
from app.utils.metadata import get_latest_version
from app.utils.tiles import to_bbox
from app.utils.validators import validate_version, validate_bbox


Bounds = Tuple[float, float, float, float]


async def xyz(
    x: int = Path(..., title="Tile grid column", ge=0),
    y: str = Path(
        ...,
        title="Tile grid row and optional scale factor (either @2x or @0.5x)",
        regex="^\d+(@(2|0.5|0.25)x)?$",
    ),
    z: int = Path(..., title="Zoom level", ge=0, le=22),
) -> Tuple[Bounds, int, int]:
    if "@" in y:
        __y, _scale = y.split("@")
        _y: int = int(__y)
        scale: float = float(_scale[:-1])
    else:
        _y = int(y)
        scale = 1.0

    extent: int = int(4096 * scale)
    bbox: Bounds = to_bbox(x, _y, z)
    validate_bbox(*bbox)
    return bbox, z, extent


async def nasa_viirs_fire_alerts_filters(
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
) -> Dict[str, Any]:
    return {
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


async def dataset_version(
    *,
    dataset: get_dataset(),  # type: ignore
    version: str = Path(..., title="Dataset version", regex=VERSION_REGEX),
):
    if version != "latest":
        validate_version(dataset, version)
    else:
        version = get_latest_version(dataset)

    return dataset, version


async def nasa_viirs_fire_alerts_version(
    version: get_viirs_version(),  # type: ignore
) -> Version:
    dataset = "nasa_viirs_fire_alerts"
    if version == "latest":
        validate_version(dataset, version)
    else:
        version = get_latest_version(dataset)

    return version
