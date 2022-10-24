"""Utilities for calculating time-based rewards (TBR)"""

from typing import Optional
from telliot_feeds.utils.contract import Contract

from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)

async def get_time_based_rewards(oracle: Contract) -> int:
    """
    Time based rewards, as of Tellor360,
    are the TRB balance in the Oracle contract
    minus the TRB staking rewards and
    the totalStakeAmount
    """
    
    tbr, status = await oracle.read("getTotalTimeBasedRewardsBalance")

    if status.ok:
        return tbr

    else:
        logger.warning("Unable to calculate time-based rewards for reporter")
        return 0, status