from enum import Enum


class Implementation(str, Enum):
    default = "default"


class ViirsAttribute(str, Enum):
    latitude = "latitude"
    longitude = "longitude"
    alert__date = "alert__date"
    alert__time_utc = "alert__time_utc"
    confidence__cat = "confidence__cat"
    bright_ti4__k = "bright_ti4__k"
    bright_ti5__k = "bright_ti5__k"
    frp__mw = "frp__mw"
