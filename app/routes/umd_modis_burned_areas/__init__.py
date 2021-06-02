from typing import List, Optional, Type

import pendulum
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


def default_start():
    now = pendulum.now()
    return now.subtract(months=1).to_date_string()


def default_end():
    now = pendulum.now()
    return now.to_date_string()
