from fastapi.responses import Response


class VectorTileResponse(Response):
    media_type = "application/x-protobuf"


class RasterTileResponse(Response):
    media_type = "image/png"


class XMLResponse(Response):
    media_type = "application/xml"
