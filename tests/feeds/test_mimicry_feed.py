from typing import get_type_hints

import pytest

from telliot_feeds.feeds.mimicry_feed import mimicry_collection_stat_datafeed
from telliot_feeds.queries.mimicry import MimicryCollectionStat
from telliot_feeds.sources.mimicry.collection_stat import MimicryCollectionStatSource


@pytest.mark.asyncio
async def test_feed():
    """test mimicry_collection_stat_datafeed"""
    # source test is in tests/sources/test_mimicry_source.py
    assert mimicry_collection_stat_datafeed.query.chainId is None
    assert mimicry_collection_stat_datafeed.query.collectionAddress is None
    assert mimicry_collection_stat_datafeed.query.metric is None
    assert mimicry_collection_stat_datafeed.source.chainId is None
    assert mimicry_collection_stat_datafeed.source.collectionAddress is None
    assert mimicry_collection_stat_datafeed.source.metric is None
    assert isinstance(mimicry_collection_stat_datafeed.source, MimicryCollectionStatSource)
    assert isinstance(mimicry_collection_stat_datafeed.query, MimicryCollectionStat)
    query_attributes = get_type_hints(mimicry_collection_stat_datafeed.query)
    source_attributes = get_type_hints(mimicry_collection_stat_datafeed.source)
    assert ["chainId", "collectionAddress", "metric"] == list(query_attributes.keys())
    assert ["chainId", "collectionAddress", "metric"] == list(source_attributes.keys())
