from typing import Dict, Type

import attr
import morecantile
from rio_tiler.io import MultiBandReader, Reader


@attr.s
class IntegratedAlertsReader(MultiBandReader):

    input: str = attr.ib()
    # bands: Sequence[str] = attr.ib(init=False)
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
        band_url: str = self._get_band_url(
            "gfw_integrated_alerts/v20230922/raster/epsg-4326/cog/default"
        )
        with self.reader(band_url) as cog:
            self.bounds = cog.bounds
            self.crs = cog.crs
            self.minzoom = cog.minzoom
            self.maxzoom = cog.maxzoom

    def _get_band_url(self, band: str) -> str:
        """Validate band's name and return band's url."""
        return f"{self.input}/{band}.tif"
