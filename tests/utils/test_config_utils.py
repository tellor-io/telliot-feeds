from tabnanny import check
from telliot_feeds.utils.cfg import check_config
from telliot_core.apps.telliot_config import TelliotConfig


def test_check_config():
    """test checking configs and overwriting if desired"""

    cfg = TelliotConfig()

    check_config(cfg=cfg)