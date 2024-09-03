# Layer

- Add endpoint to `~/telliot/endpoints.yaml`
- Add network to `<pathto>/telliot_core/apps/core.py`  

```json
NETWORKS = {
    123456: "layer"
}
```

- `telliot account add layeracct dd37b2bb86947972f29003a52c6aef5072f98ef9d978695af968596b030a1248 123456`
- `telliot layer -a layeracct`
