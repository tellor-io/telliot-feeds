import operator
from datetime import datetime
from datetime import timezone
from typing import Dict
from typing import List
from typing import Union

from dateutil.relativedelta import relativedelta

from telliot_feeds.sources.mimicry.types import InclusionMapValue
from telliot_feeds.sources.mimicry.types import Transaction


def sort_transactions(transaction_history: List[Transaction]) -> List[Transaction]:
    """Given a list of transactions, this returns those transactions sorted in chronological order."""
    return sorted(transaction_history, key=operator.attrgetter("date"))


def filter_valid_transactions(transaction_history: List[Transaction]) -> List[Transaction]:
    """Given a list of transactions, this returns only transactions that have at least
    2 sales in the last year, and at least one sale in the last 6 months."""
    now = datetime.utcnow()
    one_year_ago = (now - relativedelta(years=1)).replace(tzinfo=timezone.utc)
    six_months_ago = (now - relativedelta(months=6)).replace(tzinfo=timezone.utc)

    inclusion_map: Dict[Union[float, int], InclusionMapValue] = {}
    for transaction in transaction_history:

        item_id = transaction.itemId
        date = transaction.date

        if item_id not in inclusion_map:
            inclusion_map[item_id] = InclusionMapValue(0, False, False)

        current_map_item = inclusion_map[item_id]

        if current_map_item.is_valid:
            continue

        if date < one_year_ago:
            continue

        current_map_item.past_year_sale_count += 1

        if date < six_months_ago:
            continue

        current_map_item.has_sale_in_last_six_months = True

        if current_map_item.past_year_sale_count >= 2:
            current_map_item.is_valid = True

    return [transaction for transaction in transaction_history if inclusion_map[transaction.itemId].is_valid]
