import yaml

from telliot_feed_examples.feeds.ampl_usd_vwap_feed import ampl_usd_vwap_feed


def test_ampl_feed():
    """Test AMPL/USD/VWAP feed."""
    feed = ampl_usd_vwap_feed

    print(yaml.dump(feed.get_state(), sort_keys=False))
