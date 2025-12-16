# After upgrading to Python 3.11, this can become just
# from enum import StrEnum
try:
    from enum import StrEnum
except ImportError:
    from enum import Enum
    class StrEnum(str, Enum):
        pass


class Attributes(StrEnum):
    __doc__ = "Attribute name"


class TcdEnum(StrEnum):
    tcd_10 = "10"
    tcd_15 = "15"
    tcd_20 = "20"
    tcd_25 = "25"
    tcd_30 = "30"
    tcd_50 = "50"
    tcd_75 = "75"


class TcdStyleEnum(StrEnum):
    tcd_10 = "tcd_10"
    tcd_15 = "tcd_15"
    tcd_20 = "tcd_20"
    tcd_25 = "tcd_25"
    tcd_30 = "tcd_30"
    tcd_50 = "tcd_50"
    tcd_75 = "tcd_75"
