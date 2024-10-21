from collections import OrderedDict, namedtuple

from app.models.enumerators.titiler import DeforestationAlertConfidence

from .alerts import Alerts


class DISTAlerts(Alerts):
    title: str = "Land Disturbunce (DIST) Alerts"
    description: str = "Decode and visualize DIST alerts"

    Colors: namedtuple = namedtuple("Colors", ["red", "green", "blue"])
    DeforestationAlert: namedtuple = namedtuple(
        "DeforestationAlert", ["confidence", "colors"]
    )

    conf_colors: OrderedDict = OrderedDict(
        {
            DeforestationAlertConfidence.low: DeforestationAlert(
                confidence=2, colors=Colors(237, 164, 194)
            ),
            DeforestationAlertConfidence.high: DeforestationAlert(
                confidence=3, colors=Colors(220, 102, 153)
            ),
        }
    )

    record_start_date: str = "2020-12-13"
