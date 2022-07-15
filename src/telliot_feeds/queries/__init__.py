""" TODO: Remove these imports.  They only remain to avoid breaking
telliot-feeds, until it starts importing from the api module.
"""
from telliot_feeds.queries.legacy_query import LegacyRequest
from telliot_feeds.queries.price.spot_price import SpotPrice

__all__ = ["LegacyRequest", "SpotPrice"]
