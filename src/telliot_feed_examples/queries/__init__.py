""" TODO: Remove these imports.  They only remain to avoid breaking
telliot-feed-examples, until it starts importing from the api module.
"""
from telliot_core.queries.legacy_query import LegacyRequest
from telliot_core.queries.price.spot_price import SpotPrice

__all__ = ["LegacyRequest", "SpotPrice"]
