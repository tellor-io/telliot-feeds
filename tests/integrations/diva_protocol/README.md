## Steps to report for DIVA Protocol

1. listen for newly created pools from the DIVA subgraph (`test_listen_new_pools.py`)
2. filter for valid pools (`test_listen_new_pools.py`)
3. fetch pool info given pool ID (`test_fetch_pool_info.py`)
4. construct datafeed from pool info (`test_construct_datafeed.py`)
5. report using constructed datafeed (`test_report.py`)
6. settle pool (`test_settle_pool.py`)

`test_cli_cmds.py` Tests the needed commands for reporting using the `telliot-feeds` CLI tool.

Features for `test_claim_fees.py` are yet to be implemented.

### Addresses
DIVA Protocol new Ropsten address (DIVADiamond): `0xebBAA31B1Ebd727A1a42e71dC15E304aD8905211`

Fake ERC20 token used during testnet as collateral: dUSD: `0x134e62bd2ee247d4186A1fdbaA9e076cb26c1355`

New DIVATellorOracle on Ropsten: `0x2f4218C9262216B7B73A76334e5A98F3eF71A61c`
