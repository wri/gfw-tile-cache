# After upgrading to Python 3.11, this can become just
# from enum import StrEnum
try:
    from enum import StrEnum
except ImportError:
    from enum import Enum
    class StrEnum(str, Enum):
        pass


class TileCacheType(StrEnum):
    dynamic_vector_tile_cache = "Dynamic vector tile cache"
    static_vector_tile_cache = "Static vector tile cache"
    raster_tile_cache = "Raster tile cache"
    cog = "COG"
