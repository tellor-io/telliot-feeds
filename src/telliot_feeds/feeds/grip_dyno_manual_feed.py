from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.grip_dyno_challenge_query import EthDenverChallenge2025
from telliot_feeds.sources.manual.grip_dyno_manual_source import gripDynoManualSource

challengeType = "grip_strength_dynometer"

grip_dyno_manual_feed = DataFeed(
    query=EthDenverChallenge2025(challengeType=challengeType),
    source=gripDynoManualSource(),
)
