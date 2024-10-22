from enum import Enum


class AlertConfidence(str, Enum):
    low = "low"
    high = "high"
    highest = "highest"


class RenderType(str, Enum):
    true_color = "true_color"
    encoded = "encoded"
