"""InfraNinja Actions - Entry point for infrastructure automation"""

from .base import Action
from .netdata import Netdata
from .ssh_hardening import SSHHardening
from .ssh_keys import SSHKeys
from .update_and_upgrade import UpdateAndUpgrade

__all__ = [
    "Action",
    "Netdata",
    "SSHHardening",
    "SSHKeys",
    "UpdateAndUpgrade",
]
