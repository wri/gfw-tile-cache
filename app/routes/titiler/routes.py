"""Titiler Dynamic Raster tiles for Cloud Optimized Geotiffs (COG)"""

from typing import Callable

from titiler.core.algorithm import Algorithms
from titiler.core.algorithm import algorithms as default_algorithms
from titiler.core.factory import AlgorithmFactory, MultiBandTilerFactory, TilerFactory
from titiler.extensions import cogValidateExtension, cogViewerExtension
from titiler.mosaic.factory import MosaicTilerFactory

from ...routes import cog_asset_dependency
from .algorithms import IntegratedAlerts
from .readers import IntegratedAlertsReader

# Allow other computers to attach to debugpy at this IP address and port.
# debugpy.listen(("0.0.0.0", 5678))
# print("Waiting for debugger attach...")
# debugpy.wait_for_client()
# print("Debugger attached.")


algorithms: Algorithms = default_algorithms.register(
    {"integrated_alerts": IntegratedAlerts}
)

# Create a PostProcessParams dependency
PostProcessParams: Callable = algorithms.dependency

custom = MultiBandTilerFactory(
    router_prefix="/cog/custom",
    process_dependency=PostProcessParams,
    reader=IntegratedAlertsReader,
    path_dependency=cog_asset_dependency,
)

cog = TilerFactory(
    router_prefix="/cog/basic",
    extensions=[
        cogValidateExtension(),
        cogViewerExtension(),
    ],
    path_dependency=cog_asset_dependency,
)

algorithms = AlgorithmFactory()

mosaic = MosaicTilerFactory(router_prefix="/cog/mosaic")

# add_exception_handlers(app, DEFAULT_STATUS_CODES)
