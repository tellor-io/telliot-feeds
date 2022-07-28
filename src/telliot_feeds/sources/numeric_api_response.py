import json
from dataclasses import dataclass
from typing import Any
from typing import Optional
from typing import Union

import requests

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


def api_call(url: str) -> Union[dict[Any, Any], Any]:
    """Call any API and handle exceptions, return json dict to be parsed"""
    try:
        r = requests.get(url)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error(e)
        return None

    try:
        return r.json()
    except json.decoder.JSONDecodeError as e:
        logger.error(e)
        return None


@dataclass
class NumericApiResponseSource(DataSource[float]):
    """data source for retrieving data from api calls"""

    #: URL to call and receive JSON dict to be parsed
    url: Optional[str] = ""

    #: string of comma separated keys/list indices to parse value from JSON blob
    parseStr: Optional[str] = ""

    def main_parser(self) -> Optional[float]:
        """main method, parses key string and calls url to search returned json dict"""
        if self.url is None or self.parseStr is None:
            logger.error("Query Parameters are unset")
            return None
        rsp = api_call(self.url)
        if rsp is None:
            logger.error("None returned from API call")
            return None

        parse_list = [key.strip() for key in self.parseStr.split(",")]
        parse_list = [int(key) if key.isdigit() else key for key in parse_list]

        for key_index in parse_list:
            try:
                rsp = rsp[key_index]
            except (IndexError, KeyError) as e:
                logger.error(e)
                return None

        if isinstance(rsp, list) or isinstance(rsp, dict):
            logger.error(f"Expecting a single float. Parsed response: {rsp}")
            return None

        if isinstance(rsp, float):
            return rsp
        elif isinstance(rsp, int):
            return float(rsp)
        else:
            logger.error(f"Expecting a float. Parsed response type: {type(rsp)}")
            return None

    async def fetch_new_datapoint(self) -> OptionalDataPoint[Any]:
        """fetch new datapoint method, may need to overwrite return type"""
        val = self.main_parser()
        if val is None:
            logger.error("No value returned from API call")
            return (None, None)

        datapoint = (val, datetime_now_utc())
        self.store_datapoint(datapoint)

        logger.info(f"API info {datapoint[0]} retrieved at time {datapoint[1]}")

        return datapoint
