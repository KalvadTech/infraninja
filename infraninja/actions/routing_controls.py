"""Routing controls action"""

from typing import Any

from infraninja.actions.base import Action


class RoutingControls(Action):
    slug = "routing-controls"
    name = {"en": "Routing Controls", "fr": "Contrôles de routage"}
    tags = ["security", "network", "routing", "hardening"]
    category = "security"
    color = "#34495E"
    logo = "fa-route"
    description = {
        "en": "Configure network routing controls to prevent IP spoofing and source routing attacks"
    }
    os_available = ["ubuntu", "debian"]

    def execute(self) -> Any:
        from infraninja.security.ubuntu.routing_controls import routing_controls

        return routing_controls()
