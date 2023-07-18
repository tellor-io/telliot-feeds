from collections import deque
from dataclasses import dataclass
from dataclasses import field
from typing import Deque
from typing import Optional

from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


@dataclass
class StakeInfo:
    """Check if a datafeed is in dispute
    by tracking staker balance flucutations.
    """

    max_data: int = 2
    last_report: int = 0
    reports_count: int = 0

    stake_amount_history: Deque[int] = field(default_factory=deque, init=False, repr=False)
    staker_balance_history: Deque[int] = field(default_factory=deque, init=False, repr=False)

    def __post_init__(self) -> None:
        self.stake_amount_history = deque(maxlen=self.max_data)
        self.staker_balance_history = deque(maxlen=self.max_data)

    def store_stake_amount(self, stake_amount: int) -> None:
        """Add stake amount to deque and maintain a history of 2"""
        self.stake_amount_history.append(stake_amount)

    def store_staker_balance(self, stake_balance: int) -> None:
        """Add staker info to deque and maintain a history of 2"""
        self.staker_balance_history.append(stake_balance)

    def update_last_report_time(self, last_report: int) -> None:
        """Update last report time"""
        self.last_report = last_report

    def update_reports_count(self, reports_count: int) -> None:
        """Update report count"""
        self.reports_count = reports_count

    @property
    def last_report_time(self) -> int:
        """Return report count"""
        return self.last_report

    def is_in_dispute(self) -> bool:
        """Check if staker has been disputed"""
        if len(self.staker_balance_history) == self.max_data:
            if self.staker_balance_history[-1] < self.staker_balance_history[-2]:
                logger.warning("Your staked balance has decreased, account might be in dispute")
                return True
        return False

    def stake_amount_change(self) -> bool:
        """Check oracle stake amount change"""
        logger.info(f"Current Oracle stakeAmount: {self.stake_amount_history[-1] / 1e18!r}")
        if len(self.stake_amount_history) == self.max_data:
            if self.stake_amount_history[-1] < self.stake_amount_history[-2]:
                logger.info("Oracle stake amount has decreased")
            if self.stake_amount_history[-1] > self.stake_amount_history[-2]:
                logger.info("Oracle stake amount has increased")
            return True
        return False

    @property
    def stake_amount_gt_staker_balance(self) -> bool:
        """Compare staker balance and oracle stake amount"""
        if not self.stake_amount_history or not self.staker_balance_history:
            logger.debug("Not enough data to compare stake amount and staker balance")
            return False
        if self.stake_amount_history[-1] > self.staker_balance_history[-1]:
            logger.info("Staker balance is less than oracle stake amount")
            return True
        return False

    @property
    def current_stake_amount(self) -> int:
        """Return the current stake amount"""
        if self.stake_amount_history:
            return self.stake_amount_history[-1]
        else:
            return 0

    @property
    def current_staker_balance(self) -> Optional[int]:
        """Return the current staker balance"""
        if self.staker_balance_history:
            return self.staker_balance_history[-1]
        else:
            return None

    def update_staker_balance(self, amount: int) -> None:
        """Update staker balance"""
        balance = self.current_staker_balance
        if balance is not None:
            new_amount = balance + amount
            self.store_staker_balance(new_amount)
