"""DataFeed for MimicryCollectionStat query type. Calculates TAMI index or NFT market cap"""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.mimicry.collection_stat import MimicryCollectionStat
from telliot_feeds.sources.mimicry.collection_stat import MimicryCollectionStatSource

chain_id = None
collection_address = None
metric = None

mimicry_collection_stat_feed = DataFeed(
    query=MimicryCollectionStat(chainId=chain_id, collectionAddress=collection_address, metric=metric),
    source=MimicryCollectionStatSource(chainId=chain_id, collectionAddress=collection_address, metric=metric),
)

chain_id = 1
collection_address = "0x5180db8F5c931aaE63c74266b211F580155ecac8"
metric = 0

mimicry_example_feed = DataFeed(
    query=MimicryCollectionStat(chainId=chain_id, collectionAddress=collection_address, metric=metric),
    source=MimicryCollectionStatSource(chainId=chain_id, collectionAddress=collection_address, metric=metric),
)
