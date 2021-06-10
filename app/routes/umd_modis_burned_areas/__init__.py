from typing import Optional

from ...crud.sync_db.tile_cache_assets import get_latest_version
from ...models.enumerators.nasa_viirs_fire_alerts.datasets import dataset_name
from ...models.enumerators.tile_caches import TileCacheType

# In case there is no latest version of the dataset we will need to return something
latest_version: Optional[str] = get_latest_version(
    dataset_name, TileCacheType.dynamic_vector_tile_cache
)
