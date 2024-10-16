from collections import OrderedDict
from datetime import date

import numpy as np
from dateutil.relativedelta import relativedelta
from pydantic import Field
from rio_tiler.models import ImageData
from titiler.core.algorithm import BaseAlgorithm

from app.models.enumerators.alerts_confidence import DeforestationAlertConfidence


class Alerts(BaseAlgorithm):
    """Decode Deforestation Alerts."""

    title: str = "Deforestation Alerts"
    description: str = "Decode and visualize alerts"
    conf_colors: OrderedDict = OrderedDict(
        {
            DeforestationAlertConfidence.low: {
                "confidence": 2,
                "colors": (237, 164, 194),
            },
            DeforestationAlertConfidence.high: {
                "confidence": 3,
                "colors": (220, 102, 153),
            },
            DeforestationAlertConfidence.highest: {
                "confidence": 4,
                "colors": (201, 42, 109),
            },
        }
    )
    record_start_date: str = "2014-12-31"

    # Parameters
    default_start_date: str = (date.today() - relativedelta(days=180)).strftime(
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
        DeforestationAlertConfidence.low, description="Alert confidence"
    )

    # metadata
    input_nbands: int = 2
    output_nbands: int = 4
    output_dtype: str = "uint8"

    def __call__(self, img: ImageData) -> ImageData:
        """Encode Integrated alerts to RGBA."""
        data = img.data[0]
        intensity = img.data[1]
        alert_date = data % 10000  # in days since 2014-12-31
        data_alert_confidence = data // 10000

        r = np.zeros_like(data_alert_confidence, dtype=np.uint8)
        g = np.zeros_like(data_alert_confidence, dtype=np.uint8)
        b = np.zeros_like(data_alert_confidence, dtype=np.uint8)

        for properties in self.conf_colors.values():
            confidence = properties["confidence"]
            colors = properties["colors"]

            r[data_alert_confidence >= confidence] = colors[0]
            g[data_alert_confidence >= confidence] = colors[1]
            b[data_alert_confidence >= confidence] = colors[2]

        start_mask = alert_date >= (
            np.datetime64(self.start_date) - np.datetime64(self.record_start_date)
        )
        end_mask = alert_date <= (
            np.datetime64(self.end_date) - np.datetime64(self.record_start_date)
        )

        confidence_mask = (
            data_alert_confidence
            >= self.conf_colors[self.alert_confidence]["confidence"]
        )
        mask = ~img.array.mask[0] * start_mask * end_mask * confidence_mask
        alpha = np.where(
            mask,
            intensity * 150,
            0,
        )
        alpha = np.minimum(255, alpha)
        data = np.stack([r, g, b, alpha]).astype(self.output_dtype)
        data = np.ma.MaskedArray(data, mask=False)

        return ImageData(data, assets=img.assets, crs=img.crs, bounds=img.bounds)
