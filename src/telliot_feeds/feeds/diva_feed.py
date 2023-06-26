from hexbytes import HexBytes

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.integrations.diva_protocol import DIVA_DIAMOND_ADDRESS
from telliot_feeds.integrations.diva_protocol.sources import DivaSource
from telliot_feeds.integrations.diva_protocol.sources import get_historical_price_source
from telliot_feeds.queries.diva_protocol import DIVAProtocol
from telliot_feeds.sources.manual.diva_manual_source import DivaManualSource


pool_id = None
diva_diamond = None
chain_id = None


diva_manual_feed = DataFeed(
    query=DIVAProtocol(poolId=pool_id, divaDiamond=diva_diamond, chainId=chain_id),
    source=DivaManualSource(),
)

expiry_time = 1686864504
source = DivaSource()
source.reference_asset_source = get_historical_price_source(asset="eth", currency="usd", timestamp=expiry_time)
source.collat_token_source = get_historical_price_source(asset="dusd", currency="usd", timestamp=expiry_time)
diva_example_feed = DataFeed(
    query=DIVAProtocol(
        poolId=HexBytes("0x29a5e6c77d5ba659b3c6688799a02beb98b061c1ba6431c1e660cd8454cdc984"),
        divaDiamond=DIVA_DIAMOND_ADDRESS,
        chainId=80001,
    ),
    source=source,
)
