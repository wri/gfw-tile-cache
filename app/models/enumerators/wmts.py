# After upgrading to Python 3.11, this can become just
# from enum import StrEnum
try:
    from enum import StrEnum
except ImportError:
    from enum import Enum
    class StrEnum(str, Enum):
        pass


class WmtsRequest(StrEnum):
    get_capabilities = "GetCapabilities"
    get_tiles = "GetTiles"
