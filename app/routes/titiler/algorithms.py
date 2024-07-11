# from datetime import date
import numpy as np
from pydantic import Field
from rio_tiler.models import ImageData
from titiler.core.algorithm import BaseAlgorithm


class IntegratedAlerts(BaseAlgorithm):
    """Decode Integrated Alerts."""

    title: str = "Integrated Deforestation Alerts"
    description: str = "Decode and vizualize alerts"

    # START_DATE: np.datetime64 = np.datetime64("2014-12-31").astype(int)

    # Parameters
    start_date: int = Field(None, description="start date of alert")
    end_date: int = Field(None, description="end date of alert")

    # metadata
    input_nbands: int = 2
    output_nbands: int = 4
    output_dtype: str = "uint8"

    def __call__(self, img: ImageData) -> ImageData:
        """Encode Integrated alerts to RGBA."""
        mask = img.array.mask[0].astype(int)
        data = img.data[0]

        # Will add this in next iteration
        # if self.start_date:
        #     start_mask = data % 10000 >= (
        #         np.datetime64(self.start_date).astype(int) - self.START_DATE
        #     )
        #     mask = mask * start_mask
        # if self.end_date:
        #     end_mask = data % 10000 <= (
        #         np.datetime64(self.end_date).astype(int) - self.START_DATE
        #     )
        #     mask = mask * end_mask

        r = np.where(data > 0, 228, 0)
        g = np.where(data > 0, 102, 0)
        b = np.where(data > 0, 153, 0)

        intensity = np.where(mask == 0, img.data[1], 0)
        intensity = np.minimum(255, intensity * 50)
        data = np.stack([r, g, b, intensity]).astype(self.output_dtype)
        data = np.ma.MaskedArray(data, mask=False)

        return ImageData(data, assets=img.assets, crs=img.crs, bounds=img.bounds)
