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
            -45.000: Colors(21, 29, 68),
            -42.977: Colors(23, 36, 71),
            -40.985: Colors(24, 44, 76),
            -39.050: Colors(26, 51, 80),
            -37.120: Colors(27, 58, 84),
            -35.274: Colors(28, 66, 89),
            -33.434: Colors(28, 72, 93),
            -31.626: Colors(28, 79, 98),
            -29.878: Colors(27, 87, 102),
            -28.163: Colors(26, 93, 106),
            -26.510: Colors(24, 101, 110),
            -24.863: Colors(21, 108, 114),
            -23.278: Colors(19, 115, 117),
            -21.729: Colors(17, 122, 120),
            -20.215: Colors(18, 130, 123),
            -18.767: Colors(23, 136, 125),
            -17.326: Colors(37, 145, 127),
            -15.951: Colors(52, 152, 128),
            -14.646: Colors(65, 157, 130),
            -13.348: Colors(82, 163, 132),
            -12.122: Colors(97, 169, 135),
            -10.935: Colors(111, 173, 139),
            -9.790: Colors(125, 179, 144),
            -8.686: Colors(139, 184, 150),
            -7.660: Colors(151, 189, 156),
            -6.679: Colors(164, 195, 163),
            -5.742: Colors(177, 200, 172),
            -4.891: Colors(188, 206, 180),
            -4.049: Colors(200, 212, 190),
            -3.298: Colors(211, 218, 200),
            -2.598: Colors(221, 224, 209),
            -2.000: Colors(233, 231, 221),
            2.000: Colors(236, 228, 236),
            2.598: Colors(227, 220, 231),
            3.298: Colors(220, 212, 229),
            4.049: Colors(211, 204, 227),
            4.891: Colors(204, 195, 227),
            5.742: Colors(197, 187, 228),
            6.679: Colors(190, 178, 230),
            7.660: Colors(185, 168, 232),
            8.686: Colors(180, 160, 232),
            9.790: Colors(176, 151, 231),
            10.935: Colors(172, 141, 228),
            12.122: Colors(168, 133, 224),
            13.348: Colors(165, 125, 217),
            14.646: Colors(161, 116, 210),
            15.951: Colors(158, 109, 202),
            17.326: Colors(154, 101, 192),
            18.767: Colors(148, 92, 180),
            20.215: Colors(144, 86, 171),
            21.729: Colors(140, 79, 160),
            23.278: Colors(134, 72, 150),
            24.863: Colors(130, 67, 140),
            26.510: Colors(124, 61, 130),
            28.163: Colors(118, 55, 119),
            29.878: Colors(112, 50, 110),
            31.626: Colors(106, 45, 100),
            33.434: Colors(99, 39, 90),
            35.274: Colors(92, 35, 82),
            37.120: Colors(85, 30, 72),
            39.050: Colors(78, 25, 64),
            40.985: Colors(71, 20, 56),
            42.977: Colors(63, 14, 49),
            45.000: Colors(57, 8, 42),
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
        """Opaque where data exists, transparent where nodata."""
        return np.where(~self.no_data, 255, 0).astype(self.output_dtype)

    def _rgb_zeros_array(self):
        r = np.zeros_like(self.flux, dtype=np.uint8)
        g = np.zeros_like(self.flux, dtype=np.uint8)
        b = np.zeros_like(self.flux, dtype=np.uint8)

        return r, g, b
