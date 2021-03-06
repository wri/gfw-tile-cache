from typing import Optional, Tuple
from xml.dom.minidom import parseString
from xml.etree.ElementTree import Element, SubElement, tostring

from aenum import Enum, extend_enum
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from fastapi.responses import RedirectResponse

from ..models.enumerators.wmts import WmtsRequest
from ..responses import XMLResponse
from ..settings.globals import GLOBALS
from . import raster_tile_cache_version_dependency

router = APIRouter()


def _to_key(value: str):
    return value.lower().replace(":", "_")


class Format(str, Enum):
    png = "image/png"


class TileMatrixSet(str, Enum):
    epsg_3857 = "EPSG:3857"


class TileMatrix(str, Enum):
    pass


base_scale = {TileMatrixSet.epsg_3857: 5.590822639508929e8}
for _set in [set.value for set in TileMatrixSet]:  # type: ignore
    for zoom in range(0, 23):
        extend_enum(TileMatrix, _to_key(_set), f"{_set}:{zoom}")


@router.get(
    "/{dataset}/{version}/{implementation}/wmts",
    response_class=Response,
    tags=["Raster Tiles"],
    # response_description="PNG Raster Tile",
)
async def wmts(
    *,
    dv: Tuple[str, str] = Depends(raster_tile_cache_version_dependency),
    implementation: str = Path(..., description="Tile Cache implementation"),
    SERVICE: str = Query("WMTS"),
    VERSION: str = Query("1.0.0"),
    REQUEST: WmtsRequest = Query(...),
    tileMatrixSet: Optional[TileMatrixSet] = Query(
        None, description="Projection of tiles"
    ),
    tileMatrix: Optional[TileMatrixSet] = Query(None, description="z index"),
    tileRow: Optional[int] = Query(None, description="y index", ge=0),
    tileCol: Optional[int] = Query(None, description="x index", ge=0),
    format: Optional[Format] = Query(None, description="Tile format"),
) -> Response:
    """
    WMTS Service
    """
    dataset, version = dv

    if REQUEST == WmtsRequest.get_capabilities:
        capabilities = get_capabilities(dataset, version, implementation)
        return XMLResponse(
            # With Python 3.9 we can use ET.indent() instead
            content=parseString(tostring(capabilities)).toprettyxml(),
        )
    elif REQUEST == WmtsRequest.get_tiles:
        if tileMatrixSet is None or tileCol is None or tileCol is None:
            raise HTTPException(
                status_code=400,
                detail="Must provide parameters tileMatrixSet, tileCol and tileRow with GetTile request.",
            )

        z = int(tileMatrixSet.split(":")[2])
        x = tileCol
        y = tileRow

        return RedirectResponse(
            f"{GLOBALS.tile_cache_url}/{dataset}/{version}/{implementation}/{z}/{x}/{y}.png"
        )


@router.get(
    "/{dataset}/{version}/{implementation}/wmts/1.0.0/WMTSCapabilities.xml",
    response_class=Response,
    tags=["Raster Tiles"],
    # response_description="PNG Raster Tile",
)
async def wmts_capabilities(
    *,
    dv: Tuple[str, str] = Depends(raster_tile_cache_version_dependency),
    implementation: str = Path(..., description="Tile Cache implementation"),
) -> XMLResponse:
    """
    WMTS Service
    """
    dataset, version = dv

    capabilities = get_capabilities(dataset, version, implementation)

    return XMLResponse(
        # With Python 3.9 we can use ET.indent() instead
        content=parseString(tostring(capabilities)).toprettyxml(),
    )


