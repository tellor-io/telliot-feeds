from dataclasses import dataclass
from typing import Optional

from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.sources.price.historical.cryptowatch import CryptowatchHistoricalPriceService
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.stdev_calculator import stdev_calculator


logger = get_logger(__name__)


class CryptowatchHistoricalOHLCPriceService(CryptowatchHistoricalPriceService):
    """Cryptowatch Historical Daily OHLC Price Service"""

    async def get_price(
        self,
        asset: str,
        currency: str,
        period: int = 30 * 86400,  # thirty days in seconds
        ts: Optional[int] = None,
        candle_periods: int = 86400,  # one day in seconds
    ) -> OptionalDataPoint[float]:

        """Implement PriceServiceInterface

        This implementation gets the historical price from
        the Cryptowatch API using a timestamp. Historical prices are
        fetched from Cryptowatch's recorded Coinbase-pro data.

        Documentation for Cryptowatch API:
        https://docs.cryptowat.ch/rest-api/markets/ohlc
        """
        candles, dt = await self.get_candles(
            asset=asset, currency=currency, ts=ts, period=period, candle_periods=candle_periods
        )
        if candles is not None:
            try:
                if len(candles) < 30:
                    logger.warning("Not enough data to calculate volatility.")
                    return None, None
                close_prices = [i[4] for i in candles]

                volatility = stdev_calculator(close_prices)

                return volatility, dt

            except IndexError as e:
                msg = f"Error parsing Cryptowatch API candle data: IndexError: {e}"
                logger.error(msg)

            except Exception as e:
                logger.error(e)

        return None, None


@dataclass
class CryptowatchHistoricalOHLCPriceSource(PriceSource):
    ts: int = 0
    asset: str = ""
    currency: str = ""
    service: CryptowatchHistoricalOHLCPriceService = CryptowatchHistoricalOHLCPriceService(ts=ts)

    def __post_init__(self) -> None:
        self.service.ts = self.ts
