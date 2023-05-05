import pytest

from app.settings.globals import GLOBALS
from tests.fixtures.payloads import umd_glad_alerts_payload, umd_tree_cover_loss_payload

xml = """<?xml version="1.0" ?>
<Capabilities xmlns="http://www.opengis.net/wmts/1.0" xmlns:gml="http://www.opengis.net/gml" xmlns:ows="http://www.opengis.net/ows/1.1" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/wmts/1.0 http://schemas.opengis.net/wmts/1.0/wmtsGetCapabilities_response.xsd" version="1.0.0">
<ServiceMetadataURL xlink:href="https://{domain}/{dataset}/{version}/{implementation}/wmts/1.0.0/WMTSCapabilities.xml"/>
<ows:ServiceIdentification>
<ows:Title>GFW Web Map Tile Service</ows:Title>
<ows:ServiceType>OGC WMTS</ows:ServiceType>
<ows:ServiceTypeVersion>1.0.0</ows:ServiceTypeVersion>
<ows:Profile>http://www.opengis.net/spec/wmts-simple/1.0/conf/simple-profile</ows:Profile>
<ows:Fees>none</ows:Fees>
<ows:AccessConstraints>none</ows:AccessConstraints>
</ows:ServiceIdentification>
<ows:ServiceProvider>
<ows:ProviderName>Global Forest Watch</ows:ProviderName>
<ows:ProviderSite xlink:href="https://www.globalforestwatch.org"/>
<ows:ServiceContact>
<ows:IndividualName>GFW Engineering</ows:IndividualName>
</ows:ServiceContact>
</ows:ServiceProvider>
<Contents>
<Layer>
<ows:Title>{dataset}</ows:Title>
<ows:WGS84BoundingBox>
<ows:LowerCorner>-180.0 -90.0</ows:LowerCorner>
<ows:UpperCorner>180.0 90.0</ows:UpperCorner>
</ows:WGS84BoundingBox>
<Style isDefault="true">
<ows:Identifier>default</ows:Identifier>
</Style>
<ResourceURL format="Format.png" resourceType="simpleProfileTile" template="https://{domain}/{dataset}/{version}/{implementation}/{{TileMatrix}}/{{TileCol}}/{{TileRow}}.png"/>
<ResourceURL format="Format.png" resourceType="tile" template="https://{domain}/{dataset}/{version}/{implementation}/{{TileMatrix}}/{{TileCol}}/{{TileRow}}.png"/>
<Format>image/png</Format>
<TileMatrixSetLink>
<TileMatrixSet>EPSG:3857</TileMatrixSet>
</TileMatrixSetLink>
</Layer>
<TileMatrixSet>
<ows:Identifier>EPSG:3857</ows:Identifier>
<ows:SupportedCRS>urn:ogc:def:crs:EPSG::3857</ows:SupportedCRS>
<TileMatrix>
<ows:Identifier>0</ows:Identifier>
<ScaleDenominator>559082263.9508929</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>1</MatrixWidth>
<MatrixHeight>1</MatrixHeight>
</TileMatrix>
<TileMatrix>
<ows:Identifier>1</ows:Identifier>
<ScaleDenominator>279541131.97544646</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>2</MatrixWidth>
<MatrixHeight>2</MatrixHeight>
</TileMatrix>
<TileMatrix>
<ows:Identifier>2</ows:Identifier>
<ScaleDenominator>139770565.98772323</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>4</MatrixWidth>
<MatrixHeight>4</MatrixHeight>
</TileMatrix>
<TileMatrix>
<ows:Identifier>3</ows:Identifier>
<ScaleDenominator>69885282.99386162</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>8</MatrixWidth>
<MatrixHeight>8</MatrixHeight>
</TileMatrix>
<TileMatrix>
<ows:Identifier>4</ows:Identifier>
<ScaleDenominator>34942641.49693081</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>16</MatrixWidth>
<MatrixHeight>16</MatrixHeight>
</TileMatrix>
<TileMatrix>
<ows:Identifier>5</ows:Identifier>
<ScaleDenominator>17471320.748465404</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>32</MatrixWidth>
<MatrixHeight>32</MatrixHeight>
</TileMatrix>
<TileMatrix>
<ows:Identifier>6</ows:Identifier>
<ScaleDenominator>8735660.374232702</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>64</MatrixWidth>
<MatrixHeight>64</MatrixHeight>
</TileMatrix>
<TileMatrix>
<ows:Identifier>7</ows:Identifier>
<ScaleDenominator>4367830.187116351</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>128</MatrixWidth>
<MatrixHeight>128</MatrixHeight>
</TileMatrix>
<TileMatrix>
<ows:Identifier>8</ows:Identifier>
<ScaleDenominator>2183915.0935581755</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>256</MatrixWidth>
<MatrixHeight>256</MatrixHeight>
</TileMatrix>
<TileMatrix>
<ows:Identifier>9</ows:Identifier>
<ScaleDenominator>1091957.5467790877</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>512</MatrixWidth>
<MatrixHeight>512</MatrixHeight>
</TileMatrix>
<TileMatrix>
<ows:Identifier>10</ows:Identifier>
<ScaleDenominator>545978.7733895439</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>1024</MatrixWidth>
<MatrixHeight>1024</MatrixHeight>
</TileMatrix>
<TileMatrix>
<ows:Identifier>11</ows:Identifier>
<ScaleDenominator>272989.38669477194</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>2048</MatrixWidth>
<MatrixHeight>2048</MatrixHeight>
</TileMatrix>
<TileMatrix>
<ows:Identifier>12</ows:Identifier>
<ScaleDenominator>136494.69334738597</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>4096</MatrixWidth>
<MatrixHeight>4096</MatrixHeight>
</TileMatrix>
<TileMatrix>
<ows:Identifier>13</ows:Identifier>
<ScaleDenominator>68247.34667369298</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>8192</MatrixWidth>
<MatrixHeight>8192</MatrixHeight>
</TileMatrix>
<TileMatrix>
<ows:Identifier>14</ows:Identifier>
<ScaleDenominator>34123.67333684649</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>16384</MatrixWidth>
<MatrixHeight>16384</MatrixHeight>
</TileMatrix>
<TileMatrix>
<ows:Identifier>15</ows:Identifier>
<ScaleDenominator>17061.836668423246</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>32768</MatrixWidth>
<MatrixHeight>32768</MatrixHeight>
</TileMatrix>
<TileMatrix>
<ows:Identifier>16</ows:Identifier>
<ScaleDenominator>8530.918334211623</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>65536</MatrixWidth>
<MatrixHeight>65536</MatrixHeight>
</TileMatrix>
<TileMatrix>
<ows:Identifier>17</ows:Identifier>
<ScaleDenominator>4265.4591671058115</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>131072</MatrixWidth>
<MatrixHeight>131072</MatrixHeight>
</TileMatrix>
<TileMatrix>
<ows:Identifier>18</ows:Identifier>
<ScaleDenominator>2132.7295835529058</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>262144</MatrixWidth>
<MatrixHeight>262144</MatrixHeight>
</TileMatrix>
<TileMatrix>
<ows:Identifier>19</ows:Identifier>
<ScaleDenominator>1066.3647917764529</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>524288</MatrixWidth>
<MatrixHeight>524288</MatrixHeight>
</TileMatrix>
<TileMatrix>
<ows:Identifier>20</ows:Identifier>
<ScaleDenominator>533.1823958882264</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>1048576</MatrixWidth>
<MatrixHeight>1048576</MatrixHeight>
</TileMatrix>
<TileMatrix>
<ows:Identifier>21</ows:Identifier>
<ScaleDenominator>266.5911979441132</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>2097152</MatrixWidth>
<MatrixHeight>2097152</MatrixHeight>
</TileMatrix>
<TileMatrix>
<ows:Identifier>22</ows:Identifier>
<ScaleDenominator>133.2955989720566</ScaleDenominator>
<TopLeftCorner>-2.003750834E7 2.0037508E7</TopLeftCorner>
<TileWidth>256</TileWidth>
<TileHeight>256</TileHeight>
<MatrixWidth>4194304</MatrixWidth>
<MatrixHeight>4194304</MatrixHeight>
</TileMatrix>
</TileMatrixSet>
</Contents>
</Capabilities>
"""


def _lint_doc(doc):
    " ".join([item for item in doc.split() if item != ""])

@pytest.mark.skip("Skipped to deploy metadata fix")
@pytest.mark.parametrize(
    "params, payload",
    [umd_tree_cover_loss_payload(), umd_glad_alerts_payload()],
)
def test_wmts(client, params, payload):
    dataset = payload["dataset"]
    version = payload["version"]
    implementation = payload["implementation"]

    response = client.get(
        f"/{dataset}/{version}/{implementation}/wmts/1.0.0/WMTSCapabilities.xml"
    )

    assert response.status_code == 200

    linted_response = _lint_doc(response.text)
    linted_expected_response = _lint_doc(
        xml.format(
            domain=GLOBALS.tile_cache_url,
            dataset=dataset,
            version=version,
            implementation=implementation,
        )
    )
    assert linted_response == linted_expected_response


def test_wmts_bad_request(client):
    """
    This should not work for vector tile caches.
    """
    dataset = "nasa_viirs_fire_alerts"
    version = "v202003"
    implementation = "dynamic"

    response = client.get(
        f"/{dataset}/{version}/{implementation}/wmts/1.0.0/WMTSCapabilities.xml"
    )

    assert response.status_code == 422
