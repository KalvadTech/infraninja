"""InfraNinja Actions - Entry point for infrastructure automation"""

from .base import Action, ActionResult, Composite, CompositeResult
from .full_setup import FullSetup
from .netdata import Netdata
from .ssh_hardening import SSHHardening
from .ssh_keys import SSHKeys
from .update_and_upgrade import UpdateAndUpgrade

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
