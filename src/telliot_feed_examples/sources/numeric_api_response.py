import json
from dataclasses import dataclass
from typing import Any
from typing import Optional
from typing import Union

import requests

from telliot_feed_examples.datasource import DataSource
from telliot_feed_examples.dtypes.datapoint import DataPoint
from telliot_feed_examples.dtypes.datapoint import datetime_now_utc
from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)


def api_call(url: str) -> Union[dict[Any, Any], Any]:
    """Call any API and handle exceptions, return json dict to be parsed"""
    try:
        r = requests.get(url)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error(e)
        return None

    files = r.json()
    return files


def find_value(key: str, json_dict: Optional[dict[Any, Any]]) -> list[Any]:
    """Parse target numeric value from JSON blob."""
    vals = []

    def decode_dict(ex_dict: dict[Any, Any]) -> dict[Any, Any]:
        """Nested search function"""
        try:
            vals.append(ex_dict[key])
        except KeyError:
            pass
        return ex_dict

    json.loads(
        json.dumps(json_dict, indent=1), object_hook=decode_dict
    )  # Return value ignored.
    return vals


@dataclass
class NumericApiResponseSource(DataSource[Any]):
    """data source for retrieving data from api calls"""

    #: URL to call and receive JSON dict to be parsed
    url: str = ""

    #: string of comma separated keys/list indices to parse value from JSON blob
    parseStr: str = ""

    def main_parser(self) -> Union[list[Any], str]:
        """main method, parses key string and calls url to search returned json dict"""
        # request url, handle exceptions
        files = api_call(self.url)
        json_obj = json.dumps(files, indent=1)

        if self.parseStr == "":
            return json_obj

        # create iterative list from parseStr
        key_list = [key.strip() for key in self.parseStr.split(",")]

        # find all vals that correspond with given keys, return them all as nested list
        results = [find_value(key, files) for key in key_list]
        results_fin = [val[0] if len(val) == 1 else val for val in results]

        return results_fin

    async def fetch_new_datapoint(self) -> DataPoint[Any]:
        """fetch new datapoint method, may need to overwrite return type"""
        val = self.main_parser()

        datapoint = (str(val), datetime_now_utc())
        self.store_datapoint(datapoint)

        logger.info(f"API info {datapoint[0]} retrieved at time {datapoint[1]}")

        return datapoint
