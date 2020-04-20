from fastapi.responses import Response


class VectorTileResponse(Response):
    media_type = "application/x-protobuf"
