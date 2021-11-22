import logging
import sys

from telliot_core.utils.home import default_homedir


def get_logger(name: str) -> logging.Logger:
    """Telliot feed examples logger

    Returns a logger that logs to stdout and file. The name arg
    should be the current file name. For example:
    _ = get_logger(name=__name__)
    """
    logger = logging.getLogger(name)

    logger.setLevel(level=logging.INFO)

    logs_file = default_homedir() / ("telliot-feed-examples.log")
    logs_file = logs_file.resolve().absolute()

    output_file_handler = logging.FileHandler(logs_file)
    stdout_handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    output_file_handler.setFormatter(formatter)
    stdout_handler.setFormatter(formatter)

    logger.addHandler(output_file_handler)
    logger.addHandler(stdout_handler)

    return logger
