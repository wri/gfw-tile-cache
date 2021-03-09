from copy import deepcopy
from typing import Type

from aenum import Enum, extend_enum

from app.crud.sync_db.tile_cache_assets import get_versions
from app.models.enumerators.tile_caches import TileCacheType


class Versions(str, Enum):
    __doc__ = "Version name of dataset. When using `latest` call will be redirected (307) to version tagged as latest."
    latest = "latest"


def get_versions_enum(dataset: str, tile_cache_type: TileCacheType) -> Type[Versions]:
    _Versions = deepcopy(Versions)
    versions = get_versions(dataset, tile_cache_type)
    for version in versions:
        extend_enum(_Versions, version, version)
    return _Versions
