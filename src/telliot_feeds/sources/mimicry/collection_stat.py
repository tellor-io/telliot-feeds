from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timezone
from typing import Any
from typing import List
from typing import Optional
from typing import Union

import requests
from dateutil.relativedelta import relativedelta
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from requests.exceptions import Timeout
from urllib3.util import Retry

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.sources.mimicry.tami import tami
from telliot_feeds.sources.mimicry.types import Transaction
from telliot_feeds.sources.mimicry.utils import sort_transactions
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)


@dataclass
class TransactionList:

    transactions: List[Transaction] = field(default_factory=list)
    floor_price: float = 0.0


@dataclass
class MimicryCollectionStatSource(DataSource[float]):
    """DataSource for MimicryCollectionStat expected response data."""

    chainId: Optional[int] = None
    collectionAddress: Optional[str] = None
    metric: Optional[int] = None

    def get_collection_market_cap(self, transaction_history: TransactionList) -> Optional[float]:
        """calculate the market cap of an NFT series based on a list of Transactions."""

        values: List[Union[int, float]] = []

        sorted_transactions = sort_transactions(transaction_history.transactions)

        sorted_transactions.reverse()

        last_sale_found = []

        for sale in sorted_transactions:

            if sale.itemId in last_sale_found:
                continue

            # For each token in the collection
            # calculate its value by taking the greater value
            # between the collection's floor price and last sale price of that NFT
            if transaction_history.floor_price < sale.price:
                values.append(sale.price)
            else:
                values.append(transaction_history.floor_price)

            last_sale_found.append(sale.itemId)

        return sum(values)

    async def request_historical_sales_data(self, contract: str, all: bool = True) -> Optional[TransactionList]:
        """Requests historical sales
         data of the selected collection.
         Data retrieved from Reservoir.

        Agruments:
            all (bool): if True, see all data for the selected collection (if False, only 12 months)

        Returns:
            TransactionList: formatted historical sales data of a collection retrieved from Reservoir

        """
        continuation_token = ""
        tx_list = TransactionList()
        while True:
            url = f"https://api.reservoir.tools/sales/v4?contract={contract}"
            headers = {"accept": "*/*", "x-api-key": "demo-api-key"}
            with requests.Session() as s:
                s.mount("https://", adapter)
                if not all:
                    one_year_ago = datetime.utcnow() - relativedelta(years=1)
                    start_timestamp = int(one_year_ago.timestamp())
                    url += f"&startTimestamp={start_timestamp}"
                else:
                    url += "&startTimestamp=0"
                # paginate
                if continuation_token:
                    url += "&continuation=" + continuation_token
                # 1000 sales per page
                url += "&limit=1000"

                try:
                    request = s.get(url, timeout=10, headers=headers)
                    request.raise_for_status()
                except (RequestException, Timeout) as e:
                    logger.error(f"Request to Reservoir Sales API failed: {str(e)}")
                    return None
                except Exception as e:
                    logger.error(f"Reservoir API request unsuccessful: {e}")
                    return None

                try:
                    sales_data = request.json()["sales"]
                    continuation_token = request.json()["continuation"]
                except requests.exceptions.JSONDecodeError as e:
                    logger.error(f"Unable to parse Reservoir Sales API response: {str(e)}")
                    return None

                for sale in sales_data:

                    try:
                        price = sale["price"]["amount"]["usd"]
                        item_id = sale["token"]["tokenId"]
                        timestamp = sale["timestamp"]
                    except KeyError as e:
                        logger.error("Mimicry: Reservoir Sales API KeyError: " + str(e))
                        return None
                    tx = Transaction(
                        price=price, itemId=item_id, date=datetime.fromtimestamp(timestamp, tz=timezone.utc)
                    )
                    tx_list.transactions.append(tx)

                # if on last page
                if len(sales_data) < 1000:
                    break

        if self.metric == 1:
            url = (
                "https://api.reservoir.tools/oracle/collections/floor-ask/v4?kind="
                f"spot&currency=0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48&twapSeconds=1&collection={contract}"
            )
            headers = {"accept": "*/*", "x-api-key": "demo-api-key"}

            try:
                request = s.get(url, timeout=10, headers=headers)
                request.raise_for_status()
            except (RequestException, Timeout) as e:
                logger.error(f"Request to Reservoir FloorPrice API failed: {str(e)}")
                return None

            try:
                tx_list.floor_price = request.json()["price"]
            except requests.exceptions.JSONDecodeError as e:
                logger.error(f"Unable to parse price from Reservoir FloorPrice API response: {str(e)}")
                return None

        return tx_list

    async def fetch_new_datapoint(
        self,
    ) -> OptionalDataPoint[Any]:
        """
        Calculates desired metric for a collection on the chosen chain id.

        Returns:
            float -- the desired metric
        """

        if not self.collectionAddress:
            logger.error("Missing a collection address for Mimicry NFT index calculation")
            return None, None

        if self.metric == 0:
            past_year_sales_data = await self.request_historical_sales_data(contract=self.collectionAddress, all=True)
            if past_year_sales_data:
                tami_value = tami(past_year_sales_data.transactions)

                if not tami_value:
                    logger.info(
                        f"Unable to calculate TAMI index"
                        f"for collection {self.collectionAddress} on chain id {self.chainId}"
                    )
                    return None, None
                datapoint = (tami_value, datetime_now_utc())
                self.store_datapoint(datapoint=datapoint)
                return datapoint
            else:
                logger.error(
                    f"unable to retrieve NFT collection historical sales data for TAMI "
                    f"for collection {self.collectionAddress} on chain id {self.chainId}"
                )
                return None, None

        elif self.metric == 1:
            all_sales_data = await self.request_historical_sales_data(contract=self.collectionAddress)
            if all_sales_data:
                market_cap = self.get_collection_market_cap(all_sales_data)

                if not market_cap:
                    logger.info(
                        f"Unable to calculate NFT market cap"
                        f"for collection {self.collectionAddress} on chain id {self.chainId}"
                    )
                    return None, None
                datapoint = (market_cap, datetime_now_utc())
                self.store_datapoint(datapoint=datapoint)
                return datapoint
            else:
                logger.error("unable to retrieve NFT collection historical sales data for total market cap")
                return None, None

        else:
            logger.info(msg=f"Invalid metric for Mimicry Protocol: {self.metric}")
            return None, None


if __name__ == "__main__":

    import asyncio

    source = MimicryCollectionStatSource(
        chainId=1, collectionAddress="0x5180db8F5c931aaE63c74266b211F580155ecac8", metric=0
    )
    print(asyncio.run(source.fetch_new_datapoint()))
