"""Utilities for calculating time-based rewards (TBR)"""
from telliot_core.tellor.tellor360.oracle import Tellor360OracleContract

from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


async def get_time_based_rewards(oracle: Tellor360OracleContract) -> int:
    """
    Time based rewards, as of Tellor360,
    are the TRB balance in the Oracle contract
    minus the TRB staking rewards and
    the totalStakeAmount
    """

    tbr: int

    tbr, status = await oracle.read("getTotalTimeBasedRewardsBalance")

    if status.ok:
        return tbr

    else:
        logger.warning("Unable to calculate time-based rewards for reporter: " + status.error)
        return 0
