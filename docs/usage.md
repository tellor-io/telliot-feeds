# Usage

**This is experimental software! You can lose money!**

Prerequisites: Update configuration files: [Getting Started](https://tellor-io.github.io/telliot-feed-examples/getting-started/)

To use any of the telliot datafeed and reporter examples, use the command line interface (CLI) tool. A basic example:
```
$ telliot-examples -st fakename report
```
**Be sure to confirm the correct settings when prompted and read chain-specific reporting sections below:**
```
$ telliot-examples -st fakename report
telliot-core 0.0.10.dev1
telliot_feed_examples (plugin): Version 0.0.12dev0
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
$ telliot-examples --help
Usage: telliot-examples [OPTIONS] COMMAND [ARGS]...

  Telliot command line interface

Options:
  -st, --staker-tag TEXT          use specific staker by tag
  -sgt, --signature-tag TEXT      use specific signature account by tag
  -fb, --flashbots / -nfb, --no-flashbots
  --help                          Show this message and exit.

Commands:
  report  Report values to Tellor oracle
```

The help flag shows subcommand options as well:
```
$ telliot-examples report --help
Usage: telliot-examples report [OPTIONS]

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

## Staker Tag Flag
You must select an account to use for reporting. The staker tag flag (`--staker-tag`/`-st`) is used to retrieve a [ChainedAccount](https://github.com/pydefi/chained-accounts) with a corresponding name. This `ChainedAccount` stores the account's checksum address, private key, and chain IDs. Example usage:
```
telliot-examples -st fakeaccountname report
```

## Report Command
Use the `report` command to submit data to the TellorX or TellorFlex oracles. Example `report` command usage:
```
telliot-examples --st bigdaddysatoshi report
```
By default, the reporter will continue to attempt reporting whenever out of reporting lock. Use the `--submit-once` flag to only report once:
```
telliot-examples -st staker1 report --submit-once
```

## Profit Flag
Use the profit flag (`--profit/-p`) to.. specify an expected profit. The default is 100% profit, which will likely result in your reporter never attempting to report unless you're on a testnet. To bypass profitability checks, use the `"YOLO"` string:
```
telliot-examples -st staker1 report -p YOLO
```
Normal profit flag usage:
```
telliot-examples -st staker4000 report -p 2
```

**Reporting for profit is extremely competitive and profit estimates aren't guarantees that you won't lose money!**

## Gas, Fee, & Transaction Type Flags
If gas fees and transaction types (`--tx-type/-tx`) aren't specified by the user, defaults and estimates will be used/retrieved.

The `--gas-price/-gp` flag is for legacy transactions, while the `--max-fee/-mf` and `--priority-fee/-pf` flags are for type 2 transactions (EIP-1559). If sending legacy transactions, you can also override the gas price estimate speed using the `--gas-price-speed/-gps` flag. To set the gas limit used for the actual `submitValue()` transaction, use the `--gas-limit/-gl` flag.

Example usage:
```
telliot-examples -st kevin report -tx 0 -gl 310000 -gp 1234 -p 22
```

# Reporting on Ethereum
## Regular Usage
## Using Flashbots

In order to submit transactions through the [Flashbots](https://docs.flashbots.net/flashbots-auction/searchers/quick-start/) relay, you need an additional private key and the associated account info in `stakers.yaml` that they'll use to identify you (and for building reputation as a Flashbots searcher). This account doesn't need any funds in it.

Here's an example of said signatory account added to `stakers.yaml`:
```yaml
type: StakerList
stakers:
- type: Staker
  tag: my_mainnet_staker
  address: '0x00001234'
  private_key: '0x00009999'
  chain_id: 1
- type: Staker
  tag: my_rinkeby_staker
  address: '0x00005678'
  private_key: '0x00009999'
  chain_id: 4
- type: Staker
  tag: flashbots-sig
  address: '0xthisaddressdoesnotexist'
  private_key: '0xthisisafakeprivatekey'
  chain_id: 1
```

After tweaking your config files, you need to select your mainnet staker as well as the signature account with the `--staker-tag/-st` and `--signature-tag/-sgt` CLI flag options, respectively. Also, add the `--flashbots/-fb` flag:
```
telliot-examples -st my_mainnet_staker -sgt flashbots-sig -fb report -lid 2 -p 10
```