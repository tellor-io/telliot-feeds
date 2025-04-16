from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.grip_dyno_challenge_query import EthDC2025Test
from telliot_feeds.sources.manual.grip_dyno_manual_source import gripDynoManualSource

challengeType = "grip_strength_dynamometer"

grip_dyno_manual_feed = DataFeed(
    query=EthDC2025Test(challengeType=challengeType),
    source=gripDynoManualSource(),
)
