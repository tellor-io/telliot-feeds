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
