from enum import Enum


class Dataset(str, Enum):
    nasa_viirs_fire_alerts = "nasa_viirs_fire_alerts"


class ViirsVersion(str, Enum):
    v20200224 = "v202003"
    latest = "latest"


class Implementation(str, Enum):
    default = "default"
