# inventory || coolify.py

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import requests
from requests.exceptions import RequestException

sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


class CoolifyError(Exception):
    """Base exception for Coolify-related errors."""

    pass


class CoolifyAPIError(CoolifyError):
    """Exception raised for API-related errors."""

    pass


class CoolifySSHError(CoolifyError):
    """Exception raised for SSH-related errors."""

    pass


class Coolify:
    def __init__(
        self,
        ssh_key_path: Optional[Union[str, Path]] = None,
        api_url: str = "https://coolify.example.com/api",
        api_key: Optional[str] = None,
        tags: Optional[List[str]] = None,
        ssh_config_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        """Initialize the Coolify class with configuration.

        Args:
            ssh_key_path: Path to SSH key file. If None, uses ~/.ssh/id_rsa
            api_url: Base URL for the Coolify API
            api_key: API key for authentication
            tags: Server tags to filter by
            ssh_config_dir: Directory for SSH config files. If None, uses ~/.ssh/config.d

        Raises:
            CoolifySSHError: If SSH key path does not exist
            CoolifyAPIError: If API key is not set
        """
        # Set SSH configuration
        self.ssh_config_dir: Path = (
            Path(ssh_config_dir).expanduser()
            if ssh_config_dir
            else Path.home() / ".ssh/config.d"
        )
        self.main_ssh_config: Path = Path.home() / ".ssh/config"
        self.ssh_key_path: Path = (
            Path(ssh_key_path).expanduser()
            if ssh_key_path
            else Path.home() / ".ssh/id_rsa"
        )

        # Create SSH config directory if it doesn't exist
        self.ssh_config_dir.mkdir(parents=True, exist_ok=True)

        if not self.ssh_key_path.exists():
            raise CoolifySSHError(f"SSH key path does not exist: {self.ssh_key_path}")

        # Set API configuration
        self.api_url: str = api_url.rstrip("/")
        self.api_key: Optional[str] = api_key
        if not self.api_key:
            raise CoolifyAPIError("API key is not set")

        # Set filtering options
        self.tags: Optional[List[str]] = tags
        self.servers: List[Tuple[str, Dict[str, Any]]] = []

        # Load initial configuration
        self.load_servers()

    def _make_api_request(
        self, endpoint: str, method: str = "GET", data: Optional[Dict] = None
    ) -> Dict:
        """Make a request to the Coolify API.

        Args:
            endpoint: API endpoint to request
            method: HTTP method to use
            data: Request data for POST requests

        Returns:
            Dict: JSON response from the API

        Raises:
            CoolifyAPIError: If the API request fails
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            url = f"{self.api_url}/{endpoint.lstrip('/')}"
            logger.info(f"Making API request to: {url}")

            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            else:
                raise CoolifyAPIError(f"Unsupported HTTP method: {method}")

            # Log response status
            logger.info(f"API response status: {response.status_code}")

            # If response is not successful, log and raise an error
            if response.status_code >= 400:
                logger.error(
                    f"API request failed with status {response.status_code}: {response.text}"
                )
                response.raise_for_status()

            # Try to parse JSON response
            try:
                return response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse response as JSON: {e}")
                logger.error(
                    f"Response text: {response.text[:1000]}..."
                )  # Log first 1000 chars
                raise CoolifyAPIError(f"Failed to parse API response: {str(e)}")

        except RequestException as e:
            logger.error(f"Request exception: {str(e)}")
            raise CoolifyAPIError(f"API request failed: {str(e)}")
        except Exception as e:
            logger.exception(f"Unexpected error in API request: {str(e)}")
            raise CoolifyAPIError(f"API request failed: {str(e)}")

    def _filter_server(self, server: Dict[str, Any]) -> bool:
        """Filter a server based on tags or other criteria.

        Args:
            server: Server data dictionary from Coolify API

        Returns:
            bool: True if server matches filters, False otherwise
        """
        # If no tags are specified, include all servers
        if not self.tags:
            return True

        # For now, assume Coolify doesn't have tags in the same format
        # Instead, we'll use the name field for basic matching
        server_name = server.get("name", "").lower()

        # Check if any tag is in the server name
        return any(tag.lower() in server_name for tag in self.tags)

    def load_servers(self, timeout: int = 30) -> None:
        """Fetch servers from the Coolify API.

        Args:
            timeout: Request timeout in seconds

        Raises:
            CoolifyAPIError: If the API request fails or no servers are found
        """
        try:
            # Get list of servers from Coolify
            response = self._make_api_request("api/v1/servers")

            # The response might be a dict or a list, handle both cases
            servers = (
                response if isinstance(response, list) else response.get("data", [])
            )

            filtered_servers = []
            for server in servers:
                if self._filter_server(server):
                    filtered_servers.append(server)

            if not filtered_servers:
                logger.warning("No servers found matching the specified criteria")
                self.servers = []
                return

            self.servers = self.format_host_list(filtered_servers)

        except CoolifyAPIError as e:
            logger.error(f"Failed to load servers: {str(e)}")
            raise
        except Exception as e:
            raise CoolifyAPIError(f"An unexpected error occurred: {str(e)}")

    def format_host_list(
        self, filtered_servers: List[Dict[str, Any]]
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """Format a list of servers into the expected host list format.

        Args:
            filtered_servers: List of server dictionaries

        Returns:
            List of (hostname, attributes) tuples
        """
        result = []
        for server in filtered_servers:
            server_name = server.get("name", "")
            ip_address = server.get("ip")
            settings = server.get("settings", {})

            # Skip servers that are not reachable or usable
            if settings:
                is_reachable = settings.get("is_reachable", False)
                is_usable = settings.get("is_usable", False)
                if not is_reachable or not is_usable:
                    logger.warning(
                        f"Skipping server {server_name} as it is not reachable or usable"
                    )
                    continue
            
            # Skip localhost entries
            if server_name.lower() == "localhost" or \
               ip_address == "127.0.0.1" or \
               ip_address == "::1":
                continue

            # Create server entry for PyInfra
            result.append(
                (
                    server_name,
                    {
                        "hostname": ip_address,
                        "ssh_user": server.get("user", "root"),
                        "ssh_port": server.get("port", 22),
                        "ssh_key": str(self.ssh_key_path),
                        "is_active": True,
                        "uuid": server.get("uuid", ""),
                        "server_id": server.get("id", ""),
                        "description": server.get("description", ""),
                    },
                )
            )
        return result

    def get_servers(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Get the list of servers.

        Returns:
            List[Tuple[str, Dict[str, Any]]]: List of (hostname, attributes) tuples
        """
        return self.servers

    def get_server_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get server details by name.

        Args:
            name: Server name to look up

        Returns:
            Optional[Dict[str, Any]]: Server details if found, None otherwise
        """
        for server_name, attributes in self.servers:
            if server_name == name:
                return attributes
        return None

    def get_servers_by_tag(self, tag: str) -> List[Tuple[str, Dict[str, Any]]]:
        """Get all servers with a specific tag.

        Args:
            tag: Tag to filter by

        Returns:
            List[Tuple[str, Dict[str, Any]]]: List of (hostname, attributes) tuples
        """
        original_tags = self.tags
        self.tags = [tag]
        try:
            self.load_servers()
            return self.servers
        finally:
            self.tags = original_tags
