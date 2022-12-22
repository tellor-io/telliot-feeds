from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.diva_protocol import DIVAProtocol
from telliot_feeds.sources.manual.diva_manual_source import DivaManualSource


pool_id = None
diva_diamond = None
chain_id = None


diva_manual_feed = DataFeed(
    query=DIVAProtocol(poolId=pool_id, divaDiamond=diva_diamond, chainId=chain_id),
    source=DivaManualSource(),
)
