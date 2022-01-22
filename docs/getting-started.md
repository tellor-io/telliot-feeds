# Getting Started

Installation of Telliot Feed Examples requires that Python 3.9 or greater is already
installed on your system.


## Install Telliot Feed Examples

*Optional*: Create and activate a [virtual environment](https://docs.python.org/3/library/venv.html).  
In this example, the virtual environment is located in a subfolder called `tenv`:

=== "Linux"

    ```
    python3 -m venv tenv
    source tenv/bin/activate
    ```

=== "Windows"

    ```
    py -m venv tenv
    tenv\Scripts\activate
    ```

=== "Mac M1"

    ```
    python3 -m venv tenv
    source tenv/bin/activate
    ```

You can install Telliot Feed Examples and all of it's dependencies
(including [telliot-core](https://github.com/tellor-io/telliot-core) and [chained-accounts](https://github.com/pydefi/chained-accounts)) through the command line:

    pip install telliot-feed-examples

## Telliot Configuration

After installation, Telliot must be personalized to use your own private keys and endpoints.

First, create the default configuration files:

    telliot config init

The default configuration files are created in a folder called `telliot` in the user home folder:

    ~/telliot
        ├── chains.json
        ├── endpoints.yaml
        └── main.yaml

To show the current configuration:

    telliot config show

### Configure endpoints

Edit `~/telliot/endpoints.yaml` to configure Telliot to use your own endpoints.

If you don't have an endpoint, a free one is available at [Infura.io](http://www.infura.io).  Simply replace `INFURA_API_KEY` with the one provided by Infura.

Endpoints should be configured for both Etherium mainnet and Rinkeby testnet.

**Warning! All telliot software and reporter feeds should be validated on Rinkeby prior to deploying on mainnet.**

Note that endpoints must use the websocket protocol because HTTPS endpoints do not support event listeners. If reporting on Polygon, websockets are not supported, so use an HTTPS endpoint

*Example `endpoints.yaml` file:*
```yaml
type: EndpointList
endpoints:
- type: RPCEndpoint
  chain_id: 1
  network: mainnet
  provider: Infura
  url: wss://mainnet.infura.io/ws/v3/{INFURA_API_KEY}
  explorer: https://etherscan.io
- type: RPCEndpoint
  chain_id: 4
  network: rinkeby
  provider: Infura
  url: wss://rinkeby.infura.io/ws/v3{INFURA_API_KEY}
  explorer: https://rinkeby.etherscan.io
- type: RPCEndpoint
  chain_id: 137
  network: mainnet
  provider: Matic
  url: https://polygon-mainnet.infura.io/v3/{INFURA_API_KEY}
  explorer: https://polygonscan.com/
- type: RPCEndpoint
  chain_id: 80001
  network: mumbai
  provider: Matic
  url: https://polygon-mumbai.infura.io/v3/{INFURA_API_KEY}
  explorer: https://mumbai.polygonscan.com/
...
```
Once you've specified your endpoints, what's left is to configure your account information (private keys, chain IDs, et.) using `chained-accounts`.

### Save Account Info

Save your encrypted private keys and account information via the command line. Instructions [here](https://github.com/pydefi/chained-accounts). Once finished,  read the [Usage](https://tellor-io.github.io/telliot-feed-examples/usage/) section, then you'll be set to report.

## Other possible configs
### AMPL

If you'd like to report legacy AMPL values, generate default AMPL configs from the repository's home directory:
```
python3 src/telliot_feed_examples/config.py
```

After, add AMPL api keys (BraveNewCoin/Rapid & AnyBlock) to `~/telliot/ampl.yaml`

*Example `ampl.yaml` file:*
```yaml
type: AMPLConfigOptions
anyblock_api_key: 'abc123fakeapikey'
rapid_api_key: 'abc123fakeapikey'

```
