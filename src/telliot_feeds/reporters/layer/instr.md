# Layer

- Add endpoint to `~/telliot/endpoints.yaml`

```json
NETWORKS = {
    123456: "layer"
}
```

- Add network to `<pathto>/telliot_core/apps/core.py`

- Add chain info the endpoints.yaml:

```json
- type: RPCEndpoint
  chain_id: 123456
  network: layer
  provider: Local
  url: "http://127.0.0.1:1317/"
  explorer: https://antietam.tellor.io/
```
- Export account from layer node:

`./layerd keys export alice --keyring-dir ~/.layer/alice  --keyring-backend test --unarmored-hex --unsafe`

- Add your layer account as a telliot account:

`telliot account add layeracct dd37b2bb86947972f29003a52c6aef5072f98ef9d978695af968596b030a1248 123456`

- Start telliot layer:

`telliot layer -a layeracct`
