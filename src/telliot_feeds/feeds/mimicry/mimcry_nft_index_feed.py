"""DataFeed for MimicryCollectionStat query type. Calculates TAMI index or NFT market cap"""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.sources.mimicry.mimicry_nft_market_index import NFTGoSource
from telliot_feeds.queries.mimicry.mimicry_nft_market_index import MimicryNFTMarketIndex


mimicry_nft_market_index_datafeed = DataFeed(
    query=MimicryNFTMarketIndex(chain="ethereum", currency="usd"),
    source=NFTGoSource(market_cap_currency="market_cap_usd"),
)

mimicry_nft_market_index_eth_datafeed = DataFeed(
    query=MimicryNFTMarketIndex(chain="ethereum", currency="eth"),
    source=NFTGoSource(market_cap_currency="market_cap_eth"),
)
