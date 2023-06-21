from dataclasses import dataclass
from typing import Optional
from typing import TypedDict

from web3.types import Wei


@dataclass
class StakerInfo:
    """Data types for staker info
    start_date: TimeStamp
    stake_balance: int
    locked_balance: int
    reward_debt: int
    last_report: TimeStamp
    reports_count: int
    gov_vote_count: int
    vote_count: int
    in_total_stakers: bool
    """

    start_date: int
    stake_balance: int
    locked_balance: int
    reward_debt: int
    last_report: int
    reports_count: int
    gov_vote_count: int
    vote_count: int
    in_total_stakers: bool


class GasParams(TypedDict):
    maxPriorityFeePerGas: Optional[Wei]
    maxFeePerGas: Optional[Wei]
    gasPrice: Optional[Wei]  # Legacy gas price
    gas: Optional[int]  # Gas limit
