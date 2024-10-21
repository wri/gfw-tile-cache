from enum import Enum


class AlertConfidence(str, Enum):
    low = "low"
    high = "high"
    highest = "highest"
