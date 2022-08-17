## Steps to report for DIVA Protocol

1. invoke cli cmd to start diva report/settle client
2. fetch pools from the DIVA subgraph (`test_get_pools.py`)
<!-- 2. filter for new & unique pools using pickled dictionary (`test_filter_pools.py`) -->
3. filter for valid pools
4. construct datafeed from pool info (`test_construct_datafeed.py`)
5. report using constructed datafeed (`test_report.py`)
7. settle pools (`test_settle_pool.py`)

`test_cli_cmds.py` Tests the needed commands for reporting using the `telliot-feeds` CLI tool.

Features for `test_claim_fees.py` are yet to be implemented.

### Addresses
DIVA Protocol Ropsten address (DIVADiamond): `0xebBAA31B1Ebd727A1a42e71dC15E304aD8905211`

Fake ERC20 token used during testnet as collateral: dUSD: `0x134e62bd2ee247d4186A1fdbaA9e076cb26c1355`

DIVATellorOracle on Ropsten: `0x2f4218C9262216B7B73A76334e5A98F3eF71A61c`

DIVATellorOracle contract on Ropsten with 10 sec delay for testing:
`0x638c4aB660A9af1E6D79491462A0904b3dA78bB2`

**IMPORTANT**
The data provider must be the DIVATellor middleware contract address
