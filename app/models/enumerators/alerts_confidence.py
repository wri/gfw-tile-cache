from enum import Enum


class DeforestationAlertConfidence(str, Enum):
    low = "low"
    high = "high"
    highest = "highest"
