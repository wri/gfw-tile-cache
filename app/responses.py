from xml.dom.minidom import parseString
from xml.etree.ElementTree import Element, tostring

from fastapi.responses import Response


class VectorTileResponse(Response):
    media_type = "application/x-protobuf"


class RasterTileResponse(Response):
    media_type = "image/png"


class XMLResponse(Response):
    media_type = "application/xml"

    def render(self, content: Element) -> bytes:
        if not isinstance(content, Element):
            raise ValueError("XMLResponse requires XML Element as input")

        # With Python 3.9 we can use ET.indent() instead
        pretty_content: str = parseString(tostring(content)).toprettyxml()

        return pretty_content.encode(self.charset)
