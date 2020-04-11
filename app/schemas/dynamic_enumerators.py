from aenum import extend_enum, Enum

from typing import Type

from app.utils.metadata import get_metadata, get_versions


class Dataset(str, Enum):
    pass


class Version(str, Enum):
    latest = "latest"


def get_dataset() -> Type[Dataset]:
    dataset = Dataset
    metadata = get_metadata()
    for row in metadata:
        if row.has_feature_info:
            extend_enum(dataset, row.dataset, row.dataset)
    return dataset


def get_version(dataset) -> Type[Version]:
    version = Version
    versions = get_versions(dataset)
    for row in versions:
        extend_enum(version, row.version, row.version)
    return version


def get_viirs_version() -> Type[Version]:
    return get_version("nasa_viirs_fire_alerts")