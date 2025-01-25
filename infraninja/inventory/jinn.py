# inventory || jinn.py

import os
import logging
import requests
from typing import Dict, Any, List, Tuple
from infraninja.utils.motd import show_motd

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)

show_motd(skip_initial=False)

INVENTORY_ENDPOINT = "/inventory/servers/"


def get_groups_from_data(data):
    """Extract unique groups from server data."""
    groups = set()
    for server in data.get("result", []):
        group = server.get("group", {}).get("name_en")
        if group:
            groups.add(group)
    return sorted(list(groups))


def fetch_servers(
    access_key: str, base_url: str, selected_group: str = None
) -> List[Tuple[str, Dict[str, Any]]]:
    try:
        # API call for servers
        headers = {"Authentication": access_key}
        response = requests.get(
            f"{base_url.rstrip('/')}{INVENTORY_ENDPOINT}", headers=headers
        )
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
        hosts = [
            (
                server["hostname"],
                {
                    **server.get("attributes", {}),
                    "ssh_user": server.get("ssh_user"),
                    "is_active": server.get("is_active", False),
                    "group_name": server.get("group", {}).get("name_en"),
                    "ssh_key": key_path,
                    **{
                        key: value
                        for key, value in server.items()
                        # Exclude keys that override SSH config
                        if key
                        not in [
                            "attributes",
                            "ssh_user",
                            "is_active",
                            "group",
                            "ssh_hostname",  # ADD THIS LINE
                        ]
                    },
                },
            )
            for server in data.get("result", [])
            if server.get("group", {}).get("name_en") in selected_groups
            and server.get("is_active", False)
        ]

        return hosts

    except requests.exceptions.RequestException as e:
        logger.error("An error occurred while making the request: %s", e)
        return []
    except KeyError as e:
        logger.error("Error parsing response: %s", e)
        return []
    except Exception as e:
        logger.error("An unexpected error occurred: %s", e)
        return []


# use the os import to get the .ssh key path
key_path = os.path.expanduser("~/.ssh/id_rsa")

access_key = input("Please enter your access key: ")
base_url = input("Please enter the Jinn API base URL: ")
hosts = fetch_servers(access_key, base_url)

logger.info("\nSelected servers:")
for hostname, attrs in hosts:
    logger.info("- %s (User: %s)", hostname, attrs["ssh_user"])
