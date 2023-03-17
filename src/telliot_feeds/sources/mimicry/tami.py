from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from telliot_feeds.sources.mimicry.types import IndexValueHistoryItem
from telliot_feeds.sources.mimicry.types import Transaction
from telliot_feeds.sources.mimicry.utils import filter_valid_transactions
from telliot_feeds.sources.mimicry.utils import sort_transactions


def create_index_value_history(transaction_history: List[Transaction]) -> List[IndexValueHistoryItem]:
    """Given a list of transactions, this creates a list that contains the index value at the
    time of each transaction, and includes the transaction as well.

    Args:
    - transaction_history: A list of transactions sorted by date.

    Returns:
    - A list of IndexValueHistoryItem objects (itemId, price, indexValue, Transaction)."""
    transaction_map: Dict[Union[float, int, str], Transaction] = {}

    last_index_value = 0.0
    last_divisor = 1.0

    result = []

    for i in range(len(transaction_history)):
        transaction = transaction_history[i]

        is_first_sale = transaction_map.get(transaction.itemId) is None

        transaction_map[transaction.itemId] = transaction

        item_count = len(transaction_map)

        all_last_sold_value = sum([transaction_map[item].price for item in transaction_map])

        index_value = all_last_sold_value / (item_count * last_divisor)

        if i == 0:
            last_index_value = index_value

            result.append(
                IndexValueHistoryItem(
                    itemId=transaction.itemId, price=transaction.price, indexValue=index_value, transaction=transaction
                )
            )

            continue

        next_divisor = last_divisor * (index_value / last_index_value) if is_first_sale else last_divisor

        weighted_index_value = all_last_sold_value / (item_count * next_divisor)

        last_index_value = weighted_index_value
        last_divisor = next_divisor

        result.append(
            IndexValueHistoryItem(
                itemId=transaction.itemId,
                price=transaction.price,
                indexValue=weighted_index_value,
                transaction=transaction,
            )
        )

    return result


def get_index_value(index_value_history: List[IndexValueHistoryItem]) -> Union[float, int]:
    """Given a list of IndexValueHistoryItem, returns the index value of the last item."""
    return index_value_history[-1].indexValue if index_value_history else 0


def get_index_ratios(index_valueHistory: List[IndexValueHistoryItem]) -> List[Dict[str, Any]]:
    """Given a list of IndexValueHistoryItem, calculates the index ratio for the last transaction
    of each item in the collection. Returns a list of dict objects where each object is items from
    IndexValueHistoryItem with an additional `indexRatio` item added."""
    last_sale_map: Dict[Union[float, int, str], IndexValueHistoryItem] = {}

    for history_item in index_valueHistory:
        last_sale_map[history_item.itemId] = history_item

    return [{**item.__dict__, "indexRatio": item.price / item.indexValue} for item in last_sale_map.values()]


def tami(transaction_history: List[Transaction]) -> Optional[float]:
    """Given a list of transactions for a given collection, this calculates the
    Time Adjusted Market Index for that collection.

    Returns:
    - Optional[float]
    """
    sorted_transactions = sort_transactions(transaction_history)
    valid_transactions = filter_valid_transactions(sorted_transactions)
    index_value_history = create_index_value_history(valid_transactions)

    if len(index_value_history) == 0:
        return None

    index_value = get_index_value(index_value_history)
    index_ratios = get_index_ratios(index_value_history)
    time_adjusted_values = [index_value * item["indexRatio"] for item in index_ratios]
    time_adjusted_market_index: float = sum(time_adjusted_values)
    return time_adjusted_market_index