def get_capabilities(
    dataset,
    version,
    implementation,
    formats=[Format.png],
    tile_matrix_sets=[TileMatrixSet.epsg_3857],
    max_zoom=22,
):
    url = f"{GLOBALS.tile_cache_url}/{dataset}/{version}/{implementation}/wmts"
    capabilities = Element("Capabilities")
    capabilities.set("version", "1.0.0")
    capabilities.set("xmlns", "http://www.opengis.net/wmts/1.0")
    capabilities.set("xmlns:ows", "http://www.opengis.net/ows/1.1")
    capabilities.set("xmlns:xlink", "http://www.w3.org/1999/xlink")
    service_identification = SubElement(capabilities, "ows:ServiceIdentification")
    title = SubElement(service_identification, "ows:Title")
    title.text = "GFW Web Map Tile Service"
    service_type = SubElement(service_identification, "ows:ServiceType")
    service_type.text = "OGC WMTS"
    service_type_version = SubElement(service_identification, "ows:ServiceTypeVersion")
    service_type_version.text = "1.0.0"
    service_provider = SubElement(capabilities, "ows:ServiceProvider")
    name = SubElement(service_provider, "ows:ProviderName")
    name.text = "Global Forest Watch"
    website = SubElement(service_provider, "ows:ProviderSite")
    website.set("xlink:href", "https://www.globalforestwatch.org")
    contact = SubElement(service_provider, "ows:ServiceContact")
    contact_name = SubElement(contact, "ows:IndividualName")
    contact_name.text = "GFW Engineering"
    operation_metadata = SubElement(capabilities, "ows:OperationsMetadata")
    get_operation(operation_metadata, "GetCapabilities", url)
    get_operation(operation_metadata, "GetTile", url)
    get_operation(operation_metadata, "GetFeatureInfo", url)
    content = SubElement(capabilities, "Contents")
    get_layer(content, dataset, formats, tile_matrix_sets)
    for tile_matrix_set in tile_matrix_sets:
        get_tile_matrix_set(content, tile_matrix_set, max_zoom)
    return capabilities


def get_operation(parent, operation_name, url):
    operation = SubElement(parent, "ows:Operation")
    operation.set("name", operation_name)
    dcp = SubElement(operation, "ows:DCP")
    http = SubElement(dcp, "ows:HTTP")
    get = SubElement(http, "ows:GET")
    get.set("xlink:href", url)
    constraint = SubElement(get, "ows:Constrain")
    constraint.set("name", "GetEncoding")
    allowed_values = SubElement(constraint, "ows:AllowedValues")
    value = SubElement(allowed_values, "ows:Value")
    value.text = "KVP"


def get_layer(parent, layer_name, formats, tile_matix_sets):
    layer = SubElement(parent, "Layer")
    title = SubElement(layer, "ows:Title")
    title.text = layer_name
    bbox = SubElement(layer, "ows:WGS84BoundingBox")
    lower_corner = SubElement(bbox, "ows:LowerCorner")
    lower_corner.text = "-180.0 -90.0"
    upper_corner = SubElement(bbox, "ows:UpperCorner")
    upper_corner.text = "180.0 90.0"
    style = SubElement(layer, "Style")
    style.set("isDefault", "true")
    identifier = SubElement(style, "ows:Identifier")
    identifier.text = "_null"
    for format_name in formats:
        get_format(layer, format_name)
    for tile_matix_set in tile_matix_sets:
        get_tile_matrix_set_link(layer, tile_matix_set)


def get_format(parent, format_name: str):
    layer_format = SubElement(parent, "Format")
    layer_format.text = format_name


def get_tile_matrix_set_link(parent, tile_matix_set_name):
    set_link = SubElement(parent, "TileMatrixSetLink")
    tile_matrix_set = SubElement(set_link, "TileMatrixSet")
    tile_matrix_set.text = tile_matix_set_name


def get_tile_matrix_set(parent, tile_matix_set_name, max_zoom):
    org, code = tile_matix_set_name.split(":")
    tile_matrix_set = SubElement(parent, "TileMatrixSet")
    identifier = SubElement(tile_matrix_set, "ows:Identifier")
    identifier.text = tile_matix_set_name
    supported_crs = SubElement(tile_matrix_set, "ows:SupportedCRS")
    supported_crs.text = f"urn:ogc:def:crs:{org}::{code}"
    for zoom in range(0, max_zoom + 1):
        get_tile_matrix(tile_matrix_set, tile_matix_set_name, zoom)


def get_tile_matrix(parent, tile_matrix_set: str, zoom: int):
    tile_matrix = SubElement(parent, "TileMatrix")
    identifier = SubElement(tile_matrix, "ows:Identifier")
    identifier.text = f"{tile_matrix_set}:{zoom}"
    scale_denominator = SubElement(tile_matrix, "ScaleDenominator")
    scale_denominator.text = str(base_scale[tile_matrix_set] / (2 ** zoom))
    top_left = SubElement(tile_matrix, "TopLeftCorner")
    top_left.text = "-2.003750834E7 2.0037508E7"
    tile_width = SubElement(tile_matrix, "TileWidth")
    tile_width.text = "256"
    tile_height = SubElement(tile_matrix, "TileHeight")
    tile_height.text = "256"
    matrix_width = SubElement(tile_matrix, "MatrixWidth")
    matrix_width.text = str(2 ** zoom)
    matrix_height = SubElement(tile_matrix, "MatrixHeight")
    matrix_height.text = str(2 ** zoom)
