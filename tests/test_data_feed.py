""" Simple example of creating a "plug-in" data feed

"""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.datasource import RandomSource
from telliot_feeds.queries.price.spot_price import SpotPrice


def test_data_feed():
    """Test a new feed"""
    myfeed = DataFeed(source=RandomSource(), query=SpotPrice(asset="ETH", currency="USD"))

    import yaml

    print(yaml.dump(myfeed.get_state(), sort_keys=False))
