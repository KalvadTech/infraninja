# invetory || jinn.py

import logging
import paramiko
import requests
from typing import Dict, Any, List, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


def get_groups_from_data(data):
    """Extract unique groups from server data."""
    groups = set()
    for server in data.get("result", []):
        group = server.get("group", {}).get("name_en")
        if group:
            groups.add(group)
    return sorted(list(groups))


def fetch_ssh_config(access_key: str) -> str:
    """Fetch SSH configuration from API."""
    headers = {"Authentication": access_key}
    response = requests.get(
        ssh_config_url,
        headers=headers
    )
    return response.text


def parse_ssh_config(config_text: str) -> Dict[str, Dict[str, str]]:
    """Parse SSH config text into dictionary."""
    configs = {}
    current_host = None
    
    for line in config_text.splitlines():
        line = line.strip()
        if line.startswith('Host ') and not line.startswith('Host *'):
            current_host = line.split()[1]
            configs[current_host] = {}
        elif current_host and '    ' in line:
            key, value = line.strip().split(None, 1)
            configs[current_host][key] = value
    return configs


def fetch_servers(access_key: str, selected_group: str = None) -> List[Tuple[str, Dict[str, Any]]]:
    try:
        # Fetch and parse SSH configs
        ssh_configs = parse_ssh_config(fetch_ssh_config(access_key))
        
        # Existing API call for servers
        headers = {"Authentication": access_key}
        response = requests.get(inventory_api_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # First, display available groups
        groups = get_groups_from_data(data)
        logger.info("\nAvailable groups:")
        for i, group in enumerate(groups, 1):
            logger.info("%d. %s", i, group)

        # If no group is selected, prompt for selection
        if selected_group is None:
            while True:
                choice = input(
                    "\nEnter group numbers (space-separated) or '*' for all groups: "
                ).strip()
                if choice == "*":
                    selected_groups = groups
                    break
                try:
                    # Split input and convert to integers
                    choices = [int(x) for x in choice.split()]
                    # Validate all choices
                    if all(1 <= x <= len(groups) for x in choices):
                        selected_groups = [groups[i - 1] for i in choices]
                        break
                    logger.warning("Invalid choice. Please select valid numbers.")
                except ValueError:
                    logger.warning("Please enter valid numbers or '*'.")

            logger.info("\nSelected groups: %s", ", ".join(selected_groups))

        else:
            selected_groups = [selected_group]

        # Filter servers by selected groups
        return [
            (
                server["ssh_hostname"],
                {
                    **server.get("attributes", {}),
                    "ssh_user": ssh_configs.get(server["ssh_hostname"], {}).get("User", server.get("ssh_user")),
                    "is_active": server.get("is_active", False),
                    "ssh_paramiko_connect_kwargs": {
                        "key_filename": ssh_configs.get(server["ssh_hostname"], {}).get("IdentityFile"),
                        "sock": paramiko.ProxyCommand(
                            ssh_configs.get(server["ssh_hostname"], {}).get("ProxyCommand", "")
                        ) if ssh_configs.get(server["ssh_hostname"], {}).get("ProxyCommand") else None
                    },
                    "group_name": server.get("group", {}).get("name_en"),
                    **{
                        key: value
                        for key, value in server.items()
                        if key not in ["attributes", "ssh_user", "is_active", "group"]
                    },
                },
            )
            for server in data.get("result", [])
            if server.get("group", {}).get("name_en") in selected_groups
            and server.get("is_active", False)  # Only active servers
        ]

    except requests.exceptions.RequestException as e:
        logger.error("An error occurred while making the request: %s", e)
        return []
    except KeyError as e:
        logger.error("Error parsing response: %s", e)
        return []
    except Exception as e:
        logger.error("An unexpected error occurred: %s", e)
        return []


access_key = input("Please enter your access key: ")
inventory_api_url = input("Please enter the URL to list inventory: ")
ssh_config_url = input("Please enter the URL for SSH config: ")
hosts = fetch_servers(access_key)

logger.info("\nSelected servers:")
for hostname, attrs in hosts:
    logger.info("- %s (User: %s)", hostname, attrs["ssh_user"])
    logger.info("- %s (User: %s)", hostname, attrs["ssh_user"])
