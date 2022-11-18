from dataclasses import dataclass
import operator
from typing import Any, List, Union
from typing import Optional

from __future__ import annotations

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from telliot_feeds.datasource import DataSource
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
    item_id:Union[int, str]
    price: int
    index_value: int
    index_ratio: float
    transaction: Transaction

@dataclass
class IndexValueHistoryList:
    """wrapper class for List of IndexValueHistoryItem objects, with IndexValue and IndexRatio getters"""

    index_values: List[IndexValueHistoryItem]

    async def get_index_value(self) -> int:
        """get current index value"""
        return self.index_values[-1].index_value

    async def get_index_ratios(self):
        """calculates index ratio for the last transaction of each item in the collection"""

        for last_sale in self.index_values:
            index_ratio = last_sale.price / last_sale.index_value
            last_sale.index_ratio = index_ratio

        

    

@dataclass
class TransactionList:
    """Wrapper for List of Transaction objects with sort, filter, and convert methods"""

    transactions: List[Transaction]

    async def sort_transactions(self) -> TransactionList:
        """sort of shallow copy of the tx list"""
        self.transactions.copy().sort(ascending=True, key=operator.attrgetter("timestamp"))

    async def filter_valid_transactions(self) -> TransactionList:
        """filter for valid transactions, removing invalid txs from the list"""
        one_year_ago = datetime.now() - relativedelta(years=1)
        six_months_ago = datetime.now() - relativedelta(months=6)

        inclusion_dict = {}

        for transaction in self.transactions:
            if not inclusion_dict[transaction.item_id]:
                inclusion_dict[transaction.item_id]["past_year_sale_count"] = 0
                inclusion_dict[transaction.item_id]["has_sale_in_last_six_months"] = False
                inclusion_dict[transaction.item_id]["is_valid"] = False

            if inclusion_dict[transaction.item_id]["is_valid"]:
                continue

            if not is_after(transaction.timestamp, one_year_ago):
                continue

            past_year_sale_count = inclusion_dict[transaction.item_id]["past_year_sale_count"]
            inclusion_dict[transaction.item_id]["past_year_sale_count"] += 1

            if not is_after(transaction.timestamp, six_months_ago):
                continue

            inclusion_dict[transaction.item_id]["has_sale_in_last_six_months"] = True

            if inclusion_dict[transaction.item_id]["past_year_sale_count"] >= 2:
                inclusion_dict[transaction.item_id]["is_valid"] = True

        self.transactions = [tx for tx in self.transactions if inclusion_dict[tx]["is_valid"]]

    async def create_index_value_history(self) -> IndexValueHistoryList:
        """converts TransactionList to List of IndexValueHistoryItem, adding the index value"""

        transactions_dict = {}

        last_index_value = 0
        last_divisor = 1

        result = []

        for transaction in self.transactions:

            is_first_sale = not transactions_dict[transaction.item_id]

            transactions_dict[transaction.item_id] = transaction

            item_count = transactions_dict.keys().length

            all_last_sold_value = sum(transactions_dict.values())

            index_value = all_last_sold_value / (item_count * last_divisor)

            if not transaction:
                last_index_value = index_value

                iv = IndexValueHistoryItem(transaction.item_id, transaction.price, index_value, transaction)

                result.append(iv)

                continue

            next_divisor = last_divisor * (index_value / last_index_value) if is_first_sale else last_divisor

            weighted_index_value = all_last_sold_value / ( item_count * next_divisor)

            last_index_value = weighted_index_value
            last_divisor = next_divisor

            iv = IndexValueHistoryItem(transaction.item_id, transaction.price, weighted_index_value, transaction)

        return result






@dataclass
class MimicryCollectionStatSource(DataSource[str]):
    """DataSource for GasPriceOracle expected response data."""

    chainId: Optional[int] = None
    collectionAddress: Optional[str] = None
    metric: Optional[int] = None

    async def tami(
        self,
        transaction_history: TransactionList
    ) -> Optional[float]:
        """
        Calculates Time-Adjusted Market Index.
        see https://github.com/Mimicry-Protocol/TAMI
        """

        await transaction_history.sort_transactions()
        await transaction_history.filter_valid_transactions()
        index_value_history = await transaction_history.create_index_value_history()

        if len(index_value_history) == 0:
            return None

        index_value = await index_value_history.get_index_value(index_value_history)
        index_ratios = await index_value_history.get_index_ratios(index_value_history)

        time_adjusted_values = [item.index_ratio * index_value for item in index_ratios]

        return sum(time_adjusted_values)




    async def get_collection_market_cap(
        self,
        transaction_history: List[Transaction]
    ) -> Optional[float]:
        pass

    async def request_historical_sales_data(self, contract:str, all=True) -> TransactionList:
        """Requests historical sales
         data of the selected collection.
         Data retrieved from Reservoir.
         
        Agruments:
            all (bool): if True, see all data for the selected collection (if False, only 12 months)

        Returns:
            List[Dict]: historical sales data of a collection retrieved from Reservoir

        """
        url = f"https://api.reservoir.tools/sales/v4?contract={contract}"
        headers = {
                    "accept": "*/*",
                    "x-api-key": "demo-api-key"
        }
        with requests.Session() as s:
            s.mount("https://", adapter)
            if not all:
                one_year_ago = datetime.now() - timedelta(years = 1)
                url += f"&startTimestamp={one_year_ago}"
            try:
                request = s.get(url, timeout=0.5, headers=headers)   
            except requests.exceptions.RequestException as e:
                logger.error(f"Reservoir API error: {e}")
                return None

            except requests.exceptions.Timeout as e:
                logger.error(f"Reservoir API timed out: {e}")
                return None
            
            for sale in request["sales"]:
                #price, item id, timestamp

                

    async def fetch_new_datapoint(
        self,
    ) -> OptionalDataPoint[Any]:
        """
        Calculates desired metric for a collection on the chosen chain id.

        Returns:
            float -- the desired metric
        """

        if self.metric == 0:
            past_year_sales_data = await self.request_historical_sales_data(all=False)
            if past_year_sales_data:
                return self.tami(past_year_sales_data)
            else:
                logger.error("unable to retieve NFT collection historical sales data for TAMI")
                return None
            
        elif self.metric == 1:
            all_sales_data = await self.request_historical_sales_data()
            if all_sales_data:
                return self.get_collection_market_cap(all_sales_data)
            else:
                logger.error("unable to retieve NFT collection historical sales data for total market cap")
                return None

        else:
            logger.info(msg=f"Invalid metric for Mimicry Protocol: {self.metric}")