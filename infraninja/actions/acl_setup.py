"""ACL setup action"""

from typing import Any

from pyinfra import host
from pyinfra.facts.server import OsRelease

from infraninja.actions.base import Action


class ACLSetup(Action):
    slug = "acl-setup"
    name = {"en": "ACL Setup", "fr": "Configuration des ACL"}
    tags = ["security", "acl", "permissions", "access-control"]
    category = "security"
    color = "#2980B9"
    logo = "fa-lock"
    description = {
        "en": "Set up Access Control Lists for fine-grained file permission management"
    }
    os_available = [
        "ubuntu",
        "debian",
        "alpine",
        "freebsd",
        "rhel",
        "centos",
        "fedora",
        "arch",
    ]

    def execute(self) -> Any:
        os_id = host.get_fact(OsRelease).get("id", "").lower()
        if os_id == "freebsd":
            from infraninja.security.freebsd.acl import acl_setup

            return acl_setup()
        else:
            from infraninja.security.common.acl import acl_setup

            return acl_setup()
