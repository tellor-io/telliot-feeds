from multicall.constants import MULTICALL2_ADDRESSES

from telliot_feeds.reporters.tips import add_multicall_support


def test_add_multicall_support(caplog):
    # add testnet support for multicall that aren't avaialable in the package
    add_multicall_support(
        network="FakeNetwork",
        network_id=2500,
        multicall2_address="0x",
    )
    assert "Network FakeNetwork already exists in multicall package" not in caplog.text
    assert MULTICALL2_ADDRESSES[2500] == "0x"
    # add testnet support for multicall that is avaialable in the package
    add_multicall_support(
        network="Chiado",
        network_id=10200,
        state_override=False,
        multicall3_address="0x08e08170712c7751b45b38865B97A50855c8ab13",
    )
    assert "Network Chiado already exists in multicall package" in caplog.text
