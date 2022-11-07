"""Utilities for calculating time-based rewards (TBR)"""
from telliot_core.tellor.tellor360.oracle import Tellor360OracleContract
from telliot_core.utils.timestamp import TimeStamp

from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


async def get_time_based_rewards(oracle: Tellor360OracleContract) -> int:
    """
    Reward that will be given if a reporter submits now:
    TBR is calculated by factoring in the time of the last value to determine when it
    started accruing and the total rewards balance available in the contract since thats
    what will be dispersed if the reward is < than whats available in the contract
    """
    tbr: int
    reward: int

    time_of_last_new_value, last_val_status = await oracle.read("timeOfLastNewValue")
    tbr, tbr_status = await oracle.read("getTotalTimeBasedRewardsBalance")

    # if any call fails return 0 and a msg that tbr can't calc'd
    if not tbr_status.ok or not last_val_status.ok:
        error = tbr_status.error if not tbr_status.ok else last_val_status.error
        logger.warning(f"Unable to calculate time-based rewards for reporter: {error}")
        return 0

    reward = (
        (TimeStamp.now().ts - time_of_last_new_value) * 5e17
    ) / 300  # 0.5 tokens (5e17) dispersed every five min (300 sec)

    return reward if reward < tbr else tbr
