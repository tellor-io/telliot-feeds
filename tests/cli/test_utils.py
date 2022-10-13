from unittest import mock

from telliot_feeds.cli.utils import build_query
from telliot_feeds.queries.price.spot_price import SpotPrice


def test_build_query():
    """Test building a query."""
    with (
        mock.patch("simple_term_menu.TerminalMenu.show", return_value=7),
        mock.patch("click.prompt", side_effect=["eth", "usd"]),
    ):
        query = build_query()
        assert isinstance(query, SpotPrice)
        assert query.asset == "eth"
        assert query.currency == "usd"
