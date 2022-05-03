import json
from dataclasses import dataclass

import requests
from telliot_core.datasource import DataSource
from telliot_core.dtypes.datapoint import DataPoint
from telliot_core.dtypes.datapoint import datetime_now_utc

from telliot_feed_examples.utils.log import get_logger


# recursive lookup function that will search JSON dict for instance of key, can handle one or multiple keys as well as nested lists


def recursive_lookup(search_dict: dict, field: str) -> list:
    found = []
    for key, value in search_dict.items():

        if key == field:
            found.append(value)

        elif isinstance(value, dict):
            results = recursive_lookup(value, field)
            for result in results:
                found.append(result)

        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    more_results = recursive_lookup(item, field)
                    for another_result in more_results:
                        found.append(another_result)
    return found


@dataclass
class APIQuerySource(DataSource):
    #: URL to call and receive JSON dict to be parsed
    api_url: str = ""

    #: string of comma separated args looking to find vals in API return
    arg_string: str = ""

    def api_call(self, url: str) -> dict:
        r = requests.get(url)
        files = r.json()
        return files

    def parser(self, json_dict: dict, arg_string: str) -> list:
        args = arg_string.split(",")
        results = [
            recursive_lookup(json_dict, arg.strip())
            for arg in args
            if arg.strip() != ""
        ]
        flat_results = [item for elem in results for item in elem]
        return flat_results

    def fetch_new_datapoint(self, api_url: str, arg_string: str) -> DataPoint:
        val = self.parser(self.api_call(api_url), arg_string)

        datapoint = (val, datetime_now_utc())
        self.store_datapoint(datapoint)

        logger.info(f"API info {datapoint[0]} retrieved at time {datapoint[1]}")

        return datapoint
