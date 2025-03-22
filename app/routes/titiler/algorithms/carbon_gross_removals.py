from collections import OrderedDict, namedtuple

import numpy as np
from pydantic import ConfigDict
from rio_tiler.models import ImageData
from titiler.core.algorithm import BaseAlgorithm

Colors: namedtuple = namedtuple("Colors", ["red", "green", "blue"])


class CarbonGrossRemovals(BaseAlgorithm):
    """Visualize carbon gross removals."""

    title: str = "Carbon gross removals"
    description: str = "Visualize carbon gross removals"

    model_config = ConfigDict(arbitrary_types_allowed=True)
    conf_colors: OrderedDict[float, tuple] = OrderedDict(
        {
            -1500.0: Colors(21, 29, 68),
            -1419.0: Colors(23, 36, 71),
            -1340.0: Colors(24, 44, 76),
            -1264.0: Colors(26, 51, 80),
            -1189.0: Colors(27, 58, 84),
            -1118.0: Colors(28, 66, 89),
            -1048.0: Colors(28, 72, 93),
            -980.0: Colors(28, 79, 98),
            -915.0: Colors(27, 87, 102),
            -852.0: Colors(26, 93, 106),
            -792.0: Colors(24, 101, 110),
            -733.0: Colors(21, 108, 114),
            -677.0: Colors(19, 115, 117),
            -623.0: Colors(17, 122, 120),
            -571.0: Colors(18, 130, 123),
            -522.0: Colors(23, 136, 125),
            -474.0: Colors(37, 145, 127),
            -429.0: Colors(52, 152, 128),
            -387.0: Colors(65, 157, 130),
            -346.0: Colors(82, 163, 132),
            -308.0: Colors(97, 169, 135),
            -272.0: Colors(111, 173, 139),
            -238.0: Colors(125, 179, 144),
            -206.0: Colors(139, 184, 150),
            -177.0: Colors(151, 189, 156),
            -150.0: Colors(164, 195, 163),
            -125.0: Colors(177, 200, 172),
            -103.0: Colors(188, 206, 180),
            -82.0: Colors(200, 212, 190),
            -64.0: Colors(211, 218, 200),
            -48.0: Colors(221, 224, 209),
            -35.0: Colors(233, 231, 221),
            0.0: Colors(254, 246, 249),
        }
    )

    # metadata
    input_nbands: int = 2
    output_nbands: int = 4
    output_dtype: str = "uint8"

    def __call__(self, img: ImageData) -> ImageData:

        self.removals = img.data[0]
        self.intensity = img.data[1]
        self.no_data = img.array.mask[0]

        rgb = self.create_true_color_rgb()
        alpha = self.create_true_color_alpha()

        data = np.vstack([rgb, alpha[np.newaxis, ...]]).astype(self.output_dtype)
        data = np.ma.MaskedArray(data, mask=False)

        return ImageData(data, assets=img.assets, crs=img.crs, bounds=img.bounds)

    def create_true_color_rgb(self):
        r, g, b = self._rgb_zeros_array()

        for k, colors in self.conf_colors.items():
            r[self.removals >= k] = colors.red
            g[self.removals >= k] = colors.green
            b[self.removals >= k] = colors.blue

        return np.stack([r, g, b], axis=0)

    def create_true_color_alpha(self):
        """Set the transparency (alpha) channel based on intensity input. The
        intensity multiplier is used to control how isolated pixels fade out at
        low zoom levels, matching the rendering behavior in Flagship.

        Returns:
            np.ndarray: Array representing the alpha (transparency) channel, where pixel
            visibility is adjusted by intensity.
        """
        alpha = np.where(~self.no_data, self.intensity, 0)
        return np.minimum(255, alpha)

    def _rgb_zeros_array(self):
        r = np.zeros_like(self.removals, dtype=np.uint8)
        g = np.zeros_like(self.removals, dtype=np.uint8)
        b = np.zeros_like(self.removals, dtype=np.uint8)

        return r, g, b
