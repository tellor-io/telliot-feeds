# Getting Started


## Telliot Configuration

After installation of the `telliot-core` or any telliot data feeds,
Telliot must be personalized to use your own private keys and endpoints.

First, create the default configuration files:

    telliot config init

The default configuration files are created in a folder called `telliot` in the user home folder:

    Saved config 'main' to ~/telliot/main.yaml
    Saved config 'endpoints' to ~/telliot/endpoints.yaml
    Saved config 'chains' to ~/telliot/chains.json

To show the current configuration:

    telliot config show

### Main Configuration File

The main configuration file allows you to choose which network Telliot will interact with.
By default, Telliot is configured to run on Rinkeby testnet, as shown in the example below.
Edit the `~/telliot/main.yaml` config file for the desired configuration.

- To run on Etherium mainnet, use `chain_id: 1` and `network: mainnet`.

- To submit values to the Tellor oracle, a `private_key` must also be configured.

*Example main configuration file:*

```yaml
type: MainConfig
loglevel: INFO
chain_id: 4
network: rinkeby
private_key: ''

```


### Configure endpoints

Edit `~/telliot/endpoints.yaml` to configure Telliot to use your own endpoints.

If you don't have an endpoint, a free one is available at [Infura.io](http://www.infura.io).  Simply replace `INFURA_API_KEY` with the one provided by Infura.

Endpoints should be configured for both Etherium mainnet and Rinkeby testnet.  

!!! warning

    All telliot software and reporter feeds should be validated on Rinkeby prior to deploying on mainnet. 

Note that endpoints must use the websocket protocol because HTTPS endpoints do not support event listeners.

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

```

