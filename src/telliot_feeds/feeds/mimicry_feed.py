"""DataFeed for MimicryCollectionStat query type. Calculates TAMI index or NFT market cap"""

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.mimicry import MimicryCollectionStat
from telliot_feeds.sources.mimicry import MimicryCollectionStatSource

chain_id = None
collection_address = None
metric = None

mimicry_collection_stat_datafeed = DataFeed(
    query=MimicryCollectionStat(chainId=chain_id, collectionAddress= collection_address, metric= metric),
    source=MimicryCollectionStatSource(chainId=chain_id, collectionAddress=collection_address, metric=metric)
)