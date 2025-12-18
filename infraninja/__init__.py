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

__all__ = [
    "Action",
    "ActionResult",
    "Composite",
    "CompositeResult",
    "FullSetup",
    "Netdata",
    "SSHHardening",
    "SSHKeys",
    "UpdateAndUpgrade",
]
