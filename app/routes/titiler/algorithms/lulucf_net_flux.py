from collections import OrderedDict, namedtuple

import numpy as np
from pydantic import ConfigDict
from rio_tiler.models import ImageData
from titiler.core.algorithm import BaseAlgorithm

Colors: namedtuple = namedtuple("Colors", ["red", "green", "blue"])


class LulucfNetFlux(BaseAlgorithm):
    """Visualize LULUCF (2016-2024 average) net GHG flux."""

    title: str = "LULUCF net flux"
    description: str = "Visualize LULUCF (2016-2024 average) net GHG flux"

    model_config = ConfigDict(arbitrary_types_allowed=True)
    conf_colors: OrderedDict[float, tuple] = OrderedDict(
        {
            -12.5: Colors(0, 60, 48),      # darkest removal
            -10: Colors(1, 102, 94),
            -7.5: Colors(53, 151, 143),
            -5.0: Colors(128, 205, 193),
            -2.5: Colors(199, 234, 229),   # lightest removal
            -.001: Colors(217, 231, 213),
            .001: Colors(217, 231, 213),
            5.0: Colors(246, 232, 195),    # lightest emission
            10.0: Colors(223, 194, 125),
            15.0: Colors(191, 129, 45),
            20.0: Colors(140, 81, 10),
            25.0: Colors(84, 48, 5),        # darkest emission
        }
    )

    # metadata
    input_nbands: int = 1
    output_nbands: int = 4
    output_dtype: str = "uint8"

    def __call__(self, img: ImageData) -> ImageData:

        self.flux = img.data[0]
        self.no_data = img.array.mask[0]

        rgb = self.create_true_color_rgb()
        alpha = self.create_true_color_alpha()

        data = np.vstack([rgb, alpha[np.newaxis, ...]]).astype(self.output_dtype)
        data = np.ma.MaskedArray(data, mask=False)

        return ImageData(data, assets=img.assets, crs=img.crs, bounds=img.bounds)

    def create_true_color_rgb(self):
        r, g, b = self._rgb_zeros_array()

        for k, colors in self.conf_colors.items():
            r[self.flux >= k] = colors.red
            g[self.flux >= k] = colors.green
            b[self.flux >= k] = colors.blue

        return np.stack([r, g, b], axis=0)

    def create_true_color_alpha(self):
        #alpha = np.where(~self.no_data, self.intensity, 0)
        return np.where(~self.no_data & ((self.flux < -.001) | (self.flux > .001)), 255, 0).astype(self.output_dtype)

    def _rgb_zeros_array(self):
        r = np.zeros_like(self.flux, dtype=np.uint8)
        g = np.zeros_like(self.flux, dtype=np.uint8)
        b = np.zeros_like(self.flux, dtype=np.uint8)

        return r, g, b
