"""Tests for these spot price feeds:

AAVE/USD
AVAX/USD
BADGER/USD
BCH/USD
COMP/USD
CRV/USD
DOGE/USD
DOT/USD
EUL/USD
FIL/USD
GNO/USD
LINK/USD
LTC/USD
SHIB/USD
UNI/USD
USDT/USD
YFI/USD
"""
from typing import Optional
from urllib.parse import urlencode

import pytest
import requests

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds import *  # noqa: F403, F401
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import API_KEY
from telliot_feeds.sources.price.spot.coingecko import coingecko_coin_id
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceService
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource

pytestmark = pytest.mark.live


def _coingecko_source(feed: DataFeed) -> Optional[CoinGeckoSpotPriceSource]:  # type: ignore[type-arg]
    """Return the CoinGecko price source behind a (possibly aggregated) feed, if any."""
    for source in getattr(feed.source, "sources", [feed.source]):
        if isinstance(source, CoinGeckoSpotPriceSource):
            return source
    return None


@pytest.mark.asyncio
async def test_spot_price_feeds() -> None:
    """Test popular spot price feeds with ONE batched CoinGecko request.

    The CoinGecko /simple/price endpoint accepts up to 100 comma-separated
    coin ids, so instead of one request per feed (17 requests bursting
    against the rate-limited public API and making CI flaky with 429s),
    fetch every asset price in a single call and validate it against each
    matching feed's CoinGecko source.
    """
    assets = [
        "AAVE",
        "AVAX",
        "BADGER",
        "BCH",
        "COMP",
        "CRV",
        "DOGE",
        "DOT",
        "EUL",
        "FIL",
        "GNO",
        "LINK",
        "LTC",
        "SHIB",
        "UNI",
        "USDT",
        "YFI",
    ]
    # Map each popular asset to the feed and its CoinGecko source (some feeds,
    # e.g. USDT/USD, are priced by other providers and keep a direct fetch)
    asset_feeds = {}
    for _name, obj in globals().items():
        if isinstance(obj, DataFeed) and isinstance(obj.query, SpotPrice):
            if obj.query.currency.lower() == "usd" and obj.query.asset.upper() in assets:
                asset_feeds[obj.query.asset.upper()] = obj

    assert sorted(asset_feeds) == sorted(assets), "Missing feeds for popular assets"

    coingecko_sources = {
        asset: source for asset, obj in asset_feeds.items() if (source := _coingecko_source(obj)) is not None
    }

    coin_ids = sorted({coingecko_coin_id[src.asset.lower()] for src in coingecko_sources.values()})
    service = CoinGeckoSpotPriceService()
    request_url = service.url + "/api/v3/simple/price?{}".format(
        urlencode({"ids": ",".join(coin_ids), "vs_currencies": "usd"})
    )
    headers = {"Accepts": "application/json"}
    if API_KEY != "":
        headers["x-cg-pro-api-key"] = API_KEY

    response = requests.get(request_url, headers=headers, timeout=10)
    assert response.status_code == 200
    prices = response.json()
    # CoinGecko silently drops unknown ids, so assert every requested id came back
    assert coin_ids == sorted(prices)

    for asset, source in coingecko_sources.items():
        price = float(prices[coingecko_coin_id[source.asset.lower()]]["usd"])
        print(f"Testing {asset}/USD: {price}")
        assert price > 0

    # Feeds not backed by CoinGecko fetch their own providers (one call each)
    for asset, obj in asset_feeds.items():
        if asset not in coingecko_sources:
            print(f"Testing {asset}/USD via {type(obj.source).__name__}")
            v, _ = await obj.source.fetch_new_datapoint()
            assert v is not None and v > 0
