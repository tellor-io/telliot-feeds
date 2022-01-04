# Usage

To use any of the telliot datafeed and reporter examples, use the command line interface (CLI) entry point, `telliot-examples`. Once this package is installed and your `stakers.yaml` and `endpoints.yaml` have been updated, any of the below commands are available to use.

By default, the `report` command will submit transactions to the public mempool, not through the Flashbots relay, so there's a possibility of being beaten by those submitting through Flashbots. Getting transactions mined by submitting bundles through the Flashbots relay is not a profit guarantee, as those with higher reputation or more sophisticated monitoring can often win out over newer participants. In general, reporting for profit is highly competitive.

Overall, this is experimental software, so even if you specify an expected profit percent, you could still lose money if submitting on mainnet!

## Commands

To use any of this package's subcommands, first invoke `telliot-examples` followed by any subcommands.

### Help command

Use the help command flag to view any subcommands, flag options, and their descriptions:
```
user:~/$ telliot-examples --help
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

Each of the command line option flags have shorter versions. For example, the shorter version of `--legacy-id` is `-lid`. To report the [price of ETH/USD](https://github.com/tellor-io/dataSpecs/blob/main/ids/LegacyRequest-01.md) every ~12 hours at an expected profit of 5%:
```
telliot-examples report -lid 1 -p 5
```

Again, use the help command flag to view any info about these subcommand flag options:
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

### Reporting with Flashbots

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