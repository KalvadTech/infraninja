"""InfraNinja - Infrastructure automation toolkit"""

__version__ = "1.0.0"

# Import actions as the main entry point
from infraninja.actions import (
    Action,
    Netdata,
    SSHHardening,
    SSHKeys,
    UpdateAndUpgrade,
)

__all__ = [
    "Action",
    "Netdata",
    "SSHHardening",
    "SSHKeys",
    "UpdateAndUpgrade",
]
