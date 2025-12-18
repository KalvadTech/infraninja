"""Base Action class for InfraNinja"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Type


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

            class Netdata(Action):
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
            msg = f"{self.__class__.__name__} must define 'slug'"
            raise ValueError(msg)

        if not self.name or "en" not in self.name:
            msg = f"{self.__class__.__name__} must define 'name' with at least 'en' key"
            raise ValueError(msg)

        if not self.description or "en" not in self.description:
            msg = f"{self.__class__.__name__} must define 'description' with at least 'en' key"
            raise ValueError(msg)

        if not self.category:
            msg = f"{self.__class__.__name__} must define 'category'"
            raise ValueError(msg)

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


@dataclass
class ActionResult:
    """Result of an action execution."""

    action: str
    success: bool = True
    changed: bool = False
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompositeResult:
    """Result of a composite action execution."""

    success: bool = True
    results: List[ActionResult] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        """Returns True if any sub-action made changes."""
        return any(r.changed for r in self.results)

    def add(self, result: ActionResult) -> None:
        """Add a sub-action result."""
        self.results.append(result)
        if not result.success:
            self.success = False


class Composite(Action):
    """
    Base class for composite actions that execute multiple sub-actions.

    Composite actions group related actions together and execute them
    in sequence. They inherit all metadata capabilities from Action.

    Attributes:
        actions: List of Action classes to execute in order
        stop_on_failure: If True, stop execution when a sub-action fails

    Example:
        .. code:: python

            from infraninja.actions.base import Composite
            from infraninja.actions.update_and_upgrade import UpdateAndUpgrade
            from infraninja.actions.ssh_hardening import SSHHardening
            from infraninja.actions.netdata import Netdata

            class FullSetup(Composite):
                slug = "full-setup"
                name = {"en": "Full Server Setup"}
                description = {"en": "Complete server setup with updates, hardening, and monitoring"}
                category = "setup"

                actions = [
                    UpdateAndUpgrade,
                    SSHHardening,
                    Netdata,
                ]

            # Execute all sub-actions
            setup = FullSetup()
            result = setup.execute()

            # Pass specific params to sub-actions
            result = setup.execute(
                SSHHardening={"permit_root_login": "no"},
                Netdata={"claim_token": "xxx"},
            )
    """

    actions: List[Type[Action]] = []
    stop_on_failure: bool = True

    def __init__(self, **kwargs):
        """
        Initialize the composite action.

        Args:
            **kwargs: Parameters passed to parent Action
        """
        # Auto-compute os_available as intersection of all sub-actions
        if not self.os_available and self.actions:
            self._compute_os_available()

        super().__init__(**kwargs)

    def _compute_os_available(self) -> None:
        """Compute supported OS as intersection of all sub-actions."""
        if not self.actions:
            return

        # Start with first action's OS list
        os_set = set(self.actions[0].os_available)

        # Intersect with remaining actions
        for action_class in self.actions[1:]:
            os_set &= set(action_class.os_available)

        self.os_available = sorted(os_set)

    def execute(self, **kwargs) -> CompositeResult:
        """
        Execute all sub-actions in sequence.

        Args:
            **kwargs: Dict of {ActionClassName: {param: value}} for sub-action params

        Returns:
            CompositeResult with results from all sub-actions
        """
        result = CompositeResult()

        for action_class in self.actions:
            action_name = action_class.__name__

            # Get params for this specific action
            action_params = kwargs.get(action_name, {})

            # Instantiate and execute
            action = action_class(**action_params)

            try:
                action_result = action.execute()
                result.add(
                    ActionResult(
                        action=action_name,
                        success=True,
                        changed=bool(action_result),
                        data={"result": action_result},
                    )
                )
            except Exception as e:
                result.add(
                    ActionResult(
                        action=action_name,
                        success=False,
                        message=str(e),
                    )
                )
                if self.stop_on_failure:
                    break

        return result

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata including sub-actions info."""
        metadata = super().get_metadata()
        metadata["actions"] = [a.__name__ for a in self.actions]
        metadata["is_composite"] = True
        return metadata
