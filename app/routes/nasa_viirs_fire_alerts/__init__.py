from typing import Any, Dict, List, Optional

from fastapi import Query

from app.crud.vector_tile_assets import get_latest_dynamic_version
from app.models.pydantic.dynamic_enumerators import get_attributes

dataset_name = "nasa_viirs_fire_alerts"
IncludedAttributes = Optional[  # type: ignore
    List[get_attributes(dataset_name, get_latest_dynamic_version(dataset_name))]  # type: ignore
]


async def include_attributes(
    include_attribute: IncludedAttributes = Query(  # type: ignore
        ["frp__mw"],
        title="Included Attributes",
        description="Select which attributes to include in vector tile. Will always show attribute count. "
        "Documentation list available attributes of latest version. For legacy version "
        "please check data-api for available attribute values.",
    ),
) -> List[str]:
    attributes: List[str] = list()
    if include_attribute:
        for attribute in include_attribute:  # type: ignore
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
