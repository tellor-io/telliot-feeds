import os
from datetime import datetime

import pytest

from telliot_feed_examples.sources.aws_ec2 import AWSEC2PriceSource


@pytest.mark.asyncio
async def test_aws_ec2_source():
    """Test retrieving AWS EC2 spot prices."""
    source = AWSEC2PriceSource(region="us-east-1")

    value, timestamp = await source.fetch_new_datapoint()

    print(value)
    assert isinstance(value, str)
    assert isinstance(timestamp, datetime)
