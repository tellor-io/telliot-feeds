"""Configuration class for Nomics plugin."""
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Optional
from typing import Union

from telliot_core.apps.config import ConfigFile
from telliot_core.apps.config import ConfigOptions
from telliot_core.model.base import Base


@dataclass
class NOMICSConfigOptions(ConfigOptions):
    """Configurations needed for Nomics api."""

    # Access key for Nomics api
    nomics_api_key: str = ""


@dataclass
class NomicsConfig(Base):
    """Main Nomics plugin configuration object"""

    config_dir: Optional[Union[str, Path]] = None

    main: NOMICSConfigOptions = field(default_factory=NOMICSConfigOptions)

    def __post_init__(self) -> None:
        main_file = ConfigFile(
            name="nomics",
            config_type=NOMICSConfigOptions,
            config_format="yaml",
            config_dir=self.config_dir,
        )
        self.main = main_file.get_config()


if __name__ == "__main__":
    _ = NomicsConfig()
