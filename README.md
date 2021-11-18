# Telliot Feed Examples

## Project documentation:

- [Telliot Feed Examples](https://tellor-io.github.io/telliot-feed-examples/)

## Installation and Configuration:

- [Getting Started](https://tellor-io.github.io/telliot-feed-examples/getting-started/)

## Examples

### Report legacy ID 41 on Rinkeby

1. Make sure that Telliot is configured for Rinkeby (`chain_id=4`)

2. Report using the CLI:
   ```
   telliot-examples report uspce
   ```
3. Enter value when prompted.

### AMPL Feed Examples

First, make sure you have the required configurations:

1. Generate default AMPL configs:
    ```
    python src/telliot_feed_examples/config.py
    ```
2. Add AMPL api keys (BraveNewCoin/Rapid & AnyBlock) to `~/telliot/ampl.yaml`

#### Report legacy ID 10 once

1. Report using the CLI:
    ```
    telliot-examples report legacyid
    ```
2. When prompted, type `10` and press [ENTER].

#### Report legacy ID 10 each day after midnight UTC

1. Run a script:
    ```
    python scripts/report_usd_vwap.py
    ```
