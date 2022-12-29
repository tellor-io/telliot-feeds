# Add New Chain Support

### Prerequisites
- Complete steps in telliot-core for supporting a new chain [here](https://tellor-io.github.io/telliot-core/add-chain/).
- Install telliot-core in editable mode `pip install -e ~/path/to/telliot-core` to include new chain support in that dependency.

1. Add multicall support `src/telliot_feeds/reporters/tips/__init__.py` (assuming Multicall contract is deployed on chain).
2. Add chain ID to `AUTOPAY_CHAINS` constant in `src/telliot_feeds/reporters/reporter_autopay_utils.py`.
