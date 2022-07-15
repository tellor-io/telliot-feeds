import yaml

from telliot_feeds.feeds.uspce_feed import uspce_feed


def test_manual_uspce_feed():
    """Test USPCE feed."""
    feed = uspce_feed

    print(yaml.dump(feed.get_state(), sort_keys=False))
