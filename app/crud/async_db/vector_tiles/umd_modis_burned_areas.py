from typing import List, Optional

from sqlalchemy.sql.elements import ColumnClause, TextClause

from ....application import db
from ....models.enumerators.tile_caches import TileCacheType
from ....models.types import Bounds
from ....responses import VectorTileResponse
from ...async_db import vector_tiles
from ...sync_db.tile_cache_assets import get_latest_version
from . import get_mvt_table

SCHEMA = "umd_modis_burned_areas"

COLUMNS: List[ColumnClause] = [db.column("alert__date")]
latest_version: Optional[str] = get_latest_version(
    SCHEMA, TileCacheType.dynamic_vector_tile_cache
)


async def get_tile(
    version: str, bbox: Bounds, extent: int, filters: List[TextClause]
) -> VectorTileResponse:
    """
    Make SQL query to PostgreSQL and return vector tile in PBF format.
    """
    order_by = [db.column("alert__date")]
    query = get_mvt_table(SCHEMA, version, bbox, extent, COLUMNS, filters, order_by)
    return await vector_tiles.get_tile(query, SCHEMA, extent)
