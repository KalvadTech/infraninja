# inventory || jinn.py

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import requests

sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


class Jinn:
    def __init__(
        self,
        ssh_key_path: Optional[str] = None,
        api_url: str = "https://jinn-api.kalvad.cloud",
        api_key: Optional[str] = None,
        groups: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        use_bastion: bool = False,
    ):
        """Initialize the Jinn class with configuration.

        Args:
            ssh_key_path: Path to SSH key file. If None, uses ~/.ssh/id_rsa
            api_url: Base URL for the Jinn API
            api_key: API key for authentication
            groups: Server groups to filter by
            tags: Server tags to filter by
            use_bastion: Whether to use bastion host
        """
        self.ssh_config_dir: Path = Path.home() / ".ssh/config.d"
        self.main_ssh_config: Path = Path.home() / ".ssh/config"

        # Set SSH key path
        self.ssh_key_path: Path = (
            Path(ssh_key_path) if ssh_key_path else Path.home() / ".ssh/id_rsa"
        )

        if not self.ssh_key_path.exists():
            logger.error("SSH key path does not exist: %s", self.ssh_key_path)
            sys.exit(1)

        # Set API configuration
        self.api_url: str = api_url.rstrip("/")
        self.api_key: Optional[str] = api_key
        if not self.api_key:
            logger.error("API key is not set")
            sys.exit(1)

        # Set filtering options
        self.groups: str = groups
        self.tags: Optional[str] = tags
        self.use_bastion: bool = use_bastion
        self.project_name: Optional[str] = None
        # Set SSH config endpoint based on bastion usage
        if self.use_bastion:
            self.ssh_config_endpoint: str = "/ssh-tools/ssh-config/"
        else:
            self.ssh_config_endpoint: str = "/ssh-tools/ssh-config/?bastionless=true"

    def _str_to_bool(self, value: Optional[str]) -> bool:
        """Convert string value to boolean.

        Args:
            value: String value to convert

        Returns:
            True if value is 'True', 'true', or 't', False otherwise
        """
        if not value:
            return False
        return value.lower() in ("true", "t")

    def get_groups_from_data(self, data: Dict[str, Any]) -> List[str]:
        """Extract unique groups from server data.

        Args:
            data: Dictionary containing server data from API

        Returns:
            List of unique group names sorted alphabetically
        """
        groups: Set[str] = set()

        for server in data.get("result", []):
            group = server.get("group", {}).get("name_en")
            if group:
                groups.add(group)
        return sorted(list(groups))

    def get_project_name(self) -> str:
        headers = {"Authentication": self.api_key}
        endpoint = f"{self.api_url.rstrip('/')}/inventory/project/"

        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        self.project_name = response.json().get("name_en")
        return self.project_name

    def get_groups(self, save: bool = False) -> List[str]:
        headers = {"Authentication": self.api_key}
        endpoint = f"{self.api_url.rstrip('/')}/inventory/groups/"

        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        groups = []
        for group in response.json().get("result"):
            groups.append(group.get("name_en"))
        if save:
            self.groups = groups
        return groups

    def format_host_list(
        self, filtered_servers: List[Dict[str, Any]]
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """Format a list of servers into the expected host list format.

        Args:
            filtered_servers: List of server dictionaries
            ssh_key_path: Path to the SSH key to use for connections

        Returns:
            List of (hostname, attributes) tuples
        """

        return [
            (
                server["hostname"],
                {
                    **server.get("attributes", {}),
                    "ssh_user": server.get("ssh_user"),
                    "is_active": server.get("is_active", False),
                    "group_name": server.get("group", {}).get("name_en"),
                    "tags": server.get("tags", []),
                    "ssh_key": self.ssh_key_path,
                    **{
                        key: value
                        for key, value in server.items()
                        if key
                        not in [
                            "attributes",
                            "ssh_user",
                            "is_active",
                            "group",
                            "tags",
                            "ssh_hostname",
                        ]
                    },
                },
            )
            for server in filtered_servers
        ]

    def get_servers(
        self,
        timeout: int = 30,
    ) -> Tuple[List[Tuple[str, Dict[str, Any]]], str]:
        """Fetch servers from the API and handle user selection.
            timeout: Request timeout in seconds

        Returns:
            Tuple of (host_list, project_name)
        """
        try:
            headers = {"Authentication": self.api_key}
            endpoint = f"{self.api_url}/inventory/servers/"

            response = requests.get(endpoint, headers=headers, timeout=timeout)
            response.raise_for_status()
            raw_inventory = response.json()
            detected_project_name = self.get_project_name()
            servers = raw_inventory.get("result", [])
            filtered_servers = []

            for server in servers:
                if server.get("is_active"):
                    server_group = server.get("group", {}).get("name_en")
                    if self.groups:
                        if server_group not in self.groups:
                            continue
                    if self.tags:
                        if any(tag in self.tags for tag in server.get("tags", [])):
                            filtered_servers.append(server)
                    else:
                        filtered_servers.append(server)

            if len(filtered_servers) == 0:
                logger.error("No servers found")
                sys.exit(1)

            return self.format_host_list(filtered_servers), detected_project_name

        except requests.Timeout:
            logger.error("API request timed out")
            return [], "default"
        except requests.HTTPError as e:
            logger.error("HTTP error: %s", e)
            return [], "default"
        except requests.RequestException as e:
            logger.error("API request failed: %s", e)
            return [], "default"
        except json.JSONDecodeError as e:
            logger.error("Failed to parse API response: %s", e)
            return [], "default"
        except KeyError as e:
            logger.error("Missing required data in API response: %s", e)
            return [], "default"
        except Exception as e:
            logger.error("An unexpected error occurred: %s", str(e))
            return [], "default"
