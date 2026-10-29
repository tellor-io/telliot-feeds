# Vendored upstream code

## terra_sdk

- **Package:** `terra-sdk==4.0.0` (terra-money/terra.py, MIT License — see `terra_sdk-LICENSE`)
- **Wheel:** `terra_sdk-4.0.0-py3-none-any.whl`, sha256 `b9664b977d8b8244962d255f5979dcd828fe86ff7a884d73f92d3e5ef957d5fb`
- **Date vendored:** 2026-10-29
- **Why vendored:** terra-sdk 4.0.0's metadata pins `attrs>=21.4,<22` and
  `protobuf>=3.19,<4`, unsatisfiable against `telliot-core==0.4.1`
  (`attrs>=25.1.0`) and the CVE-2024-7254 floor `protobuf>=5.29.3`. uv hides
  this with `[tool.uv] override-dependencies`, but overrides never reach wheel
  metadata, so plain-pip users hit `ResolutionImpossible`. Upstream is dormant
  (4.0.0 is the last release ever). We vendor only `terra_sdk`;
  `terra-proto==4.0.2` and `betterproto` remain real dependencies.
- **Scope:** the full import closure of the used surface — 97 `.py` files.
  The directory keeps the original `terra_sdk` name so future upstream diffs
  are trivial. Self-imports were rewritten to `telliot_feeds._vendor.terra_sdk`
  (see git history); `terra_proto` imports were left alone.

### Closure recipe (how to regenerate/verify)

Run from the repo root against the installed wheel:

```bash
.venv/bin/python - <<'EOF'
import sys, pathlib
for m in ["terra_sdk.client.lcd","terra_sdk.client.lcd.api.tx","terra_sdk.core",
          "terra_sdk.core.msg","terra_sdk.core.coins","terra_sdk.core.bech32",
          "terra_sdk.core.public_key","terra_sdk.core.signature_v2","terra_sdk.core.tx",
          "terra_sdk.key.raw"]:
    __import__(m)
files = sorted({sys.modules[k].__file__ for k in sys.modules
                if k.startswith("terra_sdk") and getattr(sys.modules[k], "__file__", "")})
print(len(files))
EOF
```

Expect: `97` (`client/` 22, `core/` 62, `util/` 8, `key/` 3, 2 top-level).

### Known limitation: deserialize-only helpers

The lazy imports inside `Msg.from_data/from_proto/unpack_any`,
`Authorization.from_*`, and `MsgSubmitProposal.from_*` point at
`terra_sdk.util.parse_msg` / `parse_authorization` / `parse_content`, which
are outside the closure (they are never loaded at import time). Calling those
static methods in a terra-sdk-free environment raises `ModuleNotFoundError`;
the write path (`to_data` / `to_proto` / signing / broadcast) is unaffected.
This matches the old behavior for any environment without a full terra_sdk
install; deserialization of chain responses goes through the REST/ LCD dicts
instead.
