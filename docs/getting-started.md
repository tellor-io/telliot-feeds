# Getting Started

## Prerequisites
- An account with your chain's native token for gas fees. Testnets often have a faucet. For example, [here is Polygon's](https://faucet.polygon.technology/) for Mumbai testnet.
- [Test TRB](https://docs.tellor.io/tellor/the-basics/readme#need-testnet-tokens-trb) for staking.
- [Python 3.9](https://www.python.org/downloads/release/python-3915/) is required to install and use`telliot-feeds`. Alternatively, you can use our [docker](https://docs.docker.com/get-started/) release. If using Docker, please follow the [Docker setup instructions](#optional-docker-setup).


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
*Skip this section if you already have Python 3.9 and and the correct dependencies installed.*
### Prerequisites
- Install [Docker Desktop](https://docs.docker.com/desktop/) on [Windows](https://docs.docker.com/desktop/install/windows-install/), [Mac](https://docs.docker.com/desktop/install/mac-install/), or [Linux](https://docs.docker.com/engine/install/ubuntu/). If you choose Linux, use Ubuntu. For example, an AWS instance (t2.medium) with the following specs:
    - Ubuntu 20.04
    - 2 vCPUs
    - 4 GB RAM

*If you get permission errors with the Ubuntu install commands or using docker, run them as root with `sudo ` prefixed to your command. Also, if you get a `docker.service could not be found` error, run `sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin`.*

### Install Telliot Feeds Using Docker
Once Docker Desktop (which includes the Docker Engine, Docker Compose, and the Docker CLI) is installed, you can use the following commands to create and run a container with the correct Python version and dependencies to configure and run Telliot:

1. Pull image from docker hub:
```
docker pull tellorofficial/telliot
```
2. Create the following `docker-compose.yml` file using the command:
```
echo "services:
  telliot:
    image: tellorofficial/telliot
    container_name: telliot_container
    build: .
    tty: true
    entrypoint: sh" > docker-compose.yml
```
3. Create & start container in background:
```
docker compose up -d
```
4. Open shell to container: 
```
docker exec -it telliot_container sh
```
5. Next [configure telliot](#telliot-configuration) inside the container. To close shell to the container run: `exit`. If you exit the shell, the container will still be running in the background, so you can open a new shell to the container at any time with the command above. This is useful if running telliot from a remote server like an AWS instance. You can close the shell and disconnect from the server, but the container can still be running Telliot in the background.

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
