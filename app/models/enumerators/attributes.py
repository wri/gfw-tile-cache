from aenum import Enum


class Attributes(str, Enum):
    __doc__ = "Attribute name"


class TcdEnum(str, Enum):
    tcd_10 = "10"
    tcd_15 = "15"
    tcd_20 = "20"
    tcd_25 = "25"
    tcd_30 = "30"
    tcd_50 = "50"
    tcd_75 = "75"


class TcdStyleEnum(str, Enum):
    tcd_10 = "tcd_10"
    tcd_15 = "tcd_15"
    tcd_20 = "tcd_20"
    tcd_25 = "tcd_25"
    tcd_30 = "tcd_30"
    tcd_50 = "tcd_50"
    tcd_75 = "tcd_75"
