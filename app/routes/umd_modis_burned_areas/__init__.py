from typing import List, Optional, Type

from aenum import extend_enum
from fastapi import Query

from ...crud.sync_db.tile_cache_assets import get_latest_version
from ...models.enumerators.nasa_viirs_fire_alerts.attributes import (
    Attributes,
    default_attributes,
    get_attributes_enum,
)
from ...models.enumerators.nasa_viirs_fire_alerts.datasets import dataset_name
from ...models.enumerators.tile_caches import TileCacheType

# In case there is no latest version of the dataset we will need to return something
latest_version: Optional[str] = get_latest_version(
    dataset_name, TileCacheType.dynamic_vector_tile_cache
)
if latest_version:
    included_attribute_type: Type[Attributes] = get_attributes_enum(latest_version)
else:
    included_attribute_type = Attributes
    for field in default_attributes:
        extend_enum(included_attribute_type, field, field)


IncludedAttributes = Optional[List[included_attribute_type]]  # type: ignore


async def include_attributes(
    include_attribute: IncludedAttributes = Query(  # type: ignore
        default_attributes,
        title="Included Attributes",
        description="Select which attributes to include in vector tile. Will always show attribute count. "
        "Documentation list available attributes of latest version. For legacy version "
        "please check data-api for available attribute values.",
    ),
) -> List[str]:
    attributes: List[str] = list()
    if include_attribute:
        for attribute in include_attribute:
            attributes.append(attribute.value)  # type: ignore
    return attributes
