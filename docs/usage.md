# Usage

To use any of the telliot datafeed and reporter examples, use the command line interface (CLI), `telliot-examples`. Once this package is installed, any of the below commands are available to use.

Note, by default, the `report` command will have the reporter submit values every ~12 hours on the Rinkeby test network. Also, if not specified, there is no maximum gas price used and profitability is not enforced. Even if you set a profit percent threshold, you could still lose money if submitting on mainnet!

## Commands

To use any of this package's subcommands, first invoke `telliot-examples` followed by any subcommands.

### Help command

Use the help command flag to view subcommands, flag options, and their descriptions:
```
user:~/$ telliot-examples --help
Usage: telliot-examples [OPTIONS] COMMAND [ARGS]...

  Telliot command line interface

Options:
  -pk, --private-key TEXT   override the config's private key
  -cid, --chain-id INTEGER  override the config's chain ID
  -lid, --legacy-id TEXT    report to a legacy ID  [required]
  --help                    Show this message and exit.

Commands:
  report  Report values to Tellor oracle
  tip     Tip TRB for a selected query ID
```

### Report command

Use the `report` command to submit data to the TellorX oracle. Here's an example of reporting the [USPCE value](https://github.com/tellor-io/dataSpecs/blob/main/ids/LegacyRequest-41.md) once:
```
telliot-examples --legacy-id 41 report --submit-once
```

Each of the command line option flags have shorter versions. For example, the shorter version of `--legacy-id` is `-lid`. To report the [price of ETH/USD](https://github.com/tellor-io/dataSpecs/blob/main/ids/LegacyRequest-01.md) every ~12 hours:
```
telliot-examples -lid 1 report
```

Use the help command flag to view all the `report` subcommand options:
```
user:~/$ telliot-examples report --help
Usage: telliot-examples report [OPTIONS]

  Report values to Tellor oracle

Options:
  -mgp, --max-gas-price INTEGER   maximum gas price used by reporter
  -gps, --gas-price-speed [safeLow|average|fast|fastest]
                                  gas price speed for eth gas station API
  -p, --profit FLOAT              lower threshold (inclusive) for expected
                                  percent profit
  --submit-once / --submit-continuous
  --help                          Show this message and exit.
```

Here's an exampels of reporting once with a maximum gas price (gwei) of 250, and an expected profit percentage greater than or equal to 2%:
```
telliot-examples -lid 50 report -mgp 250 -p 2
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