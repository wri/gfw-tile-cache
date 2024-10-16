from collections import OrderedDict
from .alerts import Alerts

from app.models.enumerators.alerts_confidence import DeforestationAlertConfidence


class DISTAlerts(Alerts):
    title: str = "Land Disturbunce (DIST) Alerts"
    description: str = "Decode and visualize DIST alerts"

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
        }
    )

    record_start_date: str = "2020-12-13"
