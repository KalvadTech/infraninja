"""InfraNinja - Infrastructure automation toolkit"""

__version__ = "1.0.0"

# Import actions as the main entry point
from infraninja.actions import (
    Action,
    ActionResult,
    Composite,
    CompositeResult,
    FullSetup,
    Netdata,
    SSHHardening,
    SSHKeys,
    UpdateAndUpgrade,
)

# Import facts for read-only server information gathering
from infraninja.facts import (
    CompositeFact,
    CompositeFactResult,
    Fact,
    FactResult,
    FullFacts,
    Hardware,
    SystemInfo,
)

__all__ = [
    "Action",
    "ActionResult",
    "Composite",
    "CompositeResult",
    "CompositeFact",
    "CompositeFactResult",
    "Fact",
    "FactResult",
    "FullFacts",
    "FullSetup",
    "Hardware",
    "Netdata",
    "SSHHardening",
    "SSHKeys",
    "SystemInfo",
    "UpdateAndUpgrade",
]
