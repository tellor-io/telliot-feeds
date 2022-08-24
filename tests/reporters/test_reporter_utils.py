import pytest

from telliot_feeds.utils.reporter_utils import is_online


@pytest.mark.asyncio
async def test_checking_if_online():
    """test telliot check for internet connection"""

    online = await is_online()
    assert isinstance(online, bool)
