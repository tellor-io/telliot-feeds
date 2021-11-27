# Telliot Feed Examples

## Project documentation:

- [Telliot Feed Examples](https://tellor-io.github.io/telliot-feed-examples/)

## Installation and Configuration:

- [Getting Started](https://tellor-io.github.io/telliot-feed-examples/getting-started/)

## Usage:

- [Usage](https://tellor-io.github.io/telliot-feed-examples/usage/)

## Examples

### Report legacy ID 41 on Rinkeby

1. Report using the CLI:
   ```
   telliot-examples report --legacy-id 41
   ```
2. Enter value when prompted.

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
    telliot-examples report -lid 10 --submit-once
    ```
