from __future__ import annotations

import operator
import time
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import requests
from dateutil.relativedelta import relativedelta
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
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
class Transaction:
    """wrapper class for nft sale transactions"""

    price: int
    item_id: Union[int, str]
    timestamp: int


@dataclass
class IndexValueHistoryItem:
    """wrapper class for transactions with index value added"""

    item_id: Union[int, str]
    price: int
    index_value: float
    transaction: Transaction
    index_ratio: float = 0


@dataclass
class IndexValueHistoryList:
    """wrapper class for List of IndexValueHistoryItem objects, with IndexValue and IndexRatio getters"""

    index_values: List[IndexValueHistoryItem]

    def get_index_value(self) -> float:
        """get current index value"""
        return self.index_values[-1].index_value

    def get_index_ratios(self) -> List[float]:
        """calculates index ratio for the last transaction of each item in the collection"""

        index_ratios = []

        last_sale_per_item_id = {}

        for item in self.index_values:
            last_sale_per_item_id[item.item_id] = item

        for item in last_sale_per_item_id.values():
            index_ratio = item.price / item.index_value
            item.index_ratio = index_ratio
            index_ratios.append(index_ratio)

        return index_ratios


@dataclass
class TransactionList:
    """Wrapper for List of Transaction objects with sort, filter, and convert methods"""

    transactions: List[Transaction] = field(default_factory=list)
    floor_price: float = 0.0

    def sort_transactions(self, by: str) -> None:
        """sort of the tx list"""
        self.transactions.sort(key=operator.attrgetter(by))

    def filter_valid_transactions(self) -> None:
        """filter for valid transactions, removing items with <2 sales in the past year from the TransactionList."""
        one_year_ago = time.time() - relativedelta(years=1).seconds
        six_months_ago = time.time() - relativedelta(months=6).seconds

        inclusion_dict: Dict[Union[str, int], Dict[str, Any]] = {}

        for transaction in self.transactions:
            if transaction.item_id not in inclusion_dict:
                inclusion_dict[transaction.item_id]: Dict[str, Any] = {}
                inclusion_dict[transaction.item_id]["past_year_sale_count"] = 0
                inclusion_dict[transaction.item_id]["has_sale_in_last_six_months"] = False
                inclusion_dict[transaction.item_id]["is_valid"] = False

            if inclusion_dict[transaction.item_id]["is_valid"]:
                continue

            if time.time() - transaction.timestamp > one_year_ago:
                continue

            inclusion_dict[transaction.item_id]["past_year_sale_count"] += 1

            if time.time() - transaction.timestamp > six_months_ago:
                continue

            inclusion_dict[transaction.item_id]["has_sale_in_last_six_months"] = True

            if inclusion_dict[transaction.item_id]["past_year_sale_count"] >= 2:
                inclusion_dict[transaction.item_id]["is_valid"] = True

        self.transactions = [tx for tx in self.transactions if inclusion_dict[tx.item_id]["is_valid"]]

    def create_index_value_history(self) -> IndexValueHistoryList:
        """
        converts TransactionList to List of IndexValueHistoryItem, adding the index value

        example IndexValueHistoryItem:
            item_id = "Hyacinth"
            price: 500
            index_value: 300
            transaction: Transaction(price=500, item_id="Hyacinth", timestmap="12345678")
            index_ratio: 0.6

        """

        transactions_dict = {}

        last_index_value = 0.0
        last_divisor = 1.0

        result = []

        count = 0

        for transaction in self.transactions:

            is_first_sale = transaction.item_id not in transactions_dict

            transactions_dict[transaction.item_id] = transaction

            item_count = len(transactions_dict.keys())

            all_last_sold_value = sum([tx.price for tx in transactions_dict.values()])

            index_value = all_last_sold_value / (item_count * last_divisor)

            if count == 0:
                last_index_value = index_value

                iv = IndexValueHistoryItem(transaction.item_id, transaction.price, index_value, transaction)

                result.append(iv)

                count += 1

                continue

            next_divisor = last_divisor * (index_value / last_index_value) if is_first_sale else last_divisor

            weighted_index_value = all_last_sold_value / (item_count * next_divisor)

            last_index_value = weighted_index_value
            last_divisor = next_divisor

            iv = IndexValueHistoryItem(transaction.item_id, transaction.price, weighted_index_value, transaction)

            result.append(iv)

            count += 1

        return IndexValueHistoryList(index_values=result)


