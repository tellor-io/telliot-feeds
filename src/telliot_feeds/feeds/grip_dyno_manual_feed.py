from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.grip_dyno_challenge_query import ETHDC2025test
from telliot_feeds.sources.manual.grip_dyno_manual_source import gripDynoManualSource

challengeType = "grip_strength_dynamometer"

grip_dyno_manual_feed = DataFeed(
    query=ETHDC2025test(challengeType=challengeType),
    source=gripDynoManualSource(),
)
