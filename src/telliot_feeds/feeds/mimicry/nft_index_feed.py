"""DataFeed for MimicryNFTMarketIndex query type. Fetches a NFT collections' market cap"""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.mimicry.nft_market_index import MimicryNFTMarketIndex
from telliot_feeds.sources.mimicry.nft_market_index import NFTGoSource


mimicry_nft_market_index_usd_feed = DataFeed(
    query=MimicryNFTMarketIndex(chain="ethereum", currency="usd"),
    source=NFTGoSource(currency="usd"),
)

mimicry_nft_market_index_eth_feed = DataFeed(
    query=MimicryNFTMarketIndex(chain="ethereum", currency="eth"),
    source=NFTGoSource(currency="eth"),
)

chain = None
currency = None

mimicry_nft_market_index_feed = DataFeed(
    query=MimicryNFTMarketIndex(chain=chain, currency=currency),
    source=NFTGoSource(currency=currency),
)