@dataclass
class MimicryCollectionStatSource(DataSource[str]):
    """DataSource for MimicryCollectionStat expected response data."""

    chainId: Optional[int] = None
    collectionAddress: Optional[str] = None
    metric: Optional[int] = None

    def tami(self, transaction_history: TransactionList) -> Optional[float]:
        """
        Calculates Time-Adjusted Market Index.
        see https://github.com/Mimicry-Protocol/TAMI
        """

        transaction_history.sort_transactions("timestamp")
        transaction_history.filter_valid_transactions()
        index_value_history = transaction_history.create_index_value_history()

        if len(index_value_history.index_values) == 0:
            return None

        index_value = index_value_history.get_index_value()
        index_ratios = index_value_history.get_index_ratios()

        time_adjusted_values = [ratio * index_value for ratio in index_ratios]

        return sum(time_adjusted_values)

    def get_collection_market_cap(self, transaction_history: TransactionList) -> Optional[float]:
        """calculate the market cap of an NFT series based on a list of Transactions."""

        values = []
        transaction_history.sort_transactions("timestamp")

        transaction_history.transactions.reverse()

        for sale in transaction_history.transactions:
            # For each token in the collection
            # calculate its value by taking the greater value
            # between the collection's floor price and last sale price of that NFT
            if transaction_history.floor_price < sale.price:
                values.append(sale.price)
            else:
                values.append(int(transaction_history.floor_price))

            for other_sale in transaction_history.transactions:
                if other_sale.item_id == sale.item_id:
                    transaction_history.transactions.remove(other_sale)

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
        url = f"https://api.reservoir.tools/sales/v4?contract={contract}"
        headers = {"accept": "*/*", "x-api-key": "demo-api-key"}
        with requests.Session() as s:
            s.mount("https://", adapter)
            if not all:
                one_year_ago = datetime.now() - timedelta(days=365)
                start_timestamp = int(one_year_ago.timestamp())
                url += f"&startTimestamp={start_timestamp}"
            try:
                request = s.get(url, timeout=0.5, headers=headers)
            except requests.exceptions.RequestException as e:
                logger.error(f"Request to Reservoir Sales API failed: {str(e)}")
                return None

            except requests.exceptions.Timeout as e:
                logger.error(f"Reservoir API timed out: {str(e)}")
                return None

            if not request.ok:
                logger.error(f"Reservoir API request unsucessful: {request.text}")
                return None

            tx_list = TransactionList()

            try:
                sales_data = request.json()["sales"]
            except requests.exceptions.JSONDecodeError as e:
                logger.error(f"Unable to parse Reservoir Sales API response: {str(e)}")
                return None

            for sale in sales_data:

                try:
                    price = sale["price"]["amount"]["usd"]
                    item_id = sale["token"]["tokenId"]
                    timestamp = sale["timestamp"]
                except KeyError as e:
                    logger.warn("Mimicry: Reservoir Sales API KeyError: " + str(e))
                    return None
                tx = Transaction(price=price, item_id=item_id, timestamp=timestamp)
                tx_list.transactions.append(tx)

            if all:
                url = (
                    "https://api.reservoir.tools/oracle/collections/floor-ask/v4?kind="
                    f"spot&currency=0x0000000000000000000000000000000000000000&twapSeconds=0&collection={contract}"
                )
                headers = {"accept": "*/*", "x-api-key": "demo-api-key"}

                try:
                    request = s.get(url, timeout=0.5, headers=headers)
                except requests.exceptions.RequestException as e:
                    logger.error(f"Request to Reservoir FloorPrice API failed: {str(e)}")
                    return None

                except requests.exceptions.Timeout as e:
                    logger.error(f"Request to Reservoir FloorPrice API timed out: {str(e)}")
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
            past_year_sales_data = await self.request_historical_sales_data(contract=self.collectionAddress, all=False)
            if past_year_sales_data:
                return self.tami(past_year_sales_data), datetime_now_utc()
            else:
                logger.error("unable to retieve NFT collection historical sales data for TAMI")
                return None, None

        elif self.metric == 1:
            all_sales_data = await self.request_historical_sales_data(contract=self.collectionAddress)
            if all_sales_data:
                return self.get_collection_market_cap(all_sales_data), datetime_now_utc()
            else:
                logger.error("unable to retieve NFT collection historical sales data for total market cap")
                return None, None

        else:
            logger.info(msg=f"Invalid metric for Mimicry Protocol: {self.metric}")
            return None, None
