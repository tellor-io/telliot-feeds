"""
Feed Funder

FeedFunder implementations provide rewards for specific Query types to incentivise
reporters to interact with the Tellor protocol and put the desired data on chain.
"""
from abc import ABC
from abc import abstractmethod

from chained_accounts import ChainedAccount


class FeedFunder(ABC):
    """
    Feed Funder Abstract Base Class

    Attributes:
        account: unlocked ChainedAccount used to fund feeds
    """

    def __init__(self, account: ChainedAccount):
        self.account = account

    @abstractmethod
    def get_feeds_to_fund(self) -> None:
        """
        Get feeds to fund.
        """
        raise NotImplementedError

    @abstractmethod
    def fund_feeds(self) -> None:
        """
        Fund feeds.
        """
        raise NotImplementedError

    @abstractmethod
    def alert_funds_exhausted(self) -> None:
        """
        Alert funds exhausted.
        """
        raise NotImplementedError
