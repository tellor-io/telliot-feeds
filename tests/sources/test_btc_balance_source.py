from datetime import datetime
from unittest import mock

import pytest

from telliot_feeds.sources.btc_balance import BTCBalanceSource


@pytest.mark.asyncio
async def test_btc_balance():
    """Retrieve random number."""
    # "1652075943"  # BCT block num: 731547
    with mock.patch("telliot_feeds.utils.input_timeout.InputTimeout.__call__", side_effect=["1652075943", ""]):
        btc_bal_source = BTCBalanceSource(address="bc1q06ywseed6sc3x2fafppchefqq8v9cqd0l6vx03", timestamp=1706051389)
        v, t = await btc_bal_source.fetch_new_datapoint()

        assert v == 151914

        assert isinstance(v, int)
        assert isinstance(t, datetime)


@pytest.mark.asyncio
async def test_no_value_from_api():
    """Test that no value is returned if the API returns no value."""
    with mock.patch("requests.Session.get", return_value=mock.Mock(json=lambda: {"status": "0", "result": None})):
        btc_bal_source = BTCBalanceSource(address="bc1q06ywseed6sc3x2fafppchefqq8v9cqd0l6vx03", timestamp=1706051389)
        v, t = await btc_bal_source.fetch_new_datapoint()
        assert v is None
        assert t is None
