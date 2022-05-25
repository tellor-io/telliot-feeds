# type: ignore
from typing import Optional, Any
from .event_scanner_state import EventScannerState
import json
import time
from web3.datastructures import AttributeDict
import logging

logger = logging.getLogger(__name__)


class JSONifiedState(EventScannerState):
    """Store the state of scanned blocks and all events.

    All state is an in-memory dict.
    Simple load/store massive JSON on start up.
    """

    def __init__(self):
        self.state = None
        self.fname = "last_block.json"
        # How many second ago we saved the JSON file
        self.last_save = 0

    def reset(self) -> None:
        """Create initial state of nothing scanned."""
        self.state = {
            "last_scanned_block": 0,
            "one_time_tips": 0,
            "continuous_feed_tips": 0
        }

    def one_time_tips_count(self) -> Optional[Any]:
        """One time tips count"""
        return self.state["one_time_tips"]

    def continuous_feed_count(self) -> Optional[Any]:
        """Continuous feed count"""
        return self.state["continuous_feed_tips"]

    def decrement_continuous_feed(self) -> Optional[Any]:
        """Subtract 1 from continuous feed event count"""
        self.state["continuous_feed_tips"] -= 1

    def decrement_one_time_tip(self) -> Optional[Any]:
        """Subtract from one time tip event count"""
        self.state["one_time_tips"] -= 1

    def increment_continuous_feed(self) -> Optional[Any]:
        """Subtract 1 from continuous feed event count"""
        self.state["continuous_feed_tips"] += 1

    def increment_one_time_tip(self) -> Optional[Any]:
        """Subtract from one time tip event count"""
        self.state["one_time_tips"] += 1

    def reset_continuous_feed_count(self) -> Optional[Any]:
        """Set continuous feed event count to 0"""
        self.state["continuous_feed_tips"] = 0

    def reset_one_time_tip_count(self) -> Optional[Any]:
        """Set one time tip event count to 0"""
        self.state["one_time_tips"] = 0

    def restore(self) -> None:
        """Restore the last scan state from a file."""
        try:
            self.state = json.load(open(self.fname, "rt"))
            print(f"Restored the state, previously {self.state['last_scanned_block']}\
                 blocks have been scanned")
        except (IOError, json.decoder.JSONDecodeError):
            print("State starting from scratch")
            self.reset()

    def save(self) -> None:
        """Save everything we have scanned so far in a file."""
        with open(self.fname, "wt") as f:
            json.dump(self.state, f)
        self.last_save = time.time()

    def get_last_scanned_block(self) -> int:
        """The number of the last block we have stored."""
        return self.state["last_scanned_block"]

    def get_one_time_tips(self) -> int:
        """The count of one time tips"""
        return self.state["one_time_tips"]

    def get_continuous_feed_tips(self) -> int:
        """The count continuous feed tips"""
        return self.state["continuous_feed_tips"]

    def delete_data(self, since_block):
        """Remove potentially reorganised blocks from the scan data."""
        pass

    def start_chunk(self, block_number, chunk_size):
        pass

    def end_chunk(self, block_number):
        """Save at the end of each block,
        so we can resume in the case of a crash or CTRL+C"""
        # Next time the scanner is started we will resume from this block
        self.state["last_scanned_block"] = block_number

        # Save the database file for every minute
        if time.time() - self.last_save > 60:
            self.save()

    def process_event(self, event: AttributeDict) -> str:
        log_index = event.logIndex  # Log index within the block
        txhash = event.transactionHash.hex()  # Transaction hash
        block_number = event.blockNumber
        print(event)
        if event.event == "TipAdded":
            self.increment_one_time_tip()
        elif event.event == "DataFeedFunded":
            self.increment_continuous_feed()

        # Return a pointer that allows us to look up this event later if needed
        return f"{block_number}-{txhash}-{log_index}"
