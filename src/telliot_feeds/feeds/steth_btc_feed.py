from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.curvefi import CurveFinanceSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

steth_btc_median_feed = DataFeed(
    query=SpotPrice(asset="STETH", currency="BTC"),
    source=PriceAggregator(
        asset="steth",
        currency="btc",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="steth", currency="btc"),
            CoinpaprikaSpotPriceSource(asset="steth-lido-staked-ether", currency="btc"),
            CurveFinanceSpotPriceSource(asset="steth", currency="btc"),
        ],
    ),
)
