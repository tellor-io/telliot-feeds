"Example AWS EC2 spot price feeds."
from telliot_core.datafeed import DataFeed
from telliot_core.queries.string_query import StringQuery

from telliot_feed_examples.sources.aws_ec2 import AWSEC2PriceSource

aws_ec2_us_east_1_feed = DataFeed(
    query=StringQuery(text="AWS EC2 spot prices for us-east-1?"),
    source=AWSEC2PriceSource(region="us-east-1"),
)
