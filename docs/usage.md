# Usage

**This is experimental software! You might lose money!**

Prerequisites: [Getting Started](https://tellor-io.github.io/telliot-feeds/getting-started/)

To use any of the telliot datafeed and reporter examples, use the command line interface (CLI) tool. A basic example:

```
$ telliot-feeds --account fakename report
```

**Be sure to always confirm the correct settings when prompted and read chain-specific usage sections before setting up your reporter!**

```
$ telliot-feeds -a fakename report
telliot-core 0.0.10.dev1
telliot_feeds (plugin): Version 0.0.12dev0
Using: eth-rinkeby [staker: dev-acct-4]

Reporting with synchronized queries
Current chain ID: 4
Expected percent profit: 100.0%
Transaction type: 0
Gas Limit: 350000
Legacy gas price (gwei): None
Max fee (gwei): None
Priority fee (gwei): None
Gas price speed: fast

Press [ENTER] to confirm settings.
```

# Table of Contents

- [Reporting Basics](#reporting-basics)
- [Reporting on Ethereum](#reporting-on-ethereum)
- [Reporting on Polygon](#reporting-on-polygon)

# Reporting Basics

## Help flag

Use the help flag to view available commands and option flags:

```
$ telliot-feeds --help
Usage: telliot-feeds [OPTIONS] COMMAND [ARGS]...

  Telliot command line interface

Options:
  -a, --account TEXT              Name of account used for reporting.
  -sgt, --signature-tag TEXT      use specific signature account by tag
  -fb, --flashbots / -nfb, --no-flashbots
  --test_config                   Runs command with test configuration
                                  (developer use only)
  --help                          Show this message and exit.

Commands:
  report  Report values to Tellor oracle
  tip     Tip TRB for a selected query ID
```

The help flag shows subcommand options as well:

```
$ telliot-feeds report --help
Usage: telliot-feeds report [OPTIONS]

  Report values to Tellor oracle

Options:
  -qt, --query-tag [eth-usd-legacy|btc-usd-legacy|ampl-legacy|uspce-legacy|trb-usd-legacy|eth-jpy-legacy|ohm-eth-spot]
                                  select datafeed using query tag
  -gl, --gas-limit INTEGER        use custom gas limit
  -mf, --max-fee INTEGER          use custom maxFeePerGas (gwei)
  -pf, --priority-fee INTEGER     use custom maxPriorityFeePerGas (gwei)
  -gp, --gas-price INTEGER        use custom legacy gasPrice (gwei)
  -p, --profit TEXT               lower threshold (inclusive) for expected
                                  percent profit
  -tx, --tx-type INTEGER          choose transaction type (0 for legacy txs, 2
                                  for EIP-1559)
  -gps, --gas-price-speed [safeLow|average|fast|fastest]
                                  gas price speed for eth gas station API
  --submit-once / --submit-continuous
  --help                          Show this message and exit.
```

## Account Flag

You must select an account to use for reporting. The account flag (`--account`/`-a`) is used to retrieve a [ChainedAccount](https://github.com/pydefi/chained-accounts) with a corresponding name. This `ChainedAccount` stores the account's checksum address, private key, and chain IDs. Example usage:

```
telliot-feeds -a fakeaccountname report
```

## Report Command

Use the `report` command to submit data to the TellorX or TellorFlex oracles. Example `report` command usage:

```
telliot-feeds -a bigdaddysatoshi report
```

By default, the reporter will continue to attempt reporting whenever out of reporting lock. Use the `--submit-once` flag to only report once:

```
telliot-feeds -a staker1 report --submit-once
```

### Build Feed Flag

Use the build-a-feed flag (`--build-feed`) to build a DataFeed of a QueryType with one or more QueryParameters. When reporting, the CLI will list the QueryTypes this flag supports. To select a QueryType, enter a type from the list provided. Then, enter in the corresponding QueryParameters for the QueryType you have selected, and telliot-feeds will build the Query and select the appropriate source.

ex: \
input...
```sh
telliot-feeds -a staker1 report --build-feed --submit-once -p YOLO
```

output...
```
Enter a valid Query Type: NumericApiResponse
Enter value for Query Parameter url: https://api.coingecko.com/api/v3/simple/price?ids=uniswap&vs_currencies=usd&include_market_cap=false&include_24hr_vol=false&include_24hr_change=false&include_last_updated_at=falsw
Enter value for Query Parameter parseStr: uniswap, usd
```

## Profit Flag

**Reporting for profit is extremely competitive and profit estimates aren't guarantees that you won't lose money!**

Use the profit flag (`--profit/-p`) to.. specify an expected profit. The default is 100% profit, which will likely result in your reporter never attempting to report unless you're on a testnet. To bypass profitability checks, use the `"YOLO"` string:

```
telliot-feeds -a staker1 report -p YOLO
```

Normal profit flag usage:

```
telliot-feeds -a staker4000 report -p 2
```

## Gas, Fee, & Transaction Type Flags

If gas fees and transaction types (`--tx-type/-tx`) aren't specified by the user, defaults and estimates will be used/retrieved.

The `--gas-price/-gp` flag is for legacy transactions, while the `--max-fee/-mf` and `--priority-fee/-pf` flags are for type 2 transactions (EIP-1559). If sending legacy transactions, you can also override the gas price estimate speed using the `--gas-price-speed/-gps` flag. To set the gas limit used for the actual `submitValue()` transaction, use the `--gas-limit/-gl` flag.

Example usage:

```
telliot-feeds -a kevin report -tx 0 -gl 310000 -gp 9001 -p 22
```

# Reporting on Ethereum

Both transaction types (0 & 2) are supported for reporting.

## Regular Usage

It's not advised to report without Flashbots, unless on a testnet like Rinkeby, because transactions sent to the public mempool on Ethereum mainnet will most likely be [front-run](https://www.paradigm.xyz/2020/08/ethereum-is-a-dark-forest/), so you'll lose money.

If you want to report without flashbots on Ethereum mainnet, use the `--no-flashbots/-nfb` flag.

Example usage:

```
telliot-feeds -a mainnetstaker7 -nfb report
```

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
telliot-feeds -a mainnetstaker1 -sgt sigacct -fb report
```

# Reporting on Polygon

Only legacy transaction types are supported. Also, TellorFlex on Polygon has no built-in rewards for reporting, so profitability checks are skipped. Read more about TellorFlex on Polygon [here](https://github.com/tellor-io/tellorFlex).

Example usage:

```
telliot-feeds -a mumbaistaker report
```

## Staking

With TellorFlex on Polygon, reporters can stake multiple times. Each stake is 10 TRB, so if you stake 140 TRB, you've staked 14 times.

The `TellorFlexReporter` will prompt the user to enter a desired stake amount:

```
Enter amount TRB to stake if unstaked: [10.0]:
```

If the current account being used to report isn't staked, the reporter will use the CLI-entered stake amount to stake. Also, if the reporter account's actual stake is reduced after a dispute, the reporter will attempt to stake the difference in TRB to return to the original desired stake amount.

Example:

```
- user enters desired stake of 50
- reporter identifies that current address has only 40 TRB staked
- reporter stakes an additional 10 TRB, bringing the total amount staked to 50 TRB
- reporter reports
- reporter waits while in reporter lock
...
```

### Withdraw Stake

To withdraw your stake, there isn't a command available. Instead, you'll have to connect your wallet to the token address on your chain's explorer (e.g. [TRB on etherscan](https://etherscan.io/token/0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0#writeProxyContract)), run `requestStakingWithdraw`, wait seven days, then run `withdrawStake`.

## Reporter Lock

TellorX reporters on Ethereum must wait 12 hours between each data sumbission. The reporter lock for TellorFlex on Polygon is variable. It depends on how many stakes an account has. Specifically:

```
reporter_lock = 12 hours / number_of_stakes
```

So if you have 120 TRB staked, you can report every hour.
