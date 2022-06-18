""" TODO: Remove these imports.  They only remain to avoid breaking
telliot-feed-examples, until it starts importing from the api module.
"""
from telliot_feed_examples.queries.legacy_query import LegacyRequest
from telliot_feed_examples.queries.price.spot_price import SpotPrice

__all__ = ["LegacyRequest", "SpotPrice"]
