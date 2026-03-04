"""InfraNinja Inventories - Server inventory management"""

from .base import Inventory
from .coolify import Coolify
from .jinn import Jinn

__all__ = [
    "Inventory",
    "Coolify",
    "Jinn",
]
