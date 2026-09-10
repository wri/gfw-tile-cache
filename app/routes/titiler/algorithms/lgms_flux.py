from collections import OrderedDict, namedtuple

import numpy as np
from pydantic import ConfigDict
from rio_tiler.models import ImageData
from titiler.core.algorithm import BaseAlgorithm

Colors: namedtuple = namedtuple("Colors", ["red", "green", "blue"])


class LgmsFlux(BaseAlgorithm):
    """Renders GHG flux as an RGBA tile. Subclasses supply the colour ramp."""

    title: str = "GHG flux"
    description: str = "Visualize GHG flux"

    model_config = ConfigDict(arbitrary_types_allowed=True)
    conf_colors: OrderedDict[float, tuple] = OrderedDict()

    # Flux this close to zero renders as no flux.
    zero_threshold: float = 0

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
        return np.where(
            ~self.no_data & (np.abs(self.flux) > self.zero_threshold), 255, 0
        ).astype(self.output_dtype)

    def _rgb_zeros_array(self):
        r = np.zeros_like(self.flux, dtype=np.uint8)
        g = np.zeros_like(self.flux, dtype=np.uint8)
        b = np.zeros_like(self.flux, dtype=np.uint8)

        return r, g, b


class LulucfNetFlux(LgmsFlux):
    """Visualize LULUCF net GHG flux: negative is removal, positive is emission."""

    title: str = "LULUCF net flux"
    description: str = "Visualize LULUCF net GHG flux"

    zero_threshold: float = 0.001

    conf_colors: OrderedDict[float, tuple] = OrderedDict(
        {
            -12.5: Colors(0, 60, 48),  # darkest removal
            -10: Colors(1, 102, 94),
            -7.5: Colors(53, 151, 143),
            -5.0: Colors(128, 205, 193),
            -2.5: Colors(199, 234, 229),  # lightest removal
            -0.001: Colors(217, 231, 213),
            0.001: Colors(217, 231, 213),
            5.0: Colors(246, 232, 195),  # lightest emission
            10.0: Colors(223, 194, 125),
            15.0: Colors(191, 129, 45),
            20.0: Colors(140, 81, 10),
            25.0: Colors(84, 48, 5),  # darkest emission
        }
    )


class AgricultureEmissions(LgmsFlux):
    """Visualize agriculture GHG emissions.

    Emissions only, so the ramp is sequential rather than diverging, with
    thresholds stepping logarithmically to suit values well below 1 Mg/ha.
    """

    title: str = "Agriculture GHG emissions"
    description: str = "Visualize agriculture GHG emissions"

    conf_colors: OrderedDict[float, tuple] = OrderedDict(
        {
            0: Colors(255, 255, 212),
            0.05: Colors(254, 227, 145),
            0.2: Colors(254, 196, 79),
            0.7: Colors(254, 153, 41),
            2.0: Colors(217, 95, 14),
            6.0: Colors(153, 52, 4),
        }
    )
