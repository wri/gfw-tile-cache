from enum import Enum


class TileCacheType(str, Enum):
    dynamic_vector_tile_cache = "Dynamic vector tile cache"
    static_vector_tile_cache = "Static vector tile cache"
    raster_tile_cache = "Raster tile cache"
    cog = "COG"
