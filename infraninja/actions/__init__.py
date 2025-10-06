"""InfraNinja Actions - Entry point for infrastructure automation"""

from .base import Action
from .netdata import NetdataAction
from .ssh_hardening import SSHHardeningAction
from .ssh_keys import SSHKeysAction
from .update_and_upgrade import UpdateAndUpgradeAction

__all__ = [
    "Action",
    "NetdataAction",
    "SSHHardeningAction",
    "SSHKeysAction",
    "UpdateAndUpgradeAction",
]
