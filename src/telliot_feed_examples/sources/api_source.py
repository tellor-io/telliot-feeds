import json
from dataclasses import dataclass
from typing import Any
from typing import Optional
from typing import Union

import requests
from telliot_core.datasource import DataSource
from telliot_core.dtypes.datapoint import DataPoint
from telliot_core.dtypes.datapoint import datetime_now_utc

from telliot_feed_examples.utils.log import get_logger

logger = get_logger(__name__)

"""
url : str = api url to request.
returns none and displays error code if exception thrown
"""


def api_call(url: str) -> Union[dict[Any, Any], Any]:
    """call any api and handle exceptions, return json dict to be parsed"""
    try:
        r = requests.get(url)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error(e)
        return None
    # can make exceptions more specific if needed

    files = r.json()
    return files


"""
key: str = key whose corresponding value we are searching for
json_dict: dict = api response dict we will be searching through for value of said key
"""


def find_values(key: str, json_dict: Optional[dict[Any, Any]]) -> list[Any]:
    """search json dict w/ object_hook method for value corresponding w/ given key"""
    vals = []

    def decode_dict(ex_dict: dict[Any, Any]) -> dict[Any, Any]:
        """nested search function"""
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
class APIQuerySource(DataSource):
    """data source for retrieving data from api calls"""

    #: URL to call and receive JSON dict to be parsed
    url: str = ""

    #: string of comma separated keys looking to find corresponding vals in API return
    key_str: str = ""

    def main_parser(self) -> Union[list[Any], str]:
        """main method, parses key string and calls url to search returned json dict"""
        # request url, handle exceptions
        files = api_call(self.url)
        json_obj = json.dumps(files, indent=1)

        if self.key_str == "":
            return json_obj

        # create iterative list from key_str
        key_list = [key.strip() for key in self.key_str.split(",")]

        # find all vals that correspond with given keys, return them all as nested list
        results = [find_values(key, files) for key in key_list]
        results_fin = [val[0] if len(val) == 1 else val for val in results]

        return results_fin

    async def fetch_new_datapoint(self) -> DataPoint:
        """fetch new datapoint method, may need to overwrite return type"""
        val = self.main_parser()

        datapoint = (str(val), datetime_now_utc())
        self.store_datapoint(datapoint)

        logger.info(f"API info {datapoint[0]} retrieved at time {datapoint[1]}")

        return datapoint
