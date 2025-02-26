from collections import OrderedDict, namedtuple
from typing import Optional

import numpy as np
from fastapi.logger import logger
from rio_tiler.models import ImageData
from titiler.core.algorithm import BaseAlgorithm

from app.models.enumerators.titiler import RenderType

class TreeCoverLoss(BaseAlgorithm):

    title: str = "Tree Cover Loss"
    description: str = "Decode and visualize tree cover loss"

    start_year = 2001
    end_year = 2023
    render_type: RenderType = RenderType.encoded

    # metadata
    input_nbands: int = 2
    output_nbands: int = 4
    output_dtype: str = "uint8"

    def __call__(self, img: ImageData) -> ImageData:
        
        self.lossyear = img.data[0]
        self.intensity = img.data[1]
        self.no_data = img.array.mask[0]

        self.mask = self.create_mask(lossyear_data)

        if self.render_type == RenderType.encoded:
            return self.create_encoded_rgb(lossyear_data)
            alpha = self.create_encoded_alpha(intensity_data)
        else:   # true color
            return self.create_true_color_rgb(lossyear_data)
            alpha = self.create_true_color_alpha(intensity_data)

    def create_mask(self):
        mask = ~self.no_data

        if self.start_year:
            start_mask = self.lossyear >= self.start_year
            mask &= start_mask

        if self.end_year:
            end_mask = self.lossyear <= self.end_year
            mask &= end_mask

        return mask
    
    def create_encoded_rgb(self):
        r, g, b = self._rgb_zeros_array()

    def create_true_color_rgb(self):
        r, g, b = self._rgb_zeros_array()

        r = self.lossyear * 228;
        g = self.lossyear % 255;
        b = self.intensity

        return np.stack([r, g, b], axis=0)
