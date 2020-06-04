from enum import Enum
from typing import Optional, Dict, Any, Tuple, Union, List

from fastapi import Query, Path, HTTPException

from app.routers import VERSION_REGEX, DATE_REGEX

# from app.routers.tile_server import DEFAULT_START, DEFAULT_END
from app.schemas.dynamic_enumerators import get_dataset, get_viirs_version, Version
from app.utils.filters import geometry_filter
from app.utils.metadata import get_latest_version
from app.utils.tiles import to_bbox
from app.utils.validators import validate_version, validate_bbox

Bounds = Tuple[float, float, float, float]


class ViirsAttribute(str, Enum):
    latitude = "latitude"
    longitude = "longitude"
    alert__date = "alert__date"
    alert__time_utc = "alert__time_utc"
    confidence__cat = "confidence__cat"
    bright_ti4__k = "bright_ti4__k"
    bright_ti5__k = "bright_ti5__k"
    frp__mw = "frp__mw"


# ALLOWED_ATTRIBUTES: List[str] = [
#     "latitude",
#     "longitude",
#     "alert__date",
#     "alert__time_utc",
#     "confidence__cat",
#     "bright_ti4__k",
#     "bright_ti5__k",
#     "frp__mw",
# ]


async def xyz(
    z: int = Path(..., title="Zoom level", ge=0, le=22),
    x: int = Path(..., title="Tile grid column", ge=0),
    y: Union[int, str] = Path(
        ...,
        title="Tile grid row (integer >= 0) and optional scale factor (either @2x, @0.5x or @0.25x)",
        regex="^\d+(@(2|0.5|0.25)x)?$",
    ),
) -> Tuple[Bounds, int, int]:
    if isinstance(y, str) and "@" in y:
        __y, _scale = y.split("@")
        _y: int = int(__y)
        scale: float = float(_scale[:-1])
    elif isinstance(y, int):
        _y = y
        scale = 1.0
    else:
        raise HTTPException(
            400,
            detail="Y value must be either integer of combination and integer and scale factor",
        )

    extent: int = int(4096 * scale)
    bbox: Bounds = to_bbox(x, _y, z)
    validate_bbox(*bbox)
    return bbox, z, extent


async def include_attributes(
    include_attribute: Optional[List[ViirsAttribute]] = Query(
        ["frp__mw"],
        title="Select which attributes to include in vector tile. Will always show attribute count.",
    ),
) -> List[str]:
    attributes: List[str] = list()
    if include_attribute:
        for attribute in include_attribute:
            attributes.append(attribute.value)
    return attributes


async def nasa_viirs_fire_alerts_filters(
    is__regional_primary_forest: Optional[bool] = Query(
        None, title="Only show alerts inside regional primary forests"
    ),
    is__alliance_for_zero_extinction_site: Optional[bool] = Query(
        None, title="Only show alerts inside alliance for zero extinction sites"
    ),
    is__key_biodiversity_area: Optional[bool] = Query(
        None, title="Only show alerts inside key biodiversity areas"
    ),
    is__landmark: Optional[bool] = Query(
        None, title="Only show alerts inside landmark land right areas"
    ),
    gfw_plantation__type: Optional[str] = Query(
        None, title="Only show alerts inside selected GFW plantation types"
    ),
    is__gfw_mining: Optional[bool] = Query(
        None, title="Only show alerts inside mining permits"
    ),
    is__gfw_logging: Optional[bool] = Query(
        None, title="Only show alerts inside managed forests"
    ),
    rspo_oil_palm__certification_status: Optional[str] = Query(
        None, title="Only show alerts inside areas with selected rspo oil palm status"
    ),
    is__gfw_wood_fiber: Optional[bool] = Query(
        None, title="Only show alerts inside wood fiber concessions"
    ),
    is__peat_land: Optional[bool] = Query(
        None, title="Only show alerts inside peat land"
    ),
    is__idn_forest_moratorium: Optional[bool] = Query(
        None, title="Only show alerts inside indonesia forest moratorium areas"
    ),
    is__gfw_oil_palm: Optional[bool] = Query(
        None, title="Only show alerts inside oil palm concessions"
    ),
    idn_forest_area__type: Optional[str] = Query(
        None, title="Only show alerts inside selected forest area type in Indonesia"
    ),
    per_forest_concession__type: Optional[str] = Query(
        None, title="Only show alerts inside selected forest concessions type in Peru"
    ),
    is__gfw_oil_gas: Optional[bool] = Query(
        None, title="Only show alerts inside oil and gas concessions"
    ),
    is__mangroves_2016: Optional[bool] = Query(
        None, title="Only show alerts inside 2016 mangrove extent"
    ),
    is__intact_forest_landscapes_2016: Optional[bool] = Query(
        None, title="Only show alerts inside 2016 intact forest landscape extent"
    ),
    bra_biome__name: Optional[str] = Query(
        None, title="Only show alerts inside selected biome in Brazil"
    ),
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
        version = "v202003"  # TODO fix dependencies get_latest_version(dataset)

    return dataset, version


async def nasa_viirs_fire_alerts_version(
    version: get_viirs_version(),  # type: ignore
) -> Version:
    # dataset = "nasa_viirs_fire_alerts"
    if version == "latest":
        version = "v202003"  # validate_version(dataset, version)
    else:
        version = "v202003"  # TODO fix dependencies get_latest_version(dataset)

    return version
