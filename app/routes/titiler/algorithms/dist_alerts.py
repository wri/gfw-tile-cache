from collections import OrderedDict
from typing import Optional

from pydantic import ConfigDict
from rio_tiler.models import ImageData

from app.models.enumerators.titiler import AlertConfidence

from .alerts import AlertConfig, Alerts, Colors


class DISTAlerts(Alerts):
    title: str = "Land Disturbance (DIST) Alerts"
    description: str = "Decode and visualize DIST alerts"

    model_config = ConfigDict(arbitrary_types_allowed=True)
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

    record_start_date: str = "2020-12-31"

    tree_cover_density_mask: Optional[int] = None
    tree_cover_density_data: Optional[ImageData] = None

    tree_cover_height_mask: Optional[int] = None
    tree_cover_height_data: Optional[ImageData] = None

    # the highest loss year that is used to exclude alerts for
    # the purpose of showing only alerts in forests
    tree_cover_loss_mask: Optional[int] = None
    tree_cover_loss_data: Optional[ImageData] = None
