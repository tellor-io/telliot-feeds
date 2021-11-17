"""Configuration class for AMPL plugin."""
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Optional
from typing import Union

from telliot_core.apps.config import ConfigFile
from telliot_core.apps.config import ConfigOptions
from telliot_core.model.base import Base


@dataclass
class AMPLConfigOptions(ConfigOptions):
    """Configurations needed for AMPL apis."""

    # Acces key for AnyBlock api
    anyblock_api_key: str = ""

    # Access key for BraveNewCoin / Rapid api
    rapid_api_key: str = ""


@dataclass
class AMPLConfig(Base):
    """Main AMPL plugin configuration object"""

    config_dir: Optional[Union[str, Path]] = None

    main: AMPLConfigOptions = field(default_factory=AMPLConfigOptions)

    def __post_init__(self) -> None:
        main_file = ConfigFile(
            name="ampl",
            config_type=AMPLConfigOptions,
            config_format="yaml",
            config_dir=self.config_dir,
        )
        self.main = main_file.get_config()


if __name__ == "__main__":
    _ = AMPLConfig()
