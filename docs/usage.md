# Usage

To use any of the telliot datafeed and reporter examples, use the command line interface (CLI), `telliot-examples`. Once this package is installed, any of the below commands are available to use.

Note, by default, the `report` command will attempt to report data through the Flashbots relay.

Even if you set a profit percent threshold, you could still lose money if submitting on mainnet!

## Commands

To use any of this package's subcommands, first invoke `telliot-examples` followed by any subcommands.

### Help command

Use the help command flag to view subcommands, flag options, and their descriptions:
```
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

### Report command

Use the `report` command to submit data to the TellorX oracle. Here's an example of reporting the [USPCE value](https://github.com/tellor-io/dataSpecs/blob/main/ids/LegacyRequest-41.md) once:
```
telliot-examples --no-flashbots report --legacy-id 41 --submit-once
```

Each of the command line option flags have shorter versions. For example, the shorter version of `--legacy-id` is `-lid`. To report the [price of ETH/USD](https://github.com/tellor-io/dataSpecs/blob/main/ids/LegacyRequest-01.md) every ~12 hours:
```
telliot-examples report -lid 1
```

Use the help command flag to view all the `report` subcommand options:
```
user:~/$ telliot-examples report --help
Usage: telliot-examples report [OPTIONS]

  Report values to Tellor oracle

Options:
  -lid, --legacy-id [1|2|10|41|50|59]
                                  report to a legacy ID  [required]
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

Here's an exampels of reporting once with an expected profit percentage greater than or equal to 2%:
```
telliot-examples report --submit-once -lid 50 -p 2
```

### Tip command

Use the `tip` command to reward reporters for submitting values corresponding to a specific query ID.

Like the report command, the `--legacy-id/-lid` flag is also required to tip. Here's an example of tipping one Tellor Tribute (TRB) for the price of ETH in USD:
```
telliot-examples -lid 1 tip --amount-trb 1
```

And tipping 4.2 TRB for ETH/JPY:
```
telliot-examples -lid 59 tip -trb 4.2
```