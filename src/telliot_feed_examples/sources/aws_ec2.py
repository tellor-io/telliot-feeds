"Example AWS EC2 spot price sources."
import requests
from telliot_core.types.datapoint import datetime_now_utc
from telliot_core.types.datapoint import OptionalDataPoint

from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)

AVAILABILITY_REGIONS = {"us-east-1"}


class AWSEC2PriceSource:
    """AWS EC2 Price Service"""

    def __init__(self, region: str) -> None:
        self.name: str = "AWS EC2 Service"
        self.url: str = "http://167.172.239.133:5000"
        self.region: str = region

    async def fetch_new_datapoint(self) -> OptionalDataPoint[str]:
        """Implement PriceServiceInterface

        This implementation gets spot prices from API provided
        by Morphware."""

        self.region = self.region.lower()

        if self.region not in AVAILABILITY_REGIONS:
            raise Exception(f"Given availability region not supported: {self.region}")

        data = (
            '{"provider":"amazon","service":"compute","region":"' + self.region + '"}'
        )
        request_url = f"{self.url}/products"
        headers = {
            "content-type": "application/json",
        }

        with requests.Session() as s:
            try:
                r = s.post(request_url, data=data, headers=headers)
                json_data = r.json()
                print(json_data.keys())
                d = {"response": json_data}

            except requests.exceptions.ConnectTimeout as e:
                d = {"error": "Timeout Error", "exception": e}

            except Exception as e:
                d = {"error": str(type(e)), "exception": e}

        if "error" in d:
            logger.error(d)
            return None, None

        elif "response" in d:
            response = d["response"]

            try:
                prices = str(response["products"][0])
            except KeyError as e:
                msg = f"Error parsing API response: KeyError: {e}"
                logger.warning(msg)

        else:
            raise Exception("Invalid response from API")

        return prices, datetime_now_utc()
