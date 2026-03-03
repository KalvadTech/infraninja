"""Base Fact class for InfraNinja"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Type


class Fact(ABC):
    """
    Base class for all InfraNinja facts.

    Facts gather read-only information from servers (OS, hardware, etc.).
    Each fact represents a data-gathering unit with metadata for UI/CLI presentation.

    Attributes:
        slug: Unique identifier for the fact (e.g., 'system-info')
        name: Fact name in multiple languages {'en': 'System Info', 'ar': '...'}
        tags: List of tags for categorization and filtering
        category: Fact category (e.g., 'system', 'hardware')
        color: Color code for UI display (hex color)
        logo: Font Awesome icon name (e.g., 'fa-info-circle')
        description: Fact description in multiple languages
        os_available: List of supported operating systems
    """

    slug: str = ""
    name: Dict[str, str] = {}
    tags: List[str] = []
    category: str = ""
    color: str = "#000000"
    logo: str = "fa-cog"
    description: Dict[str, str] = {}
    os_available: List[str] = []

    def __init__(self, **kwargs):
        self.params = kwargs
        self._validate_metadata()

    def _validate_metadata(self) -> None:
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
    def execute(self, **kwargs) -> "FactResult":
        """
        Gather fact data from the server.

        Returns:
            FactResult with gathered data
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
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
        return self.name.get(language, self.name.get("en", ""))

    def get_description(self, language: str = "en") -> str:
        return self.description.get(language, self.description.get("en", ""))

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} slug='{self.slug}' category='{self.category}'>"
        )

    def __str__(self) -> str:
        return f"{self.get_name()} ({self.slug})"


@dataclass
class FactResult:
    """Result of a fact gathering operation."""

    fact: str
    success: bool = True
    data: Dict[str, Any] = field(default_factory=dict)
    message: str = ""


@dataclass
class CompositeFactResult:
    """Result of a composite fact gathering operation."""

    success: bool = True
    results: List[FactResult] = field(default_factory=list)

    @property
    def data(self) -> Dict[str, Any]:
        """Merge all sub-fact result data into a single dict."""
        merged = {}
        for r in self.results:
            merged.update(r.data)
        return merged

    def add(self, result: FactResult) -> None:
        self.results.append(result)
        if not result.success:
            self.success = False


class CompositeFact(Fact):
    """
    Base class for composite facts that gather multiple sub-facts.

    Composite facts group related facts together and execute them
    in sequence, merging results.

    Attributes:
        facts: List of Fact classes to gather in order
        stop_on_failure: If True, stop execution when a sub-fact fails
    """

    facts: List[Type[Fact]] = []
    stop_on_failure: bool = True

    def __init__(self, **kwargs):
        if not self.os_available and self.facts:
            self._compute_os_available()
        super().__init__(**kwargs)

    def _compute_os_available(self) -> None:
        if not self.facts:
            return
        os_set = set(self.facts[0].os_available)
        for fact_class in self.facts[1:]:
            os_set &= set(fact_class.os_available)
        self.os_available = sorted(os_set)

    def execute(self, **kwargs) -> CompositeFactResult:
        """
        Execute all sub-facts in sequence.

        Args:
            **kwargs: Dict of {FactClassName: {param: value}} for sub-fact params

        Returns:
            CompositeFactResult with results from all sub-facts
        """
        result = CompositeFactResult()

        for fact_class in self.facts:
            fact_name = fact_class.__name__
            fact_params = kwargs.get(fact_name, {})
            fact = fact_class(**fact_params)

            try:
                fact_result = fact.execute()
                result.add(fact_result)
            except Exception as e:
                result.add(
                    FactResult(
                        fact=fact_name,
                        success=False,
                        message=str(e),
                    )
                )
                if self.stop_on_failure:
                    break

        return result

    def get_metadata(self) -> Dict[str, Any]:
        metadata = super().get_metadata()
        metadata["facts"] = [f.__name__ for f in self.facts]
        metadata["is_composite"] = True
        return metadata
