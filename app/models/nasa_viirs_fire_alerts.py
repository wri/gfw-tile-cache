from datetime import date, time

from pydantic import BaseModel


class NasaViirsFireAlertsBase(BaseModel):
    latitude: float
    longitude: float
    alert__date: date
    alert__time_utc: time
    confidence__cat: str
    bright_ti4__K: float
    bright_ti5__K: float
    frp__MW: float


class NasaViirsFireAlertsExtended(NasaViirsFireAlertsBase):
    is__regional_primary_forest: bool
    is__alliance_for_zero_extinction_site: bool
    is__key_biodiversity_area: bool
    is__landmark: bool
    gfw_plantation__type: str
    is__gfw_mining: bool
    is__gfw_logging: bool
    rspo_oil_palm__certification_status: str
    is__gfw_wood_fiber: bool
    is__peat_land: bool
    is__idn_forest_moratorium: bool
    is__gfw_oil_palm: bool
    idn_forest_area__type: str
    per_forest_concession__type: str
    is__gfw_oil_gas: bool
    is__mangroves_2016: bool
    is__intact_forest_landscapes_2016: bool
    bra_biome__name: str
