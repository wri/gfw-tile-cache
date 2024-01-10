from typing import Type

from aenum import Enum, extend_enum

from app.crud.sync_db.tile_cache_assets import get_attributes
from app.models.enumerators.nasa_viirs_fire_alerts.datasets import dataset_name
from app.models.enumerators.nasa_viirs_fire_alerts.supported_attributes import (
    SupportedAttribute,
)
from app.models.enumerators.tile_caches import TileCacheType

default_attributes = [SupportedAttribute.FRP_MW]


class Attributes(str, Enum):
    __doc__ = "NASA VIIRS fire alerts attributes"


def get_attributes_enum(version) -> Type[Attributes]:
    attributes = get_attributes(
        dataset_name, version, TileCacheType.dynamic_vector_tile_cache
    )
    for attribute in attributes:
        extend_enum(Attributes, attribute["field_name"], attribute["field_name"])
    return Attributes
