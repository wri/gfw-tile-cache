
import numpy as np
from pydantic import Field
from rio_tiler.models import ImageData
from titiler.core.algorithm import BaseAlgorithm


class IntegratedAlerts(BaseAlgorithm):
    """Decode Integrated Alerts."""

    title: str = "Integrated Deforestation Alerts"
    description: str = "Decode and vizualize alerts"

    # START_DATE: np.datetime64 = np.datetime64(16435, "D")

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
        r = np.where(data > 0, 228, 0)
        g = np.where(data > 0, 102, 0)
        b = np.where(data > 0, 153, 0)

        intensity = np.where(mask == 0, img.data[1], 0)
        intensity = np.minimum(255, intensity * 50)
        # data = np.ma.MaskedArray(np.ma.stack([r, g, b, intensity]), mask=False).astype(
        #     self.output_dtype
        # )
        data = np.stack([r, g, b, intensity]).astype(self.output_dtype)
        data = np.ma.MaskedArray(data, mask=False)

        # plt.imsave(
        #     "rgba_image.png",
        #     np.transpose(np.stack([r, g, b, intensity]).astype(np.uint8), (1, 2, 0)),
        # )
        # plt.imsave(
        #     "intensity_image.png",
        #     img.array[1],
        # )
        return ImageData(data, assets=img.assets, crs=img.crs, bounds=img.bounds)
