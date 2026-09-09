import pytest

from app.models.enumerators.titiler import LgmsFluxType, LgmsLayer
from app.models.pydantic.lgms import LgmsAsset, UnsupportedLayerFlux, resolve_assets


def test_layer_with_its_own_raster_resolves_to_that_raster():
    assert resolve_assets(LgmsLayer.lulucf, LgmsFluxType.net) == [
        LgmsAsset(kind="mosaic", file_name="mosaic.json")
    ]


def test_layer_without_its_own_raster_resolves_to_its_children():
    assert resolve_assets(LgmsLayer.agriculture, LgmsFluxType.gross_emissions) == [
        LgmsAsset(kind="cog", file_name="cropland_emissions_per_ha.tif"),
        LgmsAsset(kind="cog", file_name="livestock_emissions_per_ha.tif"),
    ]


@pytest.mark.parametrize(
    "layer, flux_type",
    [
        (LgmsLayer.lulucf, LgmsFluxType.gross_emissions),
        (LgmsLayer.agriculture, LgmsFluxType.net),
    ],
)
def test_flux_type_the_layer_has_no_raster_for_is_rejected(layer, flux_type):
    with pytest.raises(UnsupportedLayerFlux):
        resolve_assets(layer, flux_type)
