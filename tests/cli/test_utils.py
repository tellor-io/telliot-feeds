from unittest import mock

from telliot_feeds.cli.utils import build_query
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
