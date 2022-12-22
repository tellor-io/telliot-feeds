from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.daily_volatility import DailyVolatility
from telliot_feeds.sources.manual.daily_volatility_manual_source import DailyVolatilityManualSource


asset = ""
currency = ""
days = None

daily_volatility_manual_feed = DataFeed(
    query=DailyVolatility(asset=asset, currency=currency, days=days),  # type: ignore
    source=DailyVolatilityManualSource(),
)
