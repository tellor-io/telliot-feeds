# Add New Chain Support

### Prerequisites
- Complete steps in `telliot-core` for supporting a new chain [here](https://tellor-io.github.io/telliot-core/add-chain/).
- For testing reporting on your new chain, install `telliot-core` in editable mode `pip install -e ~/path/to/telliot-core` to include new chain support in that dependency. You may need to comment out the locked version of `telliot-core` in `setup.cfg` to do this, then install `telliot-feeds` in editable mode as well.

### Steps
1. Skip this entire first step if your chain is listed [here](https://github.com/mds1/multicall#multicall3-contract-addresses). If your chain was not listed at that link (already supported in the multicall package), then deploy your own Multicall contract on your new chain, and after, update `src/telliot_feeds/reporters/tips/__init__.py` to include that contract's address. Again, skip this step if your chain is listed [here](https://github.com/mds1/multicall#multicall3-contract-addresses).
2. Add chain ID to `AUTOPAY_CHAINS` constant in `src/telliot_feeds/reporters/reporter_autopay_utils.py`.
3. Make sure there's a datafeed for the chain's native token in `src/telliot_feeds/feeds/`. If there isn't, add one by following the steps [here](https://tellor-io.github.io/telliot-feeds/add-spot-price/).
4. Support profit checks by updating `get_native_token_feed` in `src/telliot_feeds/utils/reporter_utils.py` to return the datafeed for your new chain's native token.
5. Once you've done a new release of `telliot-core`, update that dependency in this package's `setup.cfg` to the new version.
