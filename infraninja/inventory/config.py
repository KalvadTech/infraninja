import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class NinjaConfig:
    """Configuration class for Infraninja."""

    inventory_endpoint: str = "/inventory/servers/"
    ssh_config_dir: Path = Path.home() / ".ssh/config.d"
    ssh_config_endpoint: str = "/ssh-tools/ssh-config/?bastionless=true"
    main_ssh_config: Path = Path.home() / ".ssh/config"
    default_ssh_config_filename: str = "bastionless_ssh_config"
    ssh_key_path: Path = Path.home() / ".ssh/id_rsa"
    api_url: Optional[str] = None
    api_key: Optional[str] = None

    @classmethod
    def from_env(cls) -> "NinjaConfig":
        """Create config from environment variables."""
        return cls(
            api_url=os.environ.get("JINN_API_URL"),
            api_key=os.environ.get("JINN_ACCESS_KEY"),
        )


default_config = NinjaConfig()
