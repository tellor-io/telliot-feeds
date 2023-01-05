# Add New Chain Support

### Prerequisites
- Complete steps in telliot-core for supporting a new chain [here](https://tellor-io.github.io/telliot-core/add-chain/).
- Install telliot-core in editable mode `pip install -e ~/path/to/telliot-core` to include new chain support in that dependency.

1. If your new chain is not listed [here](https://github.com/mds1/multicall#multicall3-contract-addresses), then deploy your own Multicall contract on said chain. After, update `src/telliot_feeds/reporters/tips/__init__.py` to include the address of your new Multicall contract.
2. Add chain ID to `AUTOPAY_CHAINS` constant in `src/telliot_feeds/reporters/reporter_autopay_utils.py`.
3. Make sure there's a datafeed for the chain's native token in `src/telliot_feeds/feeds/`. If there isn't, add one by following the steps [here](https://tellor-io.github.io/telliot-feeds/add-spot-price/).
4. Support profit checks by updating `get_native_token_feed` in `src/telliot_feeds/utils/reporter_utils.py` to return the datafeed for your new chain's native token.
