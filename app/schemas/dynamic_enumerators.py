from aenum import extend_enum, Enum

from typing import Type

from app.utils.metadata import get_metadata


class Dataset(str, Enum):
    pass


def get_dataset() -> Type[Dataset]:
    dataset = Dataset
    metadata = get_metadata()
    for row in metadata:
        if row.has_feature_info:
            extend_enum(dataset, row.dataset, row.dataset)
    return dataset
