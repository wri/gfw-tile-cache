from typing import Dict, Type

import attr
import morecantile
from rio_tiler.io import MultiBandReader, Reader


@attr.s
class AlertsReader(MultiBandReader):

    input: str = attr.ib()
    default_band: str = attr.ib(default="default")
    tms: morecantile.TileMatrixSet = attr.ib(
        default=morecantile.tms.get("WebMercatorQuad")
    )
    reader_options: Dict = attr.ib(factory=dict)

    reader: Type[Reader] = attr.ib(default=Reader)

    minzoom: int = attr.ib()
    maxzoom: int = attr.ib()

    @minzoom.default
    def _minzoom(self):
        return self.tms.minzoom

    @maxzoom.default
    def _maxzoom(self):
        return self.tms.maxzoom

    def __attrs_post_init__(self):
        """Get grid bounds."""
        band_url: str = self._get_band_url(self.default_band)
        with self.reader(band_url) as cog:
            self.bounds = cog.bounds
            self.crs = cog.crs
            self.minzoom = cog.minzoom
            self.maxzoom = cog.maxzoom

    def _get_band_url(self, band: str) -> str:
        """Validate band's name and return band's url."""
        if band.endswith(".vrt"):
            return f"{self.input}/{band}"
        else:
            return f"{self.input}/{band}.tif"
