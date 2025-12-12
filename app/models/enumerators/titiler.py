# After upgrading to Python 3.11, this can become just
# from enum import StrEnum
try:
    from enum import StrEnum
except ImportError:
    from enum import Enum
    class StrEnum(str, Enum):
        pass


class AlertConfidence(StrEnum):
    low = "low"
    high = "high"


class IntegratedAlertConfidence(StrEnum):
    low = "low"
    high = "high"
    highest = "highest"


class RenderType(StrEnum):
    true_color = "true_color"
    encoded = "encoded"


class TreeCoverDensityThreshold(StrEnum):
    tcd_30 = "30"
    tcd_50 = "50"
    tcd_75 = "75"


class TCLTreeCoverDensityThreshold(StrEnum):
    tcd_10 = "10"
    tcd_15 = "15"
    tcd_20 = "20"
    tcd_25 = "25"
    tcd_30 = "30"
    tcd_50 = "50"
    tcd_75 = "75"
    tcd_90 = "90"
