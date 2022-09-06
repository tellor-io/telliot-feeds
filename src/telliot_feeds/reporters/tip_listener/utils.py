from dataclasses import dataclass
from telliot_core.utils.timestamp import TimeStamp
from typing import List
from typing import Optional


@dataclass
class QueryIdIndex:
    query_id: str
    now_index: int
    month_old_index: int


@dataclass
class QueryIdValuesInfo:
    current_value: bytes
    current_value_timestamp: int
    now_index_status: bool
    now_index: int
    month_old_index_status: bool
    month_old_index: int
    query_id: str


@dataclass
class QueryIdTimestamps:
    query_id: str
    timestamps: List[TimeStamp]


@dataclass
class OneTimeTipDetails:
    query_data: bytes
    reward_amount: int


@dataclass
class FeedDetails:
    """Data types for feed details contract response"""

    reward: int
    balance: int
    startTime: int
    interval: int
    window: int
    priceThreshold: int
    rewardIncreasePerSecond: int
    feedsWithFundingIndex: int
    queryId: Optional[str] = None
    feedId: Optional[str] = None


@dataclass
class Feed:
    details: FeedDetails
    query_data: str

    def __post_init__(self) -> None:
        self.details = FeedDetails(*self.details)
