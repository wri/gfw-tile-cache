from enum import Enum


class DeforestationAlertConfidence(str, Enum):
    nominal = "nominal"
    high = "high"
    highest = "highest"
