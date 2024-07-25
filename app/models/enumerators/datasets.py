from aenum import Enum, extend_enum

from ...crud.sync_db.tile_cache_assets import get_datasets
from .tile_caches import TileCacheType


class DeforestationAlertDatasets(str, Enum):
    glad = "umd_glad_alerts"
    radd = "wur_radd_alerts"


class RasterTileCacheDatasets(str, Enum):
    __doc__ = "Raster tile cache datasets"


_datasets = get_datasets(TileCacheType.raster_tile_cache)
for _dataset in _datasets:
    extend_enum(RasterTileCacheDatasets, _dataset, _dataset)


class DynamicVectorTileCacheDatasets(str, Enum):
    __doc__ = "Dynamic vector tile cache datasets"


_datasets = get_datasets(TileCacheType.dynamic_vector_tile_cache)
for _dataset in _datasets:
    extend_enum(DynamicVectorTileCacheDatasets, _dataset, _dataset)


class StaticVectorTileCacheDatasets(str, Enum):
    __doc__ = "Static vector tile cache datasets"


_datasets = get_datasets(TileCacheType.static_vector_tile_cache)
for _dataset in _datasets:
    extend_enum(StaticVectorTileCacheDatasets, _dataset, _dataset)


class COGDatasets(str, Enum):
    __doc__ = "Data API datasets with COG assets"


_datasets = get_datasets(TileCacheType.cog)
for _dataset in _datasets:
    extend_enum(COGDatasets, _dataset, _dataset)
