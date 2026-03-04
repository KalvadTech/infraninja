"""Redis authentication patch action"""

from typing import Any, Optional

from infraninja.actions.base import Action


class RedisAuthPatch(Action):
    slug = "redis-auth-patch"
    name = {"en": "Redis Auth Patch", "fr": "Patch d'authentification Redis"}
    tags = ["security", "redis", "authentication", "patch"]
    category = "security"
    color = "#D63031"
    logo = "fa-database"
    description = {
        "en": "Enable Redis authentication by setting the requirepass directive"
    }
    os_available = [
        "ubuntu",
        "debian",
        "alpine",
        "rhel",
        "centos",
        "fedora",
        "arch",
    ]

    def __init__(self, redis_password: Optional[str] = None):
        self.redis_password = redis_password
        super().__init__()

    def execute(self) -> Any:
        from infraninja.security.patches.redis_auth_patch import (
            RedisAuthPatch as _RedisAuthPatchImpl,
        )

        patch = _RedisAuthPatchImpl(redis_password=self.redis_password)
        return patch.deploy()
