from typing import Type

from aenum import Enum, extend_enum

from ...crud.sync_db.vector_tile_assets import get_dynamic_datasets as get_d_datasets
from ...crud.sync_db.vector_tile_assets import get_dynamic_fields
from ...crud.sync_db.vector_tile_assets import get_dynamic_versions as get_d_versions
from ...crud.sync_db.vector_tile_assets import get_static_datasets as get_s_datasets
from ...crud.sync_db.vector_tile_assets import get_static_versions as get_s_versions


class Datasets(str, Enum):
    pass


class Versions(str, Enum):
    latest = "latest"


class Attributes(str, Enum):
    pass


def get_dynamic_datasets() -> Type[Datasets]:
    dynamic_datasets = Datasets

    datasets = get_d_datasets()
    for dataset in datasets:
        extend_enum(dynamic_datasets, dataset, dataset)

    return dynamic_datasets


def get_dynamic_versions(dataset) -> Type[Versions]:
    dynamic_versions = Versions
    versions = get_d_versions(dataset)
    for version in versions:
        extend_enum(dynamic_versions, version, version)
    return dynamic_versions


def get_static_datasets() -> Type[Datasets]:
    static_datasets = Datasets

    datasets = get_s_datasets()
    for dataset in datasets:
        extend_enum(static_datasets, dataset, dataset)

    return static_datasets


def get_static_versions(dataset) -> Type[Versions]:
    static_versions = Versions
    versions = get_s_versions(dataset)
    for version in versions:
        extend_enum(static_versions, version, version)
    return static_versions


def get_attributes(dataset, version):
    attributes = Attributes
    fields = get_dynamic_fields(dataset, version)
    for field in fields:
        if field["is_feature_info"]:
            extend_enum(attributes, field["field_name_"], field["field_name_"])
    return attributes
