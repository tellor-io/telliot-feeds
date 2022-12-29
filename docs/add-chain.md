# Add New Chain Support

### Prerequisites
- Complete steps in telliot-core for supporting a new chain [here]()
- Install telliot-core in editable mode `pip install -e ~/path/to/telliot-core`

1. Add multicall support `telliot_feeds.reporters.tips.__init__.py` (assuming Multicall contract is deployed on chain)
2. Add chain ID to line 369 in `telliot_feeds.reporters.reporter_autopay_utils.autopay_suggested_report`