from statistics import stdev
from typing import List
from typing import Optional


def stdev_calculator(close_prices: List[float]) -> Optional[float]:
    """
    Calculates the percent change(daily returns) for a list of numbers and returns the standard deviation
    """

    pct_change = []
    for i, j in zip(close_prices[:-1], close_prices[1:]):
        try:
            pct = (j - i) / i
        except ZeroDivisionError:
            pct = None
        pct_change.append(pct)
    return stdev(pct_change)  # type: ignore
