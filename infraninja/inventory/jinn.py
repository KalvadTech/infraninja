# inventory || jinn.py

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import requests
from requests.exceptions import RequestException

sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


class JinnError(Exception):
    """Base exception for Jinn-related errors."""

    pass


class JinnAPIError(JinnError):
    """Exception raised for API-related errors."""

    pass


class JinnSSHError(JinnError):
    """Exception raised for SSH-related errors."""

    pass


class Jinn:
    def __init__(
        self,
        ssh_key_path: Optional[Union[str, Path]] = None,
        api_url: str = "https://jinn-api.kalvad.cloud",
        api_key: Optional[str] = None,
        groups: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        use_bastion: bool = False,
        ssh_config_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        """Initialize the Jinn class with configuration.

        Args:
            ssh_key_path: Path to SSH key file. If None, uses ~/.ssh/id_rsa
            api_url: Base URL for the Jinn API
            api_key: API key for authentication
            groups: Server groups to filter by
            tags: Server tags to filter by
            use_bastion: Whether to use bastion host
            ssh_config_dir: Directory for SSH config files. If None, uses ~/.ssh/config.d

        Raises:
            JinnSSHError: If SSH key path does not exist
            JinnAPIError: If API key is not set
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
            raise JinnSSHError(f"SSH key path does not exist: {self.ssh_key_path}")

        # Set API configuration
        self.api_url: str = api_url.rstrip("/")
        self.api_key: Optional[str] = api_key
        if not self.api_key:
            raise JinnAPIError("API key is not set")

        # Set filtering options
        self.groups: Optional[List[str]] = groups
        self.tags: Optional[List[str]] = tags
        self.use_bastion: bool = use_bastion
        self.project_name: Optional[str] = None
        self.servers: List[Tuple[str, Dict[str, Any]]] = []

        # Set SSH config endpoint based on bastion usage
        self.ssh_config_endpoint: str = "/ssh-tools/ssh-config/"

        # Load initial configuration
        self.get_project_name()
        self.load_servers()
        self.refresh_ssh_config()

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
        """Get the project name from the API.

        Returns:
            str: The project name

        Raises:
            JinnAPIError: If the API request fails
        """
        try:
            headers = {"Authentication": self.api_key}
            endpoint = f"{self.api_url.rstrip('/')}/inventory/project/"

            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            self.project_name = response.json().get("name_en")
            return self.project_name
        except RequestException as e:
            raise JinnAPIError(f"Failed to get project name: {str(e)}")

    def get_groups(self, save: bool = False) -> List[str]:
        """Get available groups from the API.

        Args:
            save: Whether to save the groups to the instance

        Returns:
            List[str]: List of group names

        Raises:
            JinnAPIError: If the API request fails
        """
        try:
            headers = {"Authentication": self.api_key}
            endpoint = f"{self.api_url.rstrip('/')}/inventory/groups/"

            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            groups = [
                group.get("name_en") for group in response.json().get("result", [])
            ]
            if save:
                self.groups = groups
            return groups
        except RequestException as e:
            raise JinnAPIError(f"Failed to get groups: {str(e)}")

    def format_host_list(
        self, filtered_servers: List[Dict[str, Any]]
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """Format a list of servers into the expected host list format.

        Args:
            filtered_servers: List of server dictionaries

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
                    "ssh_key": str(self.ssh_key_path),
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

    def _filter_server(self, server: Dict[str, Any]) -> bool:
        """Filter a server based on groups and tags.

        Args:
            server: Server data dictionary

        Returns:
            bool: True if server matches filters, False otherwise
        """
        if not server.get("is_active"):
            return False

        server_group = server.get("group", {}).get("name_en")
        server_tags = set(server.get("tags", []))

        if self.groups and server_group not in self.groups:
            return False

        if self.tags:
            return any(tag in server_tags for tag in self.tags)

        return True

    def load_servers(
        self,
        timeout: int = 30,
    ) -> None:
        """Fetch servers from the API and handle user selection.

        Args:
            timeout: Request timeout in seconds

        Raises:
            JinnAPIError: If the API request fails or no servers are found
        """
        try:
            headers = {"Authentication": self.api_key}
            endpoint = f"{self.api_url}/inventory/servers/"

            response = requests.get(endpoint, headers=headers, timeout=timeout)
            response.raise_for_status()
            raw_inventory = response.json()
            servers = raw_inventory.get("result", [])

            # Filter servers
            filtered_servers = [s for s in servers if self._filter_server(s)]

            if not filtered_servers:
                raise JinnAPIError("No servers found matching the specified criteria")

            self.servers = self.format_host_list(filtered_servers)

        except requests.Timeout:
            raise JinnAPIError("API request timed out")
        except requests.HTTPError as e:
            raise JinnAPIError(f"HTTP error: {str(e)}")
        except requests.RequestException as e:
            raise JinnAPIError(f"API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise JinnAPIError(f"Failed to parse API response: {str(e)}")
        except KeyError as e:
            raise JinnAPIError(f"Missing required data in API response: {str(e)}")
        except Exception as e:
            raise JinnAPIError(f"An unexpected error occurred: {str(e)}")

    def get_servers(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Get the list of servers.

        Returns:
            List[Tuple[str, Dict[str, Any]]]: List of (hostname, attributes) tuples
        """
        return self.servers

    def get_ssh_config(self) -> str:
        """Fetch SSH configuration from the API.

        Returns:
            str: SSH configuration content

        Raises:
            JinnAPIError: If the API request fails
        """
        try:
            headers = {"Authentication": self.api_key}
            response = requests.get(
                f"{self.api_url}{self.ssh_config_endpoint}",
                headers=headers,
                params={"bastionless": not self.use_bastion},
                timeout=30,
            )
            response.raise_for_status()
            return response.text

        except RequestException as e:
            raise JinnAPIError(f"Failed to fetch SSH config: {str(e)}")

    def save_ssh_config(self, config_content: str) -> None:
        """Save SSH configuration to a file.

        Args:
            config_content: SSH configuration content to save

        Raises:
            JinnSSHError: If saving the config fails
        """
        try:
            # Clean the content to remove any potential include loops
            cleaned_content = []
            for line in config_content.splitlines():
                # Skip any Include directives that might create loops
                if line.strip().startswith("Include") and (
                    ".ssh/config" in line or self.ssh_config_dir.name in line
                ):
                    logger.warning(f"Skipping potential include loop: {line}")
                    continue
                cleaned_content.append(line)

            # Write the cleaned config
            config_file = self.ssh_config_dir / f"jinn_{self.project_name}_config"
            config_file.write_text("\n".join(cleaned_content))
            os.chmod(config_file, 0o600)  # Set secure permissions

        except Exception as e:
            raise JinnSSHError(f"Failed to save SSH config: {str(e)}")

    def update_main_ssh_config(self) -> None:
        """Update the main SSH config file to include Jinn configs.

        Raises:
            JinnSSHError: If updating the config fails
        """
        try:
            # Read existing config
            if self.main_ssh_config.exists():
                existing_config = self.main_ssh_config.read_text()
            else:
                existing_config = ""

            # Add include directive if not present
            include_directive = f"Include {self.ssh_config_dir}/*\n"

            if self.main_ssh_config.exists():
                filtered_lines = []
                for line in existing_config.splitlines():
                    if not line.strip().startswith(f"Include {self.ssh_config_dir}/"):
                        filtered_lines.append(line)

                # Write the cleaned config with a single include directive
                with open(self.main_ssh_config, "w") as f:
                    f.write("\n".join(filtered_lines))
                    if filtered_lines and filtered_lines[-1].strip():
                        f.write("\n\n")  # Add space if content exists
                    f.write(include_directive)
            else:
                # Create the file with just the include directive
                with open(self.main_ssh_config, "w") as f:
                    f.write(include_directive)

            os.chmod(self.main_ssh_config, 0o600)  # Set secure permissions

        except Exception as e:
            raise JinnSSHError(f"Failed to update main SSH config: {str(e)}")

    def refresh_ssh_config(self) -> None:
        """Fetch and save new SSH configuration.

        Raises:
            JinnAPIError: If fetching the config fails
            JinnSSHError: If saving the config fails
        """
        config_content = self.get_ssh_config()
        self.save_ssh_config(config_content)
        self.update_main_ssh_config()

    def get_server_by_hostname(self, hostname: str) -> Optional[Dict[str, Any]]:
        """Get server details by hostname.

        Args:
            hostname: Server hostname to look up

        Returns:
            Optional[Dict[str, Any]]: Server details if found, None otherwise
        """
        for server_hostname, attributes in self.servers:
            if server_hostname == hostname:
                return attributes
        return None

    def get_servers_by_group(self, group: str) -> List[Tuple[str, Dict[str, Any]]]:
        """Get all servers in a specific group.

        Args:
            group: Group name to filter by

        Returns:
            List[Tuple[str, Dict[str, Any]]]: List of (hostname, attributes) tuples
        """
        original_groups = self.groups
        self.groups = [group]
        try:
            self.load_servers()
            return self.servers
        finally:
            self.groups = original_groups

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
