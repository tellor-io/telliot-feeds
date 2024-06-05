from dataclasses import dataclass
from typing import Any
from typing import Optional

import requests
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


@dataclass
class snapshotVoteResultSource(DataSource[Any]):
    """datasource for snapshot retrieving a vote result"""

    proposalId: Optional[str] = None
    transactionsHash: Optional[str] = None
    moduleAddress: Optional[str] = None
    cfg: TelliotConfig = TelliotConfig()

    def get_response(self, proposalId: Optional[str]) -> Optional[bool]:
        url = "https://hub.snapshot.org/graphql"
        query = """
        query proposal($id: String!) {
          proposal(id: $id) {
            title
            state
            scores
            choices
          }
        }
        """
        variables = {"id": proposalId}
        response = requests.post(url, json={"query": query, "variables": variables})
        data = response.json()

        if "errors" in data:
            print("Error fetching proposal data:", data["errors"])
            return None

        proposal = data.get("data", {}).get("proposal")

        if proposal:
            title = proposal.get("title")
            state = proposal.get("state")
            scores = proposal.get("scores")
            choices = proposal.get("choices")

            if not scores or not choices:
                logger.error("Unable to automatically handle vote result (check proposal at snapshot.org)")
                return None

            outcome = {
                "title": title,
                "state": state,
                "scores": scores,
                "choices": choices,
                "winner": choices[scores.index(max(scores))] if scores else None,
            }

            # log the outcome
            if outcome:
                logger.info(f"Proposal Title: {outcome['title']}")
                logger.info(f"State: {outcome['state']}")
                logger.info("Scores by choice:")
            for choice, score in zip(outcome["choices"], outcome["scores"]):
                logger.info(f"{choice}: {score}")
                logger.info(f"Winner: {outcome['winner']}")

            # return the outcome
            if outcome["winner"] == "For":
                logger.info("Vote result: For")
                return True
            elif outcome["winner"] == "Against":
                logger.info("Vote result: Against")
                return False
            else:
                logger.info("Is proposal structure 'For/Against'? (restart with -b to report manually)")
                return None

        else:
            logger.error("Proposal details not found. Please check proposal id.")
            return None

    async def fetch_new_datapoint(self) -> OptionalDataPoint[bool]:
        """Prepare Current time-stamped boolean result of vote."""
        try:
            vote_passed = self.get_response(self.proposalId)
            if vote_passed is True:
                return True, datetime_now_utc()
            elif vote_passed is False:
                return False, datetime_now_utc()
            else:
                return None, None

        except Exception as e:
            logger.info(f"Unable to fetch vote result. Error: {e}")
            return None, None


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        proposalId = "0xe089feff7538a3700e41a8b6a8feae72933ffdb394aa559c5ef544e66f353e4d"
        source = snapshotVoteResultSource(proposalId=proposalId)
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
