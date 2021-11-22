from logging import Logger

from telliot_core.utils.home import default_homedir

from telliot_feed_examples.utils.log import get_logger


def test_get_logger() -> None:
    """Tests instantiating a logger for the main package."""
    logger = get_logger(__name__)
    log_file = logger.handlers[0].baseFilename
    expected_log_file = default_homedir() / ("telliot-feed-examples.log")
    expected_log_file.resolve().absolute()

    assert isinstance(logger, Logger)
    assert log_file == str(expected_log_file)
    assert logger.name == __name__
