from enum import Enum


class AlertConfidence(str, Enum):
    low = "low"
    high = "high"


class IntegratedAlertConfidence(str, Enum):
    low = "low"
    high = "high"
    highest = "highest"


class RenderType(str, Enum):
    true_color = "true_color"
    encoded = "encoded"


class TreeCoverDensityThreshold(str, Enum):
    tcd_30 = 30
    tcd_50 = 50
    tcd_75 = 75
