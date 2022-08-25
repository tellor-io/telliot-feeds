"""
Settle a derivative pool in DIVA Protocol after reporting the value of
it's reference asset and collateral token.

Call `setFinalReferenceValue` on the DivaOracleTellor contract.
Ensure it can't be called twice, or if there's no reported value for the pool,
or if it's too early for the pool to be settled."""
import pytest


@pytest.mark.asyncio
async def test_create_report_settle_pool():
    """
    Test settling a derivative pool in DIVA Protocol after reporting the value of
    it's reference asset and collateral token.
    """
    # create pool
    # ensure pool was created in mock contract
    # check pool params are valid
    # check pool setFinalRef status
    # check data provider

    # update min period undisputed in mock contract
    # create temp pickle file for pool info
    
    # instantiate reporter w/ mock contracts & data provider and any other params

    # check initial state of pools pickle file

    # mock fetch pools from subgraph
    # run report for diva reporter, mock sleep to stop early

    # check value reported to flex contract
    # check pool info updated in pickle file
    # check pool settled in mock contract

    # run report again, check no new pools picked up, unable to report & settle

    # clean up temp pickle file
    pass
