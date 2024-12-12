"""Titiler Dynamic Raster tiles for Cloud Optimized Geotiffs (COG)"""

from titiler.core.factory import AlgorithmFactory, TilerFactory
from titiler.extensions import cogValidateExtension, cogViewerExtension
from titiler.mosaic.factory import MosaicTilerFactory

from ...routes import cog_asset_dependency

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
