from enum import Enum


class WmtsRequest(str, Enum):
    get_capabilities = "GetCapabilities"
    get_tiles = "GetTiles"
