from typing import Type

from aenum import Enum, extend_enum

from app.crud.sync_db.tile_cache_assets import get_versions
from app.models.enumerators.nasa_viirs_fire_alerts.datasets import dataset_name
from app.models.enumerators.tile_caches import TileCacheType


class Versions(str, Enum):
    __doc__ = "NASA VIIRS fire alerts versions"
    latest = "latest"


def get_versions_enum() -> Type[Versions]:
    versions = get_versions(dataset_name, TileCacheType.dynamic_vector_tile_cache)
    for version in versions:
        extend_enum(Versions, version, version)
    return Versions
