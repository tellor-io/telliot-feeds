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
*This Docker Setup guide is for Linux Ubuntu. The commands will be different for Windows, Mac, and other Linux distros.*
### Prerequisites
- Linux Ubuntu 20.04
- Follow the Step 1 instructions [here](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-20-04) for installing Docker on Linux Ubuntu. For example, an Ubuntu AWS instance (t2.medium) with the following specs:
    - Ubuntu 20.04
    - 2 vCPUs
    - 4 GB RAM
- Install Docker Compose & Docker CLI:
    ```
    sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin
    ```

*If you get permission errors with the Ubuntu install commands or using docker, run them as root with `sudo ` prefixed to your command.*

### Install Telliot Feeds Using Docker
Use the following commands to create and run a container with the correct Python version and dependencies to configure and run Telliot:

1. Pull image from docker hub:
```
sudo docker pull tellorofficial/telliot
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
sudo docker compose up -d
```
4. Open shell to container: 
```
sudo docker exec -it telliot_container sh
```
5. Next [configure telliot](#telliot-configuration) inside the container. To close shell to the container run: `exit`. If you exit the shell, the container will still be running in the background, so you can open a new shell to the container at any time with the command above. This is useful if running telliot from a remote server like an AWS instance. You can close the shell and disconnect from the server, but the container can still be running Telliot in the background.

## Telliot Configuration

After installation, Telliot must be personalized to use your own private keys and endpoints.

First, create the default configuration files:

    telliot config init

The default configuration files are created in a folder called `telliot` in the user's home folder.

To view your current configuration at any time:

    telliot config show

### Add Reporting Accounts

The reporter (telliot) needs to know which accounts (wallet addresses) are available for submitting values to the oracle.
Use the command line to add necessary reporting accounts/private keys.

For example, to add an account called `myacct1` for reporting on Polygon mainnet (chain ID 137). You'll need to replace the private key in this example with the private key that holds your TRB for reporting:

    >> telliot account add myacct1 0x57fe7105302229455bcfd58a8b531b532d7a2bb3b50e1026afa455cd332bf706 137
    Enter encryption password for myacct1: 
    Confirm password: 
    Added new account myacct1 (address= 0xcd19cf65af3a3aea1f44a7cb0257fc7455f245f0) for use on chains (137,)

To view other options for managing accounts with telliot, use the command:
    
        telliot account --help

After adding accounts, [configure your endpoints](#configure-endpoints).

### Configure endpoints

You can add your RPC endpoints via the command line or by editing the `endpoints.yaml` file. It's easier to do via the command line, but here's an example command using the [nano](https://www.nano-editor.org/) text editor to edit the YAML file directly:
    
    nano ~/telliot/endpoints.yaml

To configure your endpoint via the CLI, use the `report` command and enter `n` when asked if you want to keep the default settings:
```
$ telliot report -a myacct1
INFO    | telliot_core | telliot-core 0.1.9
INFO    | telliot_core | Connected to polygon-mumbai [default account: myacct1], time: 2023-01-24 08:25:36.676658
Your current settings...
Your chain id: 80001

Your mumbai endpoint: 
 - provider: Infura
 - RPC url: https://polygon-mumbai.infura.io/v3/****
 - explorer url: https://mumbai.polygonscan.com/
Your account: myacct1 at address 0x1234...
Proceed with current settings (y) or update (n)? [Y/n]:
...
```
Once you enter your endpoint via the CLI, it will be saved in the `endpoints.yaml` file.

To skip reporting after you've updated your configuration, press `Ctrl+C` to exit once it prompts you to confirm your settings:
```
...
Press [ENTER] to confirm settings.
...
```

If you don't have your own node URL, a free one can be obtained at [Infura.io](http://www.infura.io).  Simply replace `INFURA_API_KEY` with the one provided by Infura.

Note that endpoints should use the websocket (wss) protocol because HTTPS endpoints do not support event listeners. (If reporting on Polygon, websockets are not supported, so the HTTPS endpoint is fine.)

**Once you've added an endpoint, you can read the [Usage](https://tellor-io.github.io/telliot-feeds/usage/) section,
then you'll be set to report.**

## Other possible configs
*Note: These configs are not necessary to run Telliot, so you can skip this section and move on to [Usage](./usage.md) if you've already finished installing Telliot, adding accounts, and adding endpoints.*

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
