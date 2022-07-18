"""Helper functions for TellorX contracts."""
import logging
from typing import Any
from typing import Optional
from typing import Tuple

from telliot_core.contract.contract import Contract
from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus
from web3.datastructures import AttributeDict

logger = logging.getLogger(__name__)


async def write_with_retry(
    contract: Contract,
    func_name: str,
    extra_gas_price: int,
    retries: int,
    gas_limit: int,
    legacy_gas_price: Optional[int] = None,
    max_priority_fee_per_gas: Optional[int] = None,
    max_fee_per_gas: Optional[int] = None,
    **kwargs: Any,
) -> Tuple[Optional[AttributeDict[Any, Any]], ResponseStatus]:
    """For submitting any contract transaction.
    Will attempt to retry (resubmit) the transaction a set number of times
    if it fails to be picked up by the chain.
    Can submit a tx with either legacy gas strategy
    or the London fork EIP-1559 strategy

    Quick explainer...
    Legacy: gas cost = gasLimit*gasPrice where...
     - you set the gas price (simple as that!)
    EIP-1559: gas cost = gasLimit*(baseFee+priorityFee) where...
     - you can set the highest priorityFee you would pay (max_priority_fee_per_gas)
     OR
     - you can set the highest maxFee (i.e. baseFee+priorityFee)
       you are willing to pay (ths is the max_fee_per_gas)
    also...
     - baseFee is set by the block

    Args:
        contract: Contract object
        func_name (str): name of contract function
        extra_gas_price (int): the amount of gas the tx resends
            with if it fails due to gas strategy
            (adds to legacy_gas_price or max_priority_fee_per_gas
            depending on tx gas strategy)
        retries (int): number of times to attempt tx resubmission
        gas_limit (int): the maximum amount of gas units (not gas price!)
            to assign to the tx
        legacy_gas_price (int): the legacy gas price for a legacy tx
        max_priority_fee_per_gas (int): the highest priorityFee in gwei
            you would pay (see guide above)
        max_fee_per_gas (int): the highest maxFee in gwei
            (baseFee+priorityFee) you would pay (see guide above)

    Returns:
        transaction receipt (if transaction is picked up by chain)
        ResponseStatus (status of tx success)


    """

    try:
        status = ResponseStatus()
        acc = contract.node.web3.eth.account.from_key(contract.private_key)
        acc_nonce = contract.node.web3.eth.get_transaction_count(acc.address)

        # Iterate through retry attempts
        for k in range(retries + 1):

            attempt = k + 1

            if k >= 1:
                logger.info(f"Retrying {func_name} (attempt #{attempt})")

            # Attempt write
            tx_receipt, status = await contract.write(
                func_name=func_name,
                legacy_gas_price=legacy_gas_price,
                max_priority_fee_per_gas=max_priority_fee_per_gas,
                max_fee_per_gas=max_fee_per_gas,
                acc_nonce=acc_nonce,
                gas_limit=gas_limit,
                **kwargs,
            )

            logger.debug(f"Attempt {attempt} status: {status}")

            # Exit loop if transaction successful
            if status.ok and (tx_receipt is not None) and (tx_receipt["status"] == 1):
                return tx_receipt, status

            else:
                logger.info(f"Write attempt {attempt} failed:")
                msg = str(status.error)
                _ = error_status(msg, log=logger.info)

                if tx_receipt is not None:
                    tx_url = f"{contract.node.explorer}/tx/{tx_receipt['transactionHash'].hex()}"  # noqa: E501

                    if tx_receipt["status"] == 0:
                        msg = f"Write attempt {attempt} failed, tx reverted ({tx_url}):"  # noqa: E501
                        return tx_receipt, error_status(msg, log=logger.info)

                    else:
                        msg = (
                            f"Write attempt {attempt}: Invalid TX Receipt status: {tx_receipt['status']}"  # noqa: E501
                        )
                        return tx_receipt, error_status(msg, log=logger.info)

                if status.error:
                    if "replacement transaction underpriced" in status.error:
                        if legacy_gas_price is not None:
                            legacy_gas_price += extra_gas_price
                            logger.info(f"Next gas price: {legacy_gas_price}")
                        elif max_fee_per_gas is not None:
                            max_fee_per_gas += extra_gas_price
                            logger.info(f"Next max fee: {max_fee_per_gas}")
                        elif max_priority_fee_per_gas is not None:
                            max_priority_fee_per_gas += extra_gas_price
                            logger.info(f"Next priority fee: {max_priority_fee_per_gas}")
                    elif "already known" in status.error:
                        acc_nonce += 1
                        logger.info(f"Incrementing nonce: {acc_nonce}")
                    elif "nonce too low" in status.error:
                        acc_nonce += 1
                        logger.info(f"Incrementing nonce: {acc_nonce}")
                    # a different rpc error
                    elif "nonce is too low" in status.error:
                        acc_nonce += 1
                        logger.info(f"Incrementing nonce: {acc_nonce}")
                    elif "not in the chain" in status.error:
                        if legacy_gas_price is not None:
                            legacy_gas_price += extra_gas_price
                            logger.info(f"Next gas price: {legacy_gas_price}")
                        elif max_fee_per_gas is not None:
                            max_fee_per_gas += extra_gas_price
                            logger.info(f"Next max fee: {max_fee_per_gas}")
                        elif max_priority_fee_per_gas is not None:
                            max_priority_fee_per_gas += extra_gas_price
                            logger.info(f"Next priority fee: {max_priority_fee_per_gas}")
                    else:
                        extra_gas_price = 0

        status.ok = False
        status.error = "ran out of retries, tx unsuccessful"

        return tx_receipt, status

    except Exception as e:
        return None, error_status("Other error", log=logger.error, e=e)
