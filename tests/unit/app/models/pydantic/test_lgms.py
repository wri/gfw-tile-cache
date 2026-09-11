import pytest

from app.models.enumerators.titiler import LgmsFluxType, LgmsLayer
from app.models.pydantic.lgms import LgmsAsset, UnsupportedLayerFlux, resolve_assets


def test_lgms_rolls_up_every_sector():
    """LULUCF's own mosaic plus agriculture's children, whose net is emissions."""
    assert resolve_assets(LgmsLayer.lgms, LgmsFluxType.net) == [
        LgmsAsset(kind="mosaic", file_name="mosaic.json"),
        LgmsAsset(kind="cog", file_name="cropland_per_ha_v2.tif"),
        LgmsAsset(kind="cog", file_name="livestock_per_ha_v2.tif"),
    ]


def test_a_rollup_missing_any_sector_is_rejected():
    """LULUCF has no gross emissions raster, so an LGMS total would be partial."""
    with pytest.raises(UnsupportedLayerFlux):
        resolve_assets(LgmsLayer.lgms, LgmsFluxType.gross_emissions)


def test_flux_type_the_layer_has_no_raster_for_is_rejected():
    with pytest.raises(UnsupportedLayerFlux):
        resolve_assets(LgmsLayer.cropland, LgmsFluxType.gross_removals)
