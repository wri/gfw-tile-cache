from enum import Enum


class SupportedAttributes(Enum):
    LATITUDE = "latitude"
    LONGITUDE = "longitude"
    ALERT_DATE = "alert__date"
    ALERT_TIME_UTC = "alert__time_utc"
    CONFIDENCE_CAT = "confidence__cat"
    BRIGHT_TI4_K = "bright_ti4__K"
    BRIGHT_TI5_K = "bright_ti5__K"
    FRP_MW = "frp__MW"

    def __str__(self):
        return self.value
