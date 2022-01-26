import logging
import os
from pathlib import Path

from telliot_core.logs import init_logging
from telliot_core.utils.home import default_homedir

from telliot_feed_examples.utils.log import default_logsdir
from telliot_feed_examples.utils.log import get_logger


def test_default_logsdir() -> None:
    """Tests creating default logs directory."""
    ld = default_homedir()
    assert isinstance(ld, Path)
    assert ld.exists()


def test_recurring_messages() -> None:
    """Ensure logger filters out recurring messages"""
    logger = get_logger("telliot_feed_examples")
    init_logging(logging.INFO)
    expected_log_file = default_logsdir() / ("telliot.log")
    expected_log_file.resolve().absolute()
    num_lines_before = 0
    with open(os.path.join(expected_log_file), "r") as f:
        for _ in f:
            num_lines_before += 1

    for _ in range(5):
        logger.info("testttt")

    num_lines_after = 0
    with open(os.path.join(expected_log_file), "r") as f:
        for _ in f:
            num_lines_after += 1

    assert num_lines_after - num_lines_before == 1
