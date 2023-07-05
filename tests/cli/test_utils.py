from unittest import mock

import pytest
from hexbytes import HexBytes

from telliot_feeds.cli.utils import build_query
from telliot_feeds.cli.utils import CustomHexBytes
from telliot_feeds.queries.abi_query import AbiQuery
from telliot_feeds.queries.price.spot_price import SpotPrice


def test_build_query():
    """Test building a query."""
    queries = [q for q in AbiQuery.__subclasses__() if q.__name__ not in ("LegacyRequest")]
    options = sorted([q.__name__ for q in queries])
    idx = options.index("SpotPrice")
    with (
        mock.patch("simple_term_menu.TerminalMenu.show", return_value=idx),
        mock.patch("click.prompt", side_effect=["eth", "usd"]),
    ):
        query = build_query()
        assert isinstance(query, SpotPrice)
        assert query.asset == "eth"
        assert query.currency == "usd"


def test_custom_hexbytes_wrapper():
    """Test custom hexbytes wrapper."""
    # test when 0x is present and not present
    for value in (CustomHexBytes("0x1234"), CustomHexBytes("1234")):
        value = CustomHexBytes("0x1234")
        assert value.hex() == "0x1234"
        assert isinstance(value, CustomHexBytes)
        assert isinstance(value, HexBytes)
        assert isinstance(value, bytes)
    with pytest.raises(ValueError):
        CustomHexBytes(1)
        CustomHexBytes(1.1)
        CustomHexBytes(True)
        CustomHexBytes(False)
