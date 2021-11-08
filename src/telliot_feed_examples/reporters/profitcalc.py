""" Profit Calculation

This module provides utilities for determining if transactions will
be profitable given a user's configuration settings.
"""


def profitable(tb_reward: int, tip: int, gas: int, gas_price: int) -> bool:
    """TODO: Basic profit calculation for data reporting"""
    return tb_reward + tip > gas * gas_price
