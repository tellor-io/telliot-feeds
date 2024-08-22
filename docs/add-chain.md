# Add New Chain Support

### Prerequisites
- Complete steps in `telliot-core` for supporting a new chain [here](https://tellor-io.github.io/telliot-core/add-chain/).
- For testing reporting on your new chain, install `telliot-core` in editable mode `pip install -e ~/path/to/telliot-core` to include new chain support in that dependency. You may need to comment out the locked version of `telliot-core` in `setup.cfg` to do this, then install `telliot-feeds` in editable mode as well.

### Steps
1. Update `src/telliot_feeds/reporters/tips/__init__.py` with an `add_multicall_support...` block for multicall3 support on the new chain. Check if your chain is listed [here](https://www.multicall3.com/deployments). If the chain *is* on the list, you can use the standard multicall3 Deployment address. If the new chain was not listed, then you will need to deploy your own multicall3 contract, and use that address instead.
2. Check if there is a a previously defined feed for the new chain's native token price defined in `src/telliot_feeds/feeds/`. If there is not, add the feed by following the steps [here](https://tellor-io.github.io/telliot-feeds/add-spot-price/).
3. Add the new network ID to the appropriate list in `src/telliot_feeds/constants.py`. If the chain uses a different native token from any of the other networks listed, add the set of chain ids that will use the same native token. E.g.: `MANTLE_CHAINS = {5001, 5000}`.
5. Add your network's native token map to `src.telliot_feeds.utils.reporter_utils.get_native_token_feed` and `src.telliot_feeds.utils.reporter_utils.tkn_symbol` (if not already there).
6. Once you've done a new release of `telliot-core`, update that dependency in this package's `setup.cfg` to the new version.
