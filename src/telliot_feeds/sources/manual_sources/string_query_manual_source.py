from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from typing import Optional


class StringQueryManualSource(DataSource[Optional[str]]):

    async def fetch_new_datapoint(self) -> OptionalDataPoint[str]:
        text = None
        msg = "Type your string query response:"
        print(f"{msg}\n")

        while text is None:
            usr_inpt = input()

            # not sure what to catch here but possible bytes that could be passed via something other than the cli
            # since everything will be interepreted to string when passed through the cli.
            if len(usr_inpt) > 1 and isinstance(usr_inpt, str):
                text = usr_inpt
            else:
                print("Invalid input. use regular text! (Example input: the earth is flat, jk!)")
                continue

            print(f"\nString query response to be submitted to oracle->: {text}")
            print("Press [ENTER] to confirm.")
            _ = input()
        datapoint = (text, datetime_now_utc())
        self.store_datapoint(datapoint)

        return datapoint
