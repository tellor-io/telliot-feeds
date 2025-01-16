from dataclasses import dataclass
from typing import Any
from typing import Optional

from rich import print

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.queries.grip_dyno_challenge_query import GripDynoReturnType
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

    data_set: Optional[bool] = True
    right_hand: Optional[float] = None
    left_hand: Optional[float] = None
    x_handle: Optional[str] = None
    github_username: Optional[str] = None
    hours_of_sleep: Optional[float] = None

    # user_vals = [data_set, right_hand, left_hand, x_handle, github_username, hours_of_sleep]

    def parse_user_vals(self) -> Optional[Any]:
        """Parse user input and return list of the participant's data."""
        print("[bold]So you've Completed the grip challenge??? [/]")
        print("[bold blue]🤜 REPORT YOUR GRIP STRENGTH RESULT TO THE TELLOR ORACLE 🤛[/]\n")
        print("[bold blue]Data is written to tellor Oracle on Base Sepolia chain![/]")
        print('Press Enter to get started. (enter "w" for womens data set) [M/w]')
        try:
            start_selection = input_timeout().strip().lower()
            if start_selection in ("w", "women", "womens", "women's"):
                self.data_set = False
            elif start_selection in ("", "m", "men", "mens", "men's"):
                self.data_set = True
            else:
                print("Invalid input. Defaulting to men's dataset (0)")
                self.data_set = True
        except TimeoutOccurred:
            logger.info("Input timeout. Defaulting to men's dataset (0)")
            self.data_set = True

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
            print("Timeout or invalid input occurred waiting for hours of sleep.")
            print("Using default (6 hours of glorious slumber)")
            self.hours_of_sleep = 6

        print("\n")
        print("[bold blue]REPORTING THE FOLLOWING DATA TO TELLOR[/]")
        print(f"[bold blue]Right hand: {self.right_hand}")
        print(f"[bold blue]Left hand: {self.left_hand}")
        print(f"[bold blue]X Handle: {self.x_handle}")
        print(f"[bold blue]Github username: {self.github_username}")
        print(f"[bold blue]Hours of Sleep: {self.hours_of_sleep}")
        print("[bold red]Press [ENTER] to report the data shown above.")
        print("[blue]OR Use ctrl+c to start over...")
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

    async def fetch_new_datapoint(self) -> OptionalDataPoint[GripDynoReturnType]:
        """Return the Participant's time stamped data report."""

        response = self.parse_user_vals()
        if response is None:
            print("backing out...")
            return None, datetime_now_utc()

        # Create a tuple for the datapoint
        datapoint = (response, datetime_now_utc())
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
