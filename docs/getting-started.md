# Getting Started

## Prerequisites
Python 3.9 is required to install and use`telliot-feeds`. You can do yourself or use [docker](#setup-environment-with-docker). If you follow the docker instructions, you can skip the install and environment setup steps.


## Install Telliot Feeds

*Optional*: Create and activate a [virtual environment](https://docs.python.org/3/library/venv.html). It doesn't matter where you create the virtual environment, but your home directory is fine.
In this example, the virtual environment is located in a subfolder called `tenv`:

=== "Linux"

    ```
    python3.9 -m venv tenv
    source tenv/bin/activate
    ```

=== "Windows"

    ```
    py3.9 -m venv tenv
    tenv\Scripts\activate
    ```

=== "Mac M1"

    ```
    python3.9 -m venv tenv
    source tenv/bin/activate
    ```

You can install the needed dependencies with pip:

    pip install telliot-feeds

## (Optional) Setup environment with Docker
If you want to configure and run telliot in a docker container (skip environment setup):

- pull image from docker hub `docker pull tellorofficial/telliot`
- create the following `docker-compose.yml` using the command `echo "below text" > docker-compose.yml`:
```yaml
services:
  telliot:
    image: tellorofficial/telliot
    container_name: telliot_container
    build: .
    tty: true
    entrypoint: sh
```
- create & start container in background: `docker-compose up -d`
- open shell to container: `docker exec -it telliot_container sh`
- configure telliot (see below)
- close shell to container: `exit`

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

### Add Reporting Accounts

The reporter needs to know which accounts are available for submitting values to the oracle.
Use the command line to add necessary reporting accounts/private keys.

For example, to add an account called `my-matic-acct` for reporting on Polygon mainnet (chain ID 137):

    >> telliot account add my-matic-acct 0x57fe7105302229455bcfd58a8b531b532d7a2bb3b50e1026afa455cd332bf706 137
    Enter encryption password for my-matic-acct: 
    Confirm password: 
    Added new account my-matic-acct (address= 0xcd19cf65af3a3aea1f44a7cb0257fc7455f245f0) for use on chains (137,)

To view other options for managing accounts with telliot, use the command:
    
        telliot account --help

After configuring accounts, read the [Usage](https://tellor-io.github.io/telliot-feeds/usage/) section,
then you'll be set to report.

### Configure endpoints

You can add your RPC endpoints via the command line or by editing the `endpoints.yaml` file. To edit them via the command line, use the following command:

    telliot -a myacct report

Edit `~/telliot/endpoints.yaml` to configure Telliot to use your own endpoints.

If you don't have an endpoint, a free one is available at [Infura.io](http://www.infura.io).  Simply replace `INFURA_API_KEY` with the one provided by Infura.

Endpoints should be configured for both Ethereum mainnet and Goerli testnet.

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
