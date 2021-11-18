# Telliot Feed Examples

## Project documentation:

- [Telliot Feed Examples](https://tellor-io.github.io/telliot-feed-examples/)

## Installation and Configuration:

- [Getting Started](https://tellor-io.github.io/telliot-feed-examples/getting-started/)

## Report legacy id 41 on Rinkeby

To report the legacy request id 41 price on Rinkeby:

1. Make sure that Telliot is configured for Rinkeby (`chain_id=4`)

2. Enter the command line:

   telliot-examples report legacyid 41

## AMPLE Feed Example

1. Generate default AMPL configs:

    python src/telliot_feed_examples/config.py

2. Add your AMPL api keys to `~/telliot/ampl.yaml`
