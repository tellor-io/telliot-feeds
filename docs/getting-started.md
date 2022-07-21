# Getting Started

Installation of Telliot Feeds requires that Python 3.9 or greater is already
installed on your system.


## Install Telliot Feeds

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

You can install Telliot Feeds and all of it's dependencies
(including [telliot-core](https://github.com/tellor-io/telliot-core) and [chained-accounts](https://github.com/pydefi/chained-accounts)) through the command line:

    pip install telliot-feeds

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

Endpoints should be configured for both Ethereum mainnet and Rinkeby testnet.

**Warning! All telliot software and reporter feeds should be validated on testnets prior to deploying on mainnet.**

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

### Add Reporting Accounts

The reporter needs to know which accounts are available for submitting values to the oracle.
Use the command line to add necessary reporting accounts/private keys.

For example, to add an account called `my-matic-acct` for reporting on polygon mainnet (EVM chain_id=137):

    >> chained add my-matic-acct 0x57fe7105302229455bcfd58a8b531b532d7a2bb3b50e1026afa455cd332bf706 137
    Enter encryption password for my-matic-acct: 
    Confirm password: 
    Added new account my-matic-acct (address= 0xcd19cf65af3a3aea1f44a7cb0257fc7455f245f0) for use on chains (137,)

Note that reporting accounts can be used for ETH mainnet (chain_id=1), Rinkeby testnet (chain_id=4), or Polygon testnet
(chain_id=80001).  Also note that a single account/private key can be associated with multiple chains.

Detailed instructions for managing EVM accounts can be found in the
[`chained_accounts` package documentation](https://github.com/pydefi/chained-accounts). 

After configuring accounts, read the [Usage](https://tellor-io.github.io/telliot-feeds/usage/) section,
then you'll be set to report.

## Other possible configs
### AMPL

If you'd like to report legacy AMPL values, generate default AMPL configs from the repository's home directory:
```
python3 src/telliot_feeds/config.py
```

After, add AMPL api keys (BraveNewCoin/Rapid & AnyBlock) to `~/telliot/api_keys.yaml`
In addition, to use sources that require an API key, add them using the following example.

*Example `api_keys.yaml` file:*
```yaml
type: ApiKey
name: 'anyblock'
key: 'abc123fakeapikey'
url: 'https://123www.api.com/

```
