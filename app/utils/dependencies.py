from typing import Optional

from fastapi import Query, Path

from app.routers import VERSION_REGEX
from app.schemas.dynamic_enumerators import get_dataset, get_viirs_version, Version
from app.schemas.enumerators import Implementation
from app.utils.metadata import get_latest_version
from app.utils.validators import validate_version


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
):
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
