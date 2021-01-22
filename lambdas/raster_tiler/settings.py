import os


class TileNotFoundError(Exception):
    pass


ENV: str = os.environ.get("ENV", "dev")
TILE_SIZE: int = 256
SUFFIX: str = "" if ENV == "production" else f"-{ENV}"
