import pytest

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.feeds.susde_usd_feed import susde_usd_median_feed
from telliot_feeds.sources.susde_fundamental_source import sUSDESpotPriceService


@pytest.mark.asyncio
async def test_susde_usd_median_feed(monkeypatch: pytest.MonkeyPatch) -> None:
    """sUSDe/USD comes from sUSDESpotPriceService (contract ratio × USDe/USD), not a top-level PriceAggregator."""

    async def fake_get_price(self: sUSDESpotPriceService, asset: str, currency: str):
        return (1202.75, datetime_now_utc())

    monkeypatch.setattr(sUSDESpotPriceService, "get_price", fake_get_price)

    v, t = await susde_usd_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v == pytest.approx(1202.75)
    assert t is not None
    print(f"sUSDe/USD Price: {v}")
