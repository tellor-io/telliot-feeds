from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.gyd_source import gydCustomSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


gyd_usd_median_feed = DataFeed(
    query=SpotPrice(asset="GYD", currency="USD"),
    source=PriceAggregator(
        asset="gyd",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="gyd", currency="usd"),
            gydCustomSpotPriceSource(asset="gyd", currency="usd"),
        ],
    ),
)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        feed = gyd_usd_median_feed
        v, _ = await feed.source.fetch_new_datapoint()
        print(v)

        # res = await source.service.get_total_liquidity_of_pools()
        # print(res)

    asyncio.run(main())
