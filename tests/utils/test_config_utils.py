from itertools import chain
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.utils.cfg import setup_config


def test_check_config():
    """test checking configs and overwriting if desired"""

    cfg = TelliotConfig()

    setup_config(cfg=cfg)
