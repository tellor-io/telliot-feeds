from typing import Optional


def ensure_one_tx_type(
    max_fee: Optional[int],
    priority_fee: Optional[int],
    legacy_gas_price: Optional[int]) -> int:
    """Returns a bool signifying only one transaction type's parameters
    are used. Also returns int representing tx type (0 for type 0 legacy
    transactions that use gasPrice, 2 for type 2 transactions that use
    maxFeePerGas and maxPriorityFeePerGas. Returns tuple (False, None) if
    user tries to use parameters from both tx types or if no parameter
    values are given."""

    if (max_fee is not None) or (priority_fee is not None):
        if (legacy_gas_price is not None):
            raise ValueError("Cannot use parameters from both transaction types")
        return 2
    
    if (legacy_gas_price is not None):
        return 0

    raise ValueError("Must provide one value for at least one transaction type")