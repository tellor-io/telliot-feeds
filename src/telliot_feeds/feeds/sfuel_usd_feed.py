from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.sfuel_source import sFuelCustomSpotPriceSource


sfuel_usd_feed = DataFeed(
    query=SpotPrice(asset="sFUEL", currency="USD"),
    source=sFuelCustomSpotPriceSource(asset="sfuel", currency="usd")
)

if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        feed = sfuel_usd_feed
        v, _ = await feed.source.fetch_new_datapoint()
        print(v)

        # res = await source.service.get_total_liquidity_of_pools()
        # print(res)

    asyncio.run(main())
