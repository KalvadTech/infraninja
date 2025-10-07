"""Base Action class for InfraNinja"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class Action(ABC):
    """
    Base class for all InfraNinja actions.

    Actions are the main entry point for infrastructure automation tasks.
    Each action represents a deployable unit with metadata for UI/CLI presentation.

    Attributes:
        slug: Unique identifier for the action (e.g., 'deploy-netdata')
        name: Action name in multiple languages {'en': 'Deploy Netdata', 'ar': '...'}
        tags: List of tags for categorization and filtering
        category: Action category (e.g., 'monitoring', 'security', 'deployment')
        color: Color code for UI display (hex color)
        logo: Font Awesome icon name (e.g., 'fa-server', 'fa-shield')
        description: Action description in multiple languages
        os_available: List of supported operating systems

    Example:
        .. code:: python

            class NetdataAction(Action):
                slug = "deploy-netdata"
                name = {"en": "Deploy Netdata", "ar": "نشر Netdata"}
                tags = ["monitoring", "observability"]
                category = "monitoring"
                color = "#00AB44"
                logo = "fa-chart-line"
                description = {
                    "en": "Deploy Netdata real-time monitoring",
                    "ar": "نشر مراقبة Netdata في الوقت الفعلي"
                }
                os_available = ["ubuntu", "debian", "alpine", "freebsd", "rhel", "centos"]

                def execute(self, **kwargs):
                    # Implementation
                    pass
    """

    # Required class attributes to be overridden by subclasses
    slug: str = ""
    name: Dict[str, str] = {}
    tags: List[str] = []
    category: str = ""
    color: str = "#000000"
    logo: str = "fa-cog"
    description: Dict[str, str] = {}
    os_available: List[
        str
    ] = []  # List of supported OS (e.g., ["ubuntu", "debian", "alpine", "freebsd"])

    def __init__(self, **kwargs):
        """
        Initialize the action with optional parameters.

        Args:
            **kwargs: Additional parameters to pass to the action
        """
        self.params = kwargs
        self._validate_metadata()

    def _validate_metadata(self) -> None:
        """
        Validate that all required metadata is provided.

        Raises:
            ValueError: If required metadata is missing or invalid
        """
        if not self.slug:
            raise ValueError(f"{self.__class__.__name__} must define 'slug'")

        if not self.name or "en" not in self.name:
            raise ValueError(
                f"{self.__class__.__name__} must define 'name' with at least 'en' key"
            )

        if not self.description or "en" not in self.description:
            raise ValueError(
                f"{self.__class__.__name__} must define 'description' with at least 'en' key"
            )

        if not self.category:
            raise ValueError(f"{self.__class__.__name__} must define 'category'")

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Execute the action.

        This method must be implemented by all action subclasses.

        Args:
            **kwargs: Action-specific parameters

        Returns:
            Any: Action execution result
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get action metadata.

        Returns:
            Dict containing all action metadata
        """
        return {
            "slug": self.slug,
            "name": self.name,
            "tags": self.tags,
            "category": self.category,
            "color": self.color,
            "logo": self.logo,
            "description": self.description,
            "os_available": self.os_available,
        }

    def get_name(self, language: str = "en") -> str:
        """
        Get action name in specified language.

        Args:
            language: Language code (defaults to 'en')

        Returns:
            Action name in requested language, falls back to 'en'
        """
        return self.name.get(language, self.name.get("en", ""))

    def get_description(self, language: str = "en") -> str:
        """
        Get action description in specified language.

        Args:
            language: Language code (defaults to 'en')

        Returns:
            Action description in requested language, falls back to 'en'
        """
        return self.description.get(language, self.description.get("en", ""))

    def __repr__(self) -> str:
        """String representation of the action."""
        return (
            f"<{self.__class__.__name__} slug='{self.slug}' category='{self.category}'>"
        )

    def __str__(self) -> str:
        """User-friendly string representation."""
        return f"{self.get_name()} ({self.slug})"
