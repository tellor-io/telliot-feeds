import os
from logging import Logger
from pathlib import Path

from telliot_core.utils.home import default_homedir

from telliot_feed_examples.utils.log import default_logsdir
from telliot_feed_examples.utils.log import get_logger


def test_default_logsdir() -> None:
    """Tests creating default logs directory."""
    ld = default_homedir()
    assert isinstance(ld, Path)
    assert ld.exists()


def test_get_logger() -> None:
    """Tests instantiating a logger for the main package."""
    logger = get_logger(__name__)
    log_file = logger.handlers[0].baseFilename
    expected_log_file = default_logsdir() / ("telliot-feed-examples.log")
    expected_log_file.resolve().absolute()

    assert isinstance(logger, Logger)
    assert log_file == str(expected_log_file)
    assert logger.name == __name__


def test_reocurring_messages() -> None:
    """Ensure logger filters out recocurring messages"""
    logger = get_logger(__name__)
    expected_log_file = default_logsdir() / ("telliot-feed-examples.log")
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

    assert num_lines_after - num_lines_before == 2
