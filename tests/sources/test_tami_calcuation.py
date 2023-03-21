from datetime import datetime
from datetime import timezone

from dateutil.relativedelta import relativedelta

from telliot_feeds.sources.mimicry.tami import create_index_value_history
from telliot_feeds.sources.mimicry.tami import get_index_ratios
from telliot_feeds.sources.mimicry.tami import get_index_value
from telliot_feeds.sources.mimicry.tami import tami
from telliot_feeds.sources.mimicry.types import IndexValueHistoryItem
from telliot_feeds.sources.mimicry.types import Transaction
from telliot_feeds.sources.mimicry.utils import filter_valid_transactions
from telliot_feeds.sources.mimicry.utils import sort_transactions

now = datetime.utcnow()
yesterday = (now - relativedelta(days=1)).replace(tzinfo=timezone.utc)
two_days_ago = (now - relativedelta(days=2)).replace(tzinfo=timezone.utc)
three_days_ago = (now - relativedelta(days=3)).replace(tzinfo=timezone.utc)
one_month_ago = (now - relativedelta(months=1)).replace(tzinfo=timezone.utc)
six_weeks_ago = (now - relativedelta(weeks=6)).replace(tzinfo=timezone.utc)
two_years_ago = (now - relativedelta(years=2)).replace(tzinfo=timezone.utc)


mock_transaction_history = [
    Transaction(itemId="Lavender", price=500, date=three_days_ago),
    Transaction(itemId="Hyacinth", price=700, date=one_month_ago),
    Transaction(itemId="Mars", price=1200, date=two_days_ago),
    # Nyx should be excluded since she did not have two transactions in the past year
    Transaction(itemId="Nyx", price=612, date=two_years_ago),
    Transaction(itemId="Hyacinth", price=400, date=three_days_ago),
    Transaction(itemId="Nyx", price=1200, date=yesterday),
    Transaction(itemId="Mars", price=612, date=six_weeks_ago),
]

expected_values = {
    "sortedTransactions": [
        {"itemId": "Nyx", "price": 612, "timestamp": two_years_ago},
        {"itemId": "Mars", "price": 612, "timestamp": six_weeks_ago},
        {"itemId": "Hyacinth", "price": 700, "timestamp": one_month_ago},
        {"itemId": "Lavender", "price": 500, "timestamp": three_days_ago},
        {"itemId": "Hyacinth", "price": 400, "timestamp": three_days_ago},
        {"itemId": "Mars", "price": 1200, "timestamp": two_days_ago},
        {"itemId": "Nyx", "price": 1200, "timestamp": yesterday},
    ],
    "validTransactions": [
        {"itemId": "Mars", "price": 612, "timestamp": six_weeks_ago},
        {"itemId": "Hyacinth", "price": 700, "timestamp": one_month_ago},
        {"itemId": "Hyacinth", "price": 400, "timestamp": three_days_ago},
        {"itemId": "Mars", "price": 1200, "timestamp": two_days_ago},
    ],
    "indexValueHistory": [
        IndexValueHistoryItem(
            itemId="Mars",
            price=612,
            indexValue=612.0,
            transaction=Transaction(itemId="Mars", price=612, date=six_weeks_ago),
        ),
        IndexValueHistoryItem(
            itemId="Hyacinth",
            price=700,
            indexValue=612.0,
            transaction=Transaction(itemId="Hyacinth", price=700, date=one_month_ago),
        ),
        IndexValueHistoryItem(
            itemId="Hyacinth",
            price=400,
            indexValue=472.0609756097561,
            transaction=Transaction(itemId="Hyacinth", price=400, date=three_days_ago),
        ),
        IndexValueHistoryItem(
            itemId="Mars",
            price=1200,
            indexValue=746.3414634146342,
            transaction=Transaction(itemId="Mars", price=1200, date=two_days_ago),
        ),
    ],
    "indexValue": 746.3414634146342,
    "indexRatios": [
        {
            "itemId": "Mars",
            "price": 1200,
            "indexValue": 746.3414634146342,
            "transaction": Transaction(itemId="Mars", price=1200, date=two_days_ago),
            "indexRatio": 1.6078431372549018,
        },
        {
            "itemId": "Hyacinth",
            "price": 400,
            "indexValue": 472.0609756097561,
            "transaction": Transaction(itemId="Hyacinth", price=400, date=three_days_ago),
            "indexRatio": 0.847348161926167,
        },
    ],
    "timeAdjustedValues": [1200, 632.4110671936759],
    "timeAdjustedMarketIndex": 1832.411067193676,
}

sorted_transactions = sort_transactions(mock_transaction_history)
valid_transactions = filter_valid_transactions(sorted_transactions)


def test_create_index_value_history():
    index_value_history = create_index_value_history(valid_transactions)
    assert index_value_history == expected_values["indexValueHistory"]


def test_get_index_ratios():
    index_value_history = create_index_value_history(valid_transactions)
    index_ratios = get_index_ratios(index_value_history)
    print(index_ratios)
    assert index_ratios == expected_values["indexRatios"]


def test_get_index_value():
    index_value_history = create_index_value_history(valid_transactions)
    index_value = get_index_value(index_value_history)
    assert index_value == expected_values["indexValue"]


def test_tami_with_transaction_data():
    value = tami(valid_transactions)
    assert value == expected_values["timeAdjustedMarketIndex"]


def test_tami_empty_transaction_data():
    value = tami([])
    assert value is None
