from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
#from telliot_feeds.sources.gyd_source import GYDCustomSpotPriceSource

gyd_usd_median_feed = DataFeed(
    query=SpotPrice(asset="GYD", currency="USD"),
    source=GYDCustomSpotPriceSource(asset="gyd", currency="usd")
)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        feed = gyd_usd_median_feed(asset="gyd", currency="usd")
        v, _ = await feed.source.fetch_new_datapoint()
        print(v)

        # res = await source.service.get_total_liquidity_of_pools()
        # print(res)



    asyncio.run(main())