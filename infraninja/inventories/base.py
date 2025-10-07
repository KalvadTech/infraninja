"""Base Inventory class for InfraNinja"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


class Inventory(ABC):
    """
    Base class for all InfraNinja inventories.

    Inventories are responsible for fetching and managing server infrastructure
    from various sources (APIs, cloud providers, etc.) and making them available
    for deployment operations.

    Attributes:
        slug: Unique identifier for the inventory (e.g., 'jinn', 'coolify')
        name: Inventory name in multiple languages {'en': 'Jinn Inventory', 'ar': '...'}
        description: Inventory description in multiple languages
        servers: List of (hostname, attributes) tuples representing managed servers

    Example:
        .. code:: python

            class JinnInventory(Inventory):
                slug = "jinn"
                name = {"en": "Jinn Inventory", "ar": "مخزون جن"}
                description = {
                    "en": "Fetch servers from Jinn API",
                    "ar": "جلب الخوادم من واجهة برمجة تطبيقات جن"
                }

                def __init__(self, api_key: str, **kwargs):
                    super().__init__(**kwargs)
                    self.api_key = api_key

                def load_servers(self):
                    # Implementation to fetch servers
                    pass

                def get_servers(self):
                    return self.servers
    """

    # Required class attributes to be overridden by subclasses
    slug: str = ""
    name: Dict[str, str] = {}
    description: Dict[str, str] = {}

    def __init__(
        self,
        ssh_key_path: Optional[Union[str, Path]] = None,
        ssh_config_dir: Optional[Union[str, Path]] = None,
        **kwargs,
    ):
        """
        Initialize the inventory with common SSH configuration.

        Args:
            ssh_key_path: Path to SSH key file. If None, uses ~/.ssh/id_rsa
            ssh_config_dir: Directory for SSH config files. If None, uses ~/.ssh/config.d
            **kwargs: Additional parameters to pass to the inventory
        """
        self.ssh_config_dir: Path = (
            Path(ssh_config_dir).expanduser()
            if ssh_config_dir
            else Path.home() / ".ssh/config.d"
        )
        self.main_ssh_config: Path = Path.home() / ".ssh/config"
        self.ssh_key_path: Path = (
            Path(ssh_key_path).expanduser()
            if ssh_key_path
            else Path.home() / ".ssh/id_rsa"
        )

        # Create SSH config directory if it doesn't exist
        self.ssh_config_dir.mkdir(parents=True, exist_ok=True)

        # Initialize servers list
        self.servers: List[Tuple[str, Dict[str, Any]]] = []

        # Store additional parameters
        self.params = kwargs

        # Validate metadata
        self._validate_metadata()

    def _validate_metadata(self) -> None:
        """
        Validate that all required metadata is provided.

        Raises:
            ValueError: If required metadata is missing or invalid
        """
        if not self.slug:
            msg = f"{self.__class__.__name__} must define 'slug'"
            raise ValueError(msg)

        if not self.name or "en" not in self.name:
            msg = f"{self.__class__.__name__} must define 'name' with at least 'en' key"
            raise ValueError(
                msg
            )

        if not self.description or "en" not in self.description:
            msg = f"{self.__class__.__name__} must define 'description' with at least 'en' key"
            raise ValueError(
                msg
            )

    @abstractmethod
    def load_servers(self, **kwargs) -> None:
        """
        Load servers from the inventory source.

        This method must be implemented by all inventory subclasses.
        It should populate the self.servers list with server information.

        Args:
            **kwargs: Inventory-specific parameters
        """
        pass

    @abstractmethod
    def get_servers(self) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Get the list of servers.

        Returns:
            List[Tuple[str, Dict[str, Any]]]: List of (hostname, attributes) tuples
        """
        pass

    def refresh_ssh_config(self) -> None:
        """
        Generate and save SSH configuration.

        This method can be overridden by subclasses to provide custom SSH config
        generation logic.
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get inventory metadata.

        Returns:
            Dict containing all inventory metadata
        """
        return {
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
        }

    def get_name(self, language: str = "en") -> str:
        """
        Get inventory name in specified language.

        Args:
            language: Language code (defaults to 'en')

        Returns:
            Inventory name in requested language, falls back to 'en'
        """
        return self.name.get(language, self.name.get("en", ""))

    def get_description(self, language: str = "en") -> str:
        """
        Get inventory description in specified language.

        Args:
            language: Language code (defaults to 'en')

        Returns:
            Inventory description in requested language, falls back to 'en'
        """
        return self.description.get(language, self.description.get("en", ""))

    def __repr__(self) -> str:
        """String representation of the inventory."""
        return f"<{self.__class__.__name__} slug='{self.slug}' servers={len(self.servers)}>"

    def __str__(self) -> str:
        """User-friendly string representation."""
        return f"{self.get_name()} ({self.slug})"
