"""
Settle a derivative pool in DIVA Protocol after reporting the value of
it's reference asset and collateral token.

Call `setFinalReferenceValue` on the DivaOracleTellor contract.
Ensure it can't be called twice, or if there's no reported value for the pool,
or if it's too early for the pool to be settled."""
import pytest


@pytest.mark.asyncio
async def test_set_final_ref_val():
    pass


@pytest.mark.asyncio
async def test_set_final_ref_val_fail():
    pass
