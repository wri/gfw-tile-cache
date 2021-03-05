from aenum import Enum


class Attributes(str, Enum):
    __doc__ = "Attribute name"


class TcdEnum(str, Enum):
    ten = "10"
    fifteen = "15"
    twenty = "20"
    twentyfive = "25"
    thirty = "30"
    fifty = "50"
    seventyfive = "75"
