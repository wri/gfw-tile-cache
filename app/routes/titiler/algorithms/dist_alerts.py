from collections import OrderedDict

from app.models.enumerators.alerts_confidence import AlertConfidence

from .alerts import AlertConfig, Alerts, Colors


class DISTAlerts(Alerts):
    title: str = "Land Disturbunce (DIST) Alerts"
    description: str = "Decode and visualize DIST alerts"

    conf_colors: OrderedDict = OrderedDict(
        {
            AlertConfidence.low: AlertConfig(
                confidence=2, colors=Colors(237, 164, 194)
            ),
            AlertConfidence.high: AlertConfig(
                confidence=3, colors=Colors(220, 102, 153)
            ),
        }
    )

    record_start_date: str = "2020-12-13"
