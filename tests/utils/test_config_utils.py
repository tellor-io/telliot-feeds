from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.utils.cfg import check_config


def test_check_config():
    """test checking configs and overwriting if desired"""

    cfg = TelliotConfig()

    check_config(cfg=cfg)
