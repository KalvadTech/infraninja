"""
Redis Authentication Patch - Enables requirepass directive in redis.conf
"""

import secrets
import string

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.files import File, FindInFile
from pyinfra.operations import files, server


class RedisAuthPatch:
    """Enable Redis authentication by setting requirepass directive."""

    def __init__(self, redis_password=None):
        self.redis_password = redis_password or self._generate_password()

    def _generate_password(self):
        """Generate secure password."""
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(chars) for _ in range(24))

    @deploy("Redis Authentication Patch")
    def deploy(self):
        """Enable Redis authentication."""
        config_path = "/etc/redis/redis.conf"

        # Skip if config doesn't exist
        if not host.get_fact(File, path=config_path):
            host.noop(f"Redis config not found at {config_path}")
            return

        # Check if already configured
        if host.get_fact(FindInFile, path=config_path, pattern=r"^requirepass\s+.*$"):
            host.noop("Redis requirepass already configured")
            return

        # Check for commented requirepass
        commented = host.get_fact(
            FindInFile, path=config_path, pattern=r"^#\s*requirepass\s+.*$"
        )

        if commented:
            # Uncomment and set password
            files.replace(
                name="Enable requirepass",
                path=config_path,
                text=commented[0],
                replace=f"requirepass {self.redis_password}",
            )
        else:
            # Add requirepass line
            files.line(
                name="Add requirepass",
                path=config_path,
                line=f"requirepass {self.redis_password}",
                present=True,
            )

        # Restart Redis
        server.service(
            name="Restart Redis",
            service="redis-server",
            running=True,
            restarted=True,
            _ignore_errors=True,
        )
