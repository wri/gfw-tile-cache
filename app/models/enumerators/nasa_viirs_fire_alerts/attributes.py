from typing import List

from aenum import Enum, extend_enum


class Attributes(str, Enum):
    __doc__ = "NASA VIIRS fire alerts attributes"


def get_attributes_enum(attributes: List[str]) -> List[Attributes]:
    for attribute in attributes:
        extend_enum(Attributes, attribute, attribute)
    return Attributes
