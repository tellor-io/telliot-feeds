from dataclasses import dataclass
from datetime import datetime
from typing import Union


@dataclass
class Transaction:
    itemId: Union[float, int]
    price: Union[float, int]
    date: datetime


@dataclass
class InclusionMapValue:
    past_year_sale_count: int
    has_sale_in_last_six_months: bool
    is_valid: bool


@dataclass
class IndexRatiosByCollection:
    price: Union[float, int]
    indexPrice: Union[float, int]
    indexRatio: Union[float, int]


@dataclass
class IndexValueHistoryItem:
    itemId: Union[float, int, str]
    price: Union[float, int]
    indexValue: Union[float, int]
    transaction: Transaction
