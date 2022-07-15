import yaml

from telliot_feeds.feeds.ampl_usd_vwap_feed import ampl_usd_vwap_feed


def test_ampl_feed():
    """Test AMPL/USD/VWAP feed."""
    feed = ampl_usd_vwap_feed

    print(yaml.dump(feed.get_state(), sort_keys=False))
