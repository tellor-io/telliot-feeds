from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.grip_dyno_challenge_query import GripDynoChallenge
from telliot_feeds.sources.manual.grip_dyno_manual_source import gripDynoManualSource

eventDescription = "eth_denver_2025"
challengeType = "grip_strength_dynometer"

grip_dyno_manual_feed = DataFeed(
    query=GripDynoChallenge(eventDescription=eventDescription, challengeType=challengeType),
    source=gripDynoManualSource()
)
