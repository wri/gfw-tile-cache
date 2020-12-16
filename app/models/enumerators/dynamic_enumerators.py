from typing import Callable, Dict, Type

from aenum import Enum, extend_enum

from ...crud.sync_db.tile_cache_assets import (
    get_dynamic_vector_tile_cache_attributes,
    get_dynamic_vector_tile_cache_dataset,
    get_dynamic_vector_tile_cache_version,
    get_raster_tile_cache_dataset,
    get_raster_tile_cache_version,
    get_static_vector_tile_cache_attributes,
    get_static_vector_tile_cache_dataset,
    get_static_vector_tile_cache_version,
)
from .tile_caches import TileCacheType


class Datasets(str, Enum):
    __doc__ = "Dataset name"
    pass


class Versions(str, Enum):
    __doc__ = "Version name of dataset. When using `latest` call will be redirected (307) to version tagged as latest."
    latest = "latest"


class Attributes(str, Enum):
    __doc__ = "Attribute name"
    pass


def get_datasets(tile_cache_type: str) -> Type[Datasets]:
    dataset_lookup: Dict[str, Callable] = {
        TileCacheType.raster_tile_cache: get_raster_tile_cache_dataset,
        TileCacheType.dynamic_vector_tile_cache: get_dynamic_vector_tile_cache_dataset,
        TileCacheType.static_vector_tile_cache: get_static_vector_tile_cache_dataset,
    }

    dataset_enum = Datasets
    datasets = dataset_lookup[tile_cache_type]()
    for dataset in datasets:
        extend_enum(dataset_enum, dataset, dataset)

    return dataset_enum


def get_versions(dataset, tile_cache_type) -> Type[Versions]:
    version_lookup: Dict[str, Callable] = {
        TileCacheType.raster_tile_cache: get_raster_tile_cache_version,
        TileCacheType.dynamic_vector_tile_cache: get_dynamic_vector_tile_cache_version,
        TileCacheType.static_vector_tile_cache: get_static_vector_tile_cache_version,
    }

    version_enum = Versions
    versions = version_lookup[tile_cache_type](dataset)
    for version in versions:
        extend_enum(version_enum, version, version)
    return version_enum


def get_attributes(dataset, version, tile_cache_type) -> Type[Versions]:
    attribute_lookup: Dict[str, Callable] = {
        # TileCacheType.raster_tile_cache: get_raster_tile_cache_attributes,
        TileCacheType.dynamic_vector_tile_cache: get_dynamic_vector_tile_cache_attributes,
        TileCacheType.static_vector_tile_cache: get_static_vector_tile_cache_attributes,
    }

    attribute_enum = Attributes
    attributes = attribute_lookup[tile_cache_type](dataset, version)
    for attribute in attributes:
        extend_enum(attribute_enum, attribute["field_name"], attribute["field_name"])
    return attribute_enum
