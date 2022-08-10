from typing import Optional

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint


class StringQueryManualSource(DataSource[Optional[str]]):
    async def fetch_new_datapoint(self) -> OptionalDataPoint[str]:

        print("Type your string query response:\n")

        usr_inpt = input()

        print(f"\nString query response to be submitted to oracle->: {usr_inpt}")
        print("Press [ENTER] to confirm.")
        _ = input()

        datapoint = (usr_inpt, datetime_now_utc())
        self.store_datapoint(datapoint)

        return datapoint
