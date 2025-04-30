import requests
import logging
from typing import Dict, List, Optional, Any


class CoolifyError(Exception):
    """Base exception for Coolify-related errors."""

    pass


class CoolifyAPIError(CoolifyError):
    """Exception raised for Coolify API-related errors."""

    pass


class CoolifyJinnSyncError(CoolifyError):
    """Exception raised for synchronization errors between Jinn and Coolify."""

    pass


class CoolifyManager:
    """
    A class to manage interactions between Jinn and Coolify server inventories.
    It fetches servers from Jinn and syncs them to Coolify.
    """

    def __init__(
        self,
        coolify_host: Optional[str] = None,
        coolify_api_token: Optional[str] = None,
        jinn_api_url: str = "https://jinn-api.kalvad.cloud",
        jinn_api_key: Optional[str] = None,
    ):
        """
        Initialize the CoolifyManager with API credentials.

        Args:
            coolify_host: The Coolify server hostname/IP with protocol and port
            coolify_api_token: Coolify API bearer token
            jinn_api_url: Jinn API URL
            jinn_api_key: Jinn API key
        """
        if (
            not coolify_host
            or not coolify_api_token
            or not jinn_api_url
            or not jinn_api_key
        ):
            raise ValueError(
                "All parameters (coolify_host, coolify_api_token, jinn_api_url, jinn_api_key) must be provided."
            )

        self.coolify_host = coolify_host.rstrip("/")
        self.coolify_api_token = coolify_api_token
        self.jinn_api_url = jinn_api_url.rstrip("/")
        self.jinn_api_key = jinn_api_key
        self.logger = logging.getLogger(__name__)

    def get_coolify_headers(self) -> Dict[str, str]:
        """Return the headers needed for Coolify API requests."""
        return {
            "Authorization": f"Bearer {self.coolify_api_token}",
            "Content-Type": "application/json",
        }

    def get_jinn_headers(self) -> Dict[str, str]:
        """Return the headers needed for Jinn API requests."""
        return {"Authentication": self.jinn_api_key}

    def get_coolify_security_keys(self) -> List[Dict[str, Any]]:
        """
        Fetch security keys from Coolify.

        Returns:
            List of security key dictionaries with UUID and other information.
        """
        endpoint = f"{self.coolify_host}/api/v1/security/keys"
        response = requests.get(
            endpoint, headers=self.get_coolify_headers(), timeout=30
        )

        if response.status_code != 200:
            self.logger.error(
                f"Failed to fetch Coolify security keys: {response.status_code} - {response.text}"
            )
            raise CoolifyAPIError(
                f"Failed to fetch Coolify security keys: {response.status_code}"
            )

        return response.json()

    def get_jinn_servers(self) -> List[Dict[str, Any]]:
        """
        Fetch all servers from Jinn inventory.

        Returns:
            List of server dictionaries with hostname, SSH info, and other details.
        """
        endpoint = f"{self.jinn_api_url}/inventory/servers/"
        response = requests.get(endpoint, headers=self.get_jinn_headers(), timeout=30)

        if response.status_code != 200:
            self.logger.error(
                f"Failed to fetch Jinn servers: {response.status_code} - {response.text}"
            )
            raise CoolifyAPIError(
                f"Failed to fetch Jinn servers: {response.status_code}"
            )

        return response.json().get("result", [])

    def add_server_to_coolify(
        self,
        name: str,
        ip: str,
        port: int,
        user: str,
        private_key_uuid: str,
        description: Optional[str] = None,
        is_build_server: bool = True,
        instant_validate: bool = True,
    ) -> Dict[str, Any]:
        """
        Add a server to Coolify.

        Args:
            name: Server name
            ip: Server IP address
            port: SSH port
            user: SSH user
            private_key_uuid: UUID of the private key in Coolify
            description: Optional server description
            is_build_server: Whether this is a build server
            instant_validate: Whether to validate the server immediately

        Returns:
            Server creation response from Coolify
        """
        endpoint = f"{self.coolify_host}/api/v1/servers"

        payload = {
            "name": name,
            "description": description,
            "ip": ip,
            "port": port,
            "user": user,
            "private_key_uuid": private_key_uuid,
            "is_build_server": is_build_server,
            "instant_validate": instant_validate,
        }

        response = requests.post(
            endpoint, headers=self.get_coolify_headers(), json=payload, timeout=30
        )

        if response.status_code not in [200, 201]:
            self.logger.error(
                f"Failed to add server to Coolify: {response.status_code} - {response.text}"
            )
            raise CoolifyAPIError(
                f"Failed to add server to Coolify: {response.status_code} - {response.text}"
            )

        return response.json()

    def sync_jinn_to_coolify(self, filter_active: bool = True) -> List[Dict[str, Any]]:
        """
        Sync servers from Jinn to Coolify.

        Args:
            filter_active: Only sync active servers from Jinn

        Returns:
            List of results from adding servers to Coolify
        """
        try:
            # Get the private key UUID from Coolify
            security_keys = self.get_coolify_security_keys()
            if not security_keys:
                raise CoolifyAPIError("No security keys found in Coolify")

            # Use the first key by default (or implement logic to choose the right key)
            private_key_uuid = security_keys[0].get("uuid")
            if not private_key_uuid:
                raise CoolifyAPIError("No valid UUID found in security keys")

            # Get servers from Jinn
            jinn_servers = self.get_jinn_servers()

            results = []
            for server in jinn_servers:
                # Skip inactive servers if filter_active is True
                if filter_active and not server.get("is_active", False):
                    self.logger.info(
                        f"Skipping inactive server: {server.get('hostname')}"
                    )
                    continue

                # Validate required fields
                hostname = server.get("hostname")
                ssh_hostname = server.get("ssh_hostname")
                ssh_user = server.get("ssh_user")

                if not hostname or not ssh_hostname or not ssh_user:
                    self.logger.error(f"Missing required fields for server: {server}")
                    results.append(
                        {
                            "jinn_server": server.get("hostname", "unknown"),
                            "error": "Missing required fields (hostname, ssh_hostname, ssh_user)",
                            "status": "failed",
                        }
                    )
                    continue

                try:
                    result = self.add_server_to_coolify(
                        name=hostname,
                        ip=ssh_hostname,
                        port=server.get("ssh_port", 22),
                        user=ssh_user,
                        private_key_uuid=private_key_uuid,
                        description=f"Imported from Jinn - {server.get('name')}",
                    )
                    results.append(
                        {
                            "jinn_server": hostname,
                            "coolify_result": result,
                            "status": "success",
                        }
                    )
                    self.logger.info(f"Successfully added server {hostname} to Coolify")
                except Exception as e:
                    results.append(
                        {"jinn_server": hostname, "error": str(e), "status": "failed"}
                    )
                    self.logger.error(
                        f"Failed to add server {hostname} to Coolify: {e}"
                    )

            return results
        except Exception as e:
            raise CoolifyJinnSyncError(
                f"Failed to sync Jinn servers to Coolify: {str(e)}"
            )
