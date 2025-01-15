from dataclasses import dataclass
from typing import Optional
from typing import Any
from rich import print

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.input_timeout import input_timeout
from telliot_feeds.utils.input_timeout import TimeoutOccurred
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


@dataclass
class gripDynoManualSource(DataSource[Any]):
    """User input dialog for an in-person grip strength challenge.
    The user will report their own scores and social media usernames.
    (all inputs are optional)

    returns: list of challenge partic
    """
    data_set: Optional[int] = None
    right_hand: Optional[float] = None
    left_hand: Optional[float] = None
    x_handle: Optional[str] = None
    github_username: Optional[str] = None
    hours_of_sleep: Optional[float] = None

    # user_vals = [data_set, right_hand, left_hand, x_handle, github_username, hours_of_sleep]

    def parse_user_vals(self) -> Optional[tuple[int, int, int, str, str, int]]:
        """Parse user input and return list of the participant's data."""
        print("[bold]So you've Completed the grip challenge??? [/]")
        print("[bold red]🤜 REPORT YOUR GRIP STRENGTH RESULT TO THE TELLOR ORACLE 🤛[/]\n")
        print("Welcome to the cli.")
        print("The Grip Dynometer Challenge result list has 6 values")
        print("[bold blue]They are all optional![/]")
        print('Press Enter to get started. (enter "w" for womens data set) [M/w]')
        try:
            start_selection = input_timeout().strip().lower()
            if start_selection in ('w', 'women', 'womens', "women's"):
                self.data_set = 1
            elif start_selection in ('', 'm', 'men', 'mens', "men's"):
                self.data_set = 0
            else:
                print("Invalid input. Defaulting to men's dataset (0)")
                self.data_set = 0
        except TimeoutOccurred:
            logger.info("Input timeout. Defaulting to men's dataset (0)")
            self.data_set = 0

        print("[bold]**RIGHT HAND**[/] (🦅 in pounds 🇺🇸):")
        try:
            ui_right_hand = input_timeout()
            self.right_hand = int(float(ui_right_hand) * 1e18)
            print(f"spud right hand: {self.right_hand}")
        except (TimeoutOccurred, ValueError):
            logger.info("Using 0 for RIGHT HAND strength (or ctrl+c to start over)")
            logger.info("No RIGHT HAND strength reported.(ctrl+c to start over if wrong)")
            self.right_hand = 0

        print("")
        print("\n**LEFT HAND** (🦅 in pounds 🇺🇸):")
        try:
            ui_left_hand = input_timeout()
            self.left_hand = int(float(ui_left_hand) * 1e18)
            print(f"spud left hand: {self.left_hand}")
        except (TimeoutOccurred, ValueError):
            logger.info("No LEFT HAND strength reported.(ctrl+c to start over if wrong)")
            logger.info("Using 0 for LEFT HAND strength (or ctrl+c to start over)")
            self.left_hand = 0

        print("\nParticipant's X handle (username):")
        print("Leave this blank if you do NOT want to be tagged on X:")
        try:
            self.x_handle = input_timeout().strip().lower()
            if not self.x_handle:
                self.x_handle = "@eth_denver_tellor_fan_2025"
        except TimeoutOccurred:
            logger.info('Timeout occurred waiting for X username. (using default "@eth_denver_tellor_fan_2025")')
            self.x_handle = "@eth_denver_tellor_fan_2025"

        print("\n")
        print("Github username?")
        print("Leave this blank if you do NOT want share your github:")
        try:
            self.github_username = input_timeout().strip().lower()
            if not self.github_username:
                self.github_username = "tellor_dev"
        except TimeoutOccurred:
            print('Timeout occurred waiting for github username. (using default "tellor_dev")')
            self.github_username = "tellor_dev"

        print("\n")
        print("How many hours of sleep did you get last night?: ")
        try:
            self.hours_of_sleep = int(input_timeout())
        except (TimeoutOccurred, ValueError):
            print('Timeout or invalid input occurred waiting for hours of sleep.')
            print('Using default (6 hours of glorious slumber)')
            self.hours_of_sleep = 6

        print("\n")
        finish_message = "REPORTING THE FOLLOWING DATA TO TELLOR"
        print('\033[1m' + finish_message + '\033[0m')
        print(f"Right hand: {self.right_hand}")
        print(f"Left hand: {self.left_hand}")
        print(f"X Handle: {self.x_handle}")
        print(f"Github username: {self.github_username}")
        print(f"hours of Sleep: {self.hours_of_sleep}")
        print("Press [ENTER] to report the data shown above.")
        print("OR Use ctrl+c to start over.")
        try:
            _ = input_timeout()
            self.user_vals = (
                self.data_set,
                self.right_hand,
                self.left_hand,
                self.x_handle,
                self.github_username,
                self.hours_of_sleep,
            )
            return self.user_vals
        except TimeoutOccurred:
            logger.info("Timeout waiting for user to confirm.!")
            return None

    async def fetch_new_datapoint(self) -> OptionalDataPoint[str]:
        """Return the Participant's time stamped data report."""

        response = self.parse_user_vals()
        if response is None:
            print("backing out...")
            return None, datetime_now_utc()

        # Convert the response to a string representation
        response_str = str(response)
        # Create a tuple for the datapoint
        datapoint = (response_str, datetime_now_utc())
        print(f"spud's datapoint: {datapoint}")
        self.store_datapoint(datapoint)

        if response[3]:
            print(f"[bold]{response[3]} reported their grip strength! {response[1]}(RH), {response[2]}(LH)[/]")
        elif response[4]:
            print(f"[bold]{response[4]} reported their grip strength! {response[1]}(RH), {response[2]}(LH)[/]")
        else:
            print(f"[bold]You reported their grip strength! {response[1]}(RH), {response[2]}(LH)[/]")

        return datapoint


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        grip_score_source = gripDynoManualSource()
        response, timestamp = await grip_score_source.fetch_new_datapoint()
        print(response, timestamp)

    asyncio.run(main())
