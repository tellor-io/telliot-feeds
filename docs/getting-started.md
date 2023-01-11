# Getting Started

## Prerequisites
- An account with test TRB and your chain's native token. You can get test TRB from any Tellor playground contract [here](https://docs.tellor.io/tellor/the-basics/contracts-reference) by calling the `faucet` function with your address as the argument; however, for Polygon's Mumbai testnet and Ethereum's Goerli testnet, tweet @trbfaucet for test TRB on those chains. For your chain's native token, there's usually a faucet available. For example, [Polygon's faucet](https://faucet.polygon.technology/) for reporting on Mumbai testnet.
- [Python 3.9](https://www.python.org/downloads/release/python-3915/) is required to install and use`telliot-feeds`. Alternatively, you can use our [docker](https://docs.docker.com/get-started/) release. 

*If you're using docker, please follow the [Docker setup instructions](#optional-docker-setup).*


## Install Telliot Feeds

It's generally considered good practice to run telliot from a python [virtual environment](https://docs.python.org/3/library/venv.html). This is not required, but it helps prevent dependency conflicts with other Python programs running on your computer. 

In this example, the virtual environment will be created in a subfolder called `tenv`:

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

Once the virtual environment is activated, install telliot feeds with pip:

    pip install telliot-feeds

*If your log shows no errors, that's it! Next, follow the instructions for [configuring telliot](#telliot-configuration).*

## (Optional) Docker Setup
If you want to configure and run telliot in a docker container:

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

The default configuration files are created in a folder called `telliot` in the user's home folder:

    ~/telliot
        ├── chains.json
        ├── endpoints.yaml
        └── main.yaml

To view your current configuration at any time:

    telliot config show

### Add Reporting Accounts

The reporter (telliot) needs to know which accounts (wallet addresses) are available for submitting values to the oracle.
Use the command line to add necessary reporting accounts/private keys.

For example, to add an account called `my-matic-acct` for reporting on Polygon mainnet (chain ID 137). You'll need to replace the private key in this example with the private key that holds your TRB for reporting:

    >> telliot account add my-matic-acct 0x57fe7105302229455bcfd58a8b531b532d7a2bb3b50e1026afa455cd332bf706 137
    Enter encryption password for my-matic-acct: 
    Confirm password: 
    Added new account my-matic-acct (address= 0xcd19cf65af3a3aea1f44a7cb0257fc7455f245f0) for use on chains (137,)

To view other options for managing accounts with telliot, use the command:
    
        telliot account --help

After configuring accounts, read the [Usage](https://tellor-io.github.io/telliot-feeds/usage/) section,
then you'll be set to report.

### Configure endpoints

You can add your RPC endpoints via the command line or by editing the `endpoints.yaml` file. For example, using [nano](https://www.nano-editor.org/):
    
    nano ~/telliot/endpoints.yaml

To configure your endpoint via the CLI, use the following command:

    telliot report -a myacct

If you don't have your own node URL, a free one can be obtained at [Infura.io](http://www.infura.io).  Simply replace `INFURA_API_KEY` with the one provided by Infura.

For the funcitonality of telliot feeds, Endpoints should be configured for both Ethereum mainnet and Goerli testnet. (even if you don't plan on reporting oracle data on those networks)

**Warning! All telliot software and reporter feeds should be validated on testnets prior to deploying on mainnet.**

Note that endpoints should use the websocket (wss) protocol because HTTPS endpoints do not support event listeners. (If reporting on Polygon, websockets are not supported, so the HTTPS endpoint is fine.)

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

This will create a `api_keys.yaml` file in your telliot folder if it doesn't already exist. Add the necessary API keys (BraveNewCoin/Rapid & AnyBlock) to `~/telliot/api_keys.yaml`. (Most reporters need not do this)

Additionally, if you're going to be reporting data using sources that require API keys, add them using the following example. 

*Example `api_keys.yaml` file:*
```yaml
type: ApiKey
name: 'anyblock'
key: 'abc123fakeapikey'
url: 'https://123www.api.com/

```
