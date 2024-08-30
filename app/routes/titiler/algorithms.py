# from datetime import date
import numpy as np

from dateutil.relativedelta import relativedelta
from datetime import date
from pydantic import Field
from rio_tiler.models import ImageData
from titiler.core.algorithm import BaseAlgorithm

from app.models.enumerators.alerts_confidence import DeforestationAlertConfidence


class IntegratedAlerts(BaseAlgorithm):
    """Decode Integrated Alerts."""

    title: str = "Integrated Deforestation Alerts"
    description: str = "Decode and vizualize alerts"

    START_DATE: str = "2014-12-31"  # start of record

    # Parameters
    default_start_date: str = (date.today() - relativedelta(days=90)).strftime(
        "%Y-%m-%d"
    )
    start_date: str = Field(
        default_start_date,
        description="start date of alert in YYYY-MM-DD format.",
    )

    default_end_date: str = date.today().strftime("%Y-%m-%d")
    end_date: str = Field(
        default_end_date, description="end date of alert in YYYY-MM-DD format."
    )

    alert_confidence: DeforestationAlertConfidence = Field(
        DeforestationAlertConfidence.nominal, description="Alert confidence"
    )

    # metadata
    input_nbands: int = 2
    output_nbands: int = 4
    output_dtype: str = "uint8"

    alert_confidence_map: dict = {
        DeforestationAlertConfidence.nominal: 2,
        DeforestationAlertConfidence.high: 3,
        DeforestationAlertConfidence.highest: 4,
    }

    def __call__(self, img: ImageData) -> ImageData:
        """Encode Integrated alerts to RGBA."""
        mask = img.array.mask[0].astype(int)
        data = img.data[0]
        alert_date = data % 10000  # in days since 2014-12-31
        data_alert_confidence = data // 10000

        intensity = np.where(mask == 0, img.data[1], 0)
        if self.start_date:
            start_mask = alert_date >= (
                np.datetime64(self.start_date).astype(int)
                - np.datetime64(self.START_DATE).astype(int)
            )
            intensity = np.where(start_mask.astype(int) == 1, img.data[1], 0)
        if self.end_date:
            end_mask = alert_date <= (
                np.datetime64(self.end_date).astype(int)
                - np.datetime64(self.START_DATE).astype(int)
            )
            intensity = np.where(start_mask.astype(int) == 1, img.data[1], 0)

        if self.alert_confidence:
            confidence_mask = (
                data_alert_confidence
                >= self.alert_confidence_map[self.alert_confidence]
            )

        r = np.where(data > 0, 228, 0)
        g = np.where(data > 0, 102, 0)
        b = np.where(data > 0, 153, 0)

        intensity = np.where(
            (
                (mask == 0)
                & (start_mask.astype(int) == 1)
                & (end_mask.astype(int) == 1)
                & (confidence_mask.astype(int) == 1)
            ),
            img.data[1],
            0,
        )
        intensity = np.minimum(255, intensity * 50)
        data = np.stack([r, g, b, intensity]).astype(self.output_dtype)
        data = np.ma.MaskedArray(data, mask=False)

        return ImageData(data, assets=img.assets, crs=img.crs, bounds=img.bounds)
