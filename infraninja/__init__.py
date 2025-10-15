"""InfraNinja - Infrastructure automation toolkit"""

__version__ = "1.0.0"

# Import actions as the main entry point
from infraninja.actions import (
    Action,
    NetdataAction,
    SSHKeysAction,
    UpdateAndUpgradeAction,
)

__all__ = [
    "Action",
    "NetdataAction",
    "SSHKeysAction",
    "UpdateAndUpgradeAction",
]
