# Usage

Prerequisites: [Getting Started](https://tellor-io.github.io/telliot-feeds/getting-started/)

To report data to Tellor oracles, or access any other functionality, use the `telliot` CLI. A basic example:

```
$ telliot report -a acct1 -ncr -qt trb-usd-spot
```

**Be sure to always confirm the correct settings when prompted and read chain-specific usage sections before setting up your reporter!**

# Table of Contents

- [Reporting Basics](#reporting-basics)
- [Reporting on Ethereum](#reporting-on-ethereum)
- [Reporting on Polygon](#reporting-on-polygon)

# Reporting Basics

**Note: When using the `report` command, `telliot` will automatically attempt to stake the minimum required to report. To see the current stake amount, find the oracle contract on your desired chain [here](https://docs.tellor.io/tellor/the-basics/contracts-reference), then call `getStakeAmount` in the contract's read functions section on the block explorer. The returned value is denominated in wei.**

## Help flag

Use the help flag to view all available commands and option flags:

```
$ telliot --help
```

The help flag shows subcommand options as well:

```
$ telliot report --help
Usage: telliot report [OPTIONS]

  Report values to Tellor oracle

Options:
  -b, --build-feed                build a datafeed from a query type and query
                                  parameters
  -qt, --query-tag [trb-usd-spot|ohm-eth-spot|vsq-usd-spot|bct-usd-spot|dai-usd-spot|ric-usd-spot|idle-usd-spot|mkr-usd-spot|sushi-usd-spot|matic-usd-spot|usdc-usd-spot|gas-price-oracle-example|eur-usd-spot|snapshot-proposal-example|eth-usd-30day_volatility|numeric-api-response-example|diva-protocol-example|string-query-example|pls-usd-spot|eth-usd-spot|btc-usd-spot|tellor-rng-example|twap-eth-usd-example|ampleforth-uspce|ampleforth-custom|albt-usd-spot|rai-usd-spot]
                                  select datafeed using query tag
  -gl, --gas-limit INTEGER        use custom gas limit
  -mf, --max-fee INTEGER          use custom maxFeePerGas (gwei)
  -pf, --priority-fee INTEGER     use custom maxPriorityFeePerGas (gwei)
  -gp, --gas-price INTEGER        use custom legacy gasPrice (gwei)
  -p, --profit TEXT               lower threshold (inclusive) for expected
                                  percent profit
  -tx, --tx-type TEXT             choose transaction type (0 for legacy txs, 2
                                  for EIP-1559)
  -gps, --gas-price-speed [safeLow|average|fast|fastest]
                                  gas price speed for eth gas station API
  -wp, --wait-period INTEGER      wait period between feed suggestion calls
  -rngts, --rng-timestamp INTEGER
                                  timestamp for Tellor RNG
  -dpt, --diva-protocol BOOLEAN   Report & settle DIVA Protocol derivative
                                  pools
  -dda, --diva-diamond-address TEXT
                                  DIVA Protocol contract address
  -dma, --diva-middleware-address TEXT
                                  DIVA Protocol middleware contract address
  -custom-token, --custom-token-contract TEXT
                                  Address of custom token contract
  -custom-oracle, --custom-oracle-contract TEXT
                                  Address of custom oracle contract
  -custom-autopay, --custom-autopay-contract TEXT
                                  Address of custom autopay contract
  -360, --tellor-360 / -flex, --tellor-flex
                                  Choose between Tellor 360 or Flex contracts
  -s, --stake FLOAT               ❗Telliot will automatically stake more TRB
                                  if your stake is below or falls below the
                                  stake amount required to report. If you
                                  would like to stake more than required,
                                  enter the TOTAL stake amount you wish to be
                                  staked. For example, if you wish to stake
                                  1000 TRB, enter 1000.
  -mnb, --min-native-token-balance FLOAT
                                  Minimum native token balance required to
                                  report. Denominated in ether.
  -cr, --check-rewards / -ncr, --no-check-rewards
                                  If the --no-rewards-check flag is set, the
                                  reporter will not check profitability or
                                  available tips for the datafeed unless the
                                  user has not selected a query tag or used
                                  the random feeds flag.
  -rf, --random-feeds / -nrf, --no-random-feeds
                                  Reporter will use a random datafeed from the
                                  catalog.
  --rng-auto / --rng-auto-off
  --submit-once / --submit-continuous
  -pwd, --password TEXT
  -spwd, --signature-password TEXT
  --help 
```

### Account Flag

You must select an account (funds address) to use for reporting. To do so, use the `--account`/`-a` flags:

```
telliot --account acct1 report
```

## Report Command

Use the `report` command to submit data to Tellor oracles. Example `report` command usage:

```
telliot report -a acct2
```

When calling the `report` command, `telliot` will ask you to confirm the reporter's settings:
  
```
...
Reporting query tag: eth-usd-spot
Current chain ID: 80001
Expected percent profit: 100.0%
Transaction type: 0
Gas Limit: 350000
Legacy gas price (gwei): None
Max fee (gwei): None
Priority fee (gwei): None
Gas price speed: fast
Desired stake amount: 10.0
Minimum native token balance: 0.25 MATIC

Press [ENTER] to confirm settings.
```
The default settings are probably fine to use on testnets, but you may want to adjust them for mainnet using the `report` command flags/options.

By default, the reporter will continue to attempt reporting whenever out of reporting lock. Use the `--submit-once` flag to only report once:

```
telliot report -a staker1 --submit-once
```

### Build Feed Flag

Use the build-a-feed flag (`--build-feed`) to build a DataFeed of a QueryType with one or more QueryParameters. When reporting, the CLI will list the QueryTypes this flag supports. To select a QueryType, enter a type from the list provided. Then, enter in the corresponding QueryParameters for the QueryType you have selected, and telliot will build the Query and select the appropriate source.

```
telliot report -a staker1 --build-feed --submit-once -p YOLO
```

## Profit Flag

**Reporting for profit is extremely competitive and profit estimates aren't guarantees that you won't lose money!**

Use this flag (`--profit/-p`) to set an expected profit. The default is 100%, which will likely result in your reporter never attempting to report unless you're on a testnet. To bypass profitability checks, use the `"YOLO"` string:

```
telliot report -a acct1 -p YOLO
```

Normal profit flag usage:

```
telliot report -a acct4 -p 2
```

**Note: Skipping profit checks does not skip checks for tips on the [AutoPay contract](https://github.com/tellor-io/autoPay). If you'd like to skip these checks as well, use the `--no-check-rewards/-ncr` flag.**

## Gas, Fee, & Transaction Type Flags

If gas fees and transaction types (`--tx-type/-tx`) aren't specified by the user, defaults and estimates will be used/retrieved.

The `--gas-price/-gp` flag is for legacy transactions, while the `--max-fee/-mf` and `--priority-fee/-pf` flags are for type 2 transactions (EIP-1559). If sending legacy transactions, you can also override the gas price estimate speed using the `--gas-price-speed/-gps` flag. To set the gas limit used for the actual `submitValue()` transaction, use the `--gas-limit/-gl` flag.

Example usage:

```
telliot report -a acct3 -tx 0 -gl 310000 -gp 9001 -p 22
```

# Reporting on Ethereum

Both transaction types (0 & 2) are supported for reporting.

## Regular Usage

It's not advised to report without Flashbots, unless on a testnet like Goerli, because transactions sent to the public mempool on Ethereum mainnet will most likely be [front-run](https://www.paradigm.xyz/2020/08/ethereum-is-a-dark-forest/), so you'll lose money.

By default, `telliot` will report without Flashbots. You need to use the signature account flag (`--signature-account/-sa`) to report with Flashbots. See [below](#using-flashbots) for more info.

## Using Flashbots

The Flashbots organization provides an endpoint, or relay, to bypass the public mempool and submit transaction bundles directly to miners. More info [here](https://github.com/flashbots/pm).

Even using Flashbots, reporting on Ethereum mainnet is competitive. Other endpoints are available to experiment with ([MiningDAO](https://github.com/Mining-DAO/mev-geth#quick-start), [mistX](https://mistx.stoplight.io/)).

If the account you've selected for reporting is staked on mainnet, then the reporter will send transactions to the Flashbots relay by default. To explicitly use Flashbots, include the `--flashbots/-fb` flag.

Reporting with Flashbots on testnet is not supported.

### Create Signatory Account

In order to submit transactions through the [Flashbots](https://docs.flashbots.net/flashbots-auction/searchers/quick-start/) relay, you need an additional Ethereum acccount. The Flashbots organization uses this signatory account's address to identify you and build your historical reputation as a MEV ["searcher"](https://docs.flashbots.net/flashbots-auction/searchers/quick-start). This signatory account doesn't need any funds in it. Store it it as a `ChainedAccount` in the same way you would any other (see [Getting Started](https://tellor-io.github.io/telliot-feeds/getting-started/)).

When reporting, select your signatory account by tag as well as your staked mainnet account. Use the `--account/-a` and `--signature-tag/-sgt` flags.

Example usage:

```
telliot report -a acct2 -sgt sigacct
```

## Staking

If reporting to Tellor360 oracles, reporters can stake multiple times. Each stake is 10 TRB, so if you stake 140 TRB, you've staked 14 times.

The reporter will automatically attempt to stake the required amount, but if you'd like to stake more than the current minimum, use the `--stake/-s` flag.

```
telliot report -a acct1 -s 2000 -ncr -rf
```

If the reporter account's actual stake is reduced after a dispute, the reporter will attempt to stake the difference in TRB to return to the original desired stake amount.

### Withdraw Stake

To withdraw your stake, there isn't a command available. Instead, you'll have to connect your wallet to the token address on your chain's explorer (e.g. [TRB on etherscan](https://etherscan.io/token/0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0#writeProxyContract)), run `requestStakingWithdraw`, wait seven days, then run `withdrawStake`.

## Reporter Lock

The amount of times a reporter can submit data to a Tellor oracles is determined by the number of stakes per 12 hours.:

```
reporter_lock = 12 hours / number_of_stakes
```

So if the current min stake amount is 10 TRB, and you have 120 TRB staked, you can report every hour. But if the min stake abount is updated to 20 TRB, you can only report every two hours.
