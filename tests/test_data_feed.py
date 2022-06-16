""" Simple example of creating a "plug-in" data feed

"""
from telliot_feed_examples.datafeed import DataFeed
from telliot_feed_examples.datasource import RandomSource
from telliot_feed_examples.queries.legacy_query import LegacyRequest


def test_data_feed():
    """Test a new feed"""
    myfeed = DataFeed(source=RandomSource(), query=LegacyRequest(legacy_id=4))

    import yaml

    print(yaml.dump(myfeed.get_state(), sort_keys=False))
