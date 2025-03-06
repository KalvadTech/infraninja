# inventory || jinn.py

import glob
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

sys.path.append(str(Path(__file__).parent.parent))
import requests
from inventory.config import NinjaConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)

config = NinjaConfig.from_env()


def get_groups_from_data(data):
    """Extract unique groups from server data."""
    groups = set()
    for server in data.get("result", []):
        group = server.get("group", {}).get("name_en")
        if group:
            groups.add(group)
    return sorted(list(groups))


def get_tags_from_data(servers: List[Dict]) -> List[str]:
    """Extract unique tags from server data."""
    tags = set()
    for server in servers:
        for tag in server.get("tags", []):
            if tag and not tag.isspace():  # Skip empty or whitespace-only tags
                tags.add(tag)
    return sorted(list(tags))


def fetch_ssh_config(
    api_auth_key: str, base_api_url: str, bastionless: bool = True
) -> str:
    """
    Fetch the SSH config from the API using an API key for authentication and return its content.
    """
    headers = {"Authentication": api_auth_key}
    endpoint = f"{base_api_url.rstrip('/')}{config.ssh_config_endpoint}"
    try:
        response = requests.get(
            endpoint, headers=headers, params={"bastionless": bastionless}, timeout=10
        )
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch SSH config: {e}")


def save_ssh_config(ssh_config_content: str, ssh_config_filename: str) -> None:
    """
    Save the SSH config content to a file in the SSH config directory.
    """
    os.makedirs(config.ssh_config_dir, exist_ok=True)
    config_path = os.path.join(config.ssh_config_dir, ssh_config_filename)
    with open(config_path, "w") as file:
        file.write(ssh_config_content)
    print("")
    logger.info("Saved SSH config to: %s", config_path)


def update_main_ssh_config():
    """
    Ensure the main .ssh/config includes the SSH config directory.
    """
    include_line = f"\nInclude {config.ssh_config_dir}/*\n"
    if os.path.exists(config.main_ssh_config):
        with open(config.main_ssh_config, "r") as file:
            if include_line in file.read():
                return  # Already included

    with open(config.main_ssh_config, "a") as file:
        file.write(include_line)
    logger.info("Updated main SSH config to include: %s/*", config.ssh_config_dir)


def get_valid_filename(default_name: str = config.default_ssh_config_filename) -> str:
    """Get a valid filename from user input."""
    while True:
        input_filename = input(
            f"Enter filename for SSH config [default: {default_name}]: "
        ).strip()
        if not input_filename:
            return default_name

        # Remove any directory components for security
        input_filename = os.path.basename(input_filename)

        # Check if filename is valid
        if not all(c.isalnum() or c in "-_." for c in input_filename):
            logger.warning(
                "Filename contains invalid characters. Use only letters, numbers, dots, hyphens, and underscores."
            )
            continue

        return input_filename


def get_project_name(data: Dict) -> str:
    """Extract project name from server data."""
    if not data.get("result"):
        return "default"

    # Get the first server that has project information
    for server in data["result"]:
        project = server.get("group", {}).get("project", {})
        if project and project.get("name_en"):
            return project["name_en"]

    return "default"


def fetch_servers(
    server_auth_key: str, server_api_url: str, selected_group: str = None
) -> Tuple[List[Tuple[str, Dict[str, Any]]], str]:
    try:
        # API call for servers
        headers = {"Authentication": server_auth_key}
        response = requests.get(
            f"{server_api_url.rstrip('/')}{config.inventory_endpoint}", headers=headers
        )
        response.raise_for_status()
        data = response.json()

        # Extract project name early
        detected_project_name = get_project_name(data)

        # First, display available groups sorted alphabetically
        groups = get_groups_from_data(data)
        logger.info("\nAvailable groups:")
        for i, group in enumerate(groups, 1):
            logger.info("%d. %s", i, group)

        # If no group is selected, prompt for selection
        if selected_group is None:
            while True:
                if os.environ.get("JINN_GROUPS"):
                    choice = os.environ.get("JINN_GROUPS").strip()
                else:
                    choice = input(
                        "\nEnter group numbers (space-separated) or '*' for all groups: "
                    ).strip()
                if choice in ("*", ""):
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

        # Filter servers by selected groups first
        filtered_servers = [
            server
            for server in data.get("result", [])
            if server.get("group", {}).get("name_en") in selected_groups
            and server.get("is_active", False)
        ]

        # Tag selection with sorted display
        tags = get_tags_from_data(filtered_servers)
        if tags:
            logger.info("\nAvailable tags:")
            for i, tag in enumerate(tags, 1):
                logger.info("%2d. %s", i, tag)  # Align numbers for better readability
            if os.environ.get("JINN_TAGS"):
                tag_choice = os.environ.get("JINN_TAGS").strip()
            else:
                tag_choice = input(
                    "\nSelect tags (space-separated), '*' or Enter for all: "
                ).strip()

            if tag_choice and tag_choice != "*":
                try:
                    selected_indices = [int(i) - 1 for i in tag_choice.split()]
                    selected_tags = {
                        tags[i] for i in selected_indices if 0 <= i < len(tags)
                    }
                    # Filter servers by tags
                    filtered_servers = [
                        server
                        for server in filtered_servers
                        if any(tag in selected_tags for tag in server.get("tags", []))
                    ]
                except (ValueError, IndexError):
                    logger.warning("Invalid tag selection, showing all servers")

        # Convert to host list format
        hosts = [
            (
                server["hostname"],
                {
                    **server.get("attributes", {}),
                    "ssh_user": server.get("ssh_user"),
                    "is_active": server.get("is_active", False),
                    "group_name": server.get("group", {}).get("name_en"),
                    "tags": server.get("tags", []),
                    "ssh_key": SSH_KEY_PATH,
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

        return hosts, detected_project_name

    except requests.exceptions.RequestException as e:
        logger.error("An error occurred while making the request: %s", e)
        return [], "default"
    except KeyError as e:
        logger.error("Error parsing response: %s", e)
        return [], "default"
    except Exception as e:
        logger.error("An unexpected error occurred: %s", e)
        return [], "default"


def find_ssh_keys() -> List[str]:
    """
    Find all SSH private keys in the user's .ssh directory.
    Returns a list of full paths to SSH private key files.
    """
    ssh_dir = os.path.expanduser("~/.ssh")
    # List all files in the .ssh directory
    all_files = glob.glob(os.path.join(ssh_dir, "*"))

    # Filter for likely private keys (no .pub extension and not common non-key files)
    excluded_files = ["known_hosts", "authorized_keys", "config"]
    private_keys = [
        f
        for f in all_files
        if os.path.isfile(f)
        and not f.endswith(".pub")
        and os.path.basename(f) not in excluded_files
        and not os.path.basename(f).startswith(".")
    ]

    # Common key naming patterns to prioritize
    common_patterns = ["id_rsa", "id_ed25519", "id_dsa", "id_ecdsa", "identity"]

    # Sort keys by putting common ones first
    def key_sort(path):
        basename = os.path.basename(path)
        for i, pattern in enumerate(common_patterns):
            if pattern in basename:
                return (0, i)  # Common patterns first, in order of commonness
        return (1, basename)  # Then alphabetically

    return sorted(private_keys, key=key_sort)


def select_ssh_key() -> str:
    """
    Allow user to select from available SSH keys or specify a custom path.
    Returns the full path to the selected SSH key.
    """
    # Find available SSH keys
    available_keys = find_ssh_keys()

    if not available_keys:
        logger.warning("No SSH private keys found in ~/.ssh directory.")
        custom_path = input("Enter the full path to your SSH private key: ")
        return (
            os.path.expanduser(custom_path)
            if custom_path
            else os.path.expanduser("~/.ssh/id_rsa")
        )

    # Display available keys
    logger.info("\nAvailable SSH keys:")
    for i, key_path in enumerate(available_keys, 1):
        key_display = key_path.replace(os.path.expanduser("~"), "~")
        logger.info("%d. %s", i, key_display)

    # Add option for custom path
    custom_option = len(available_keys) + 1
    logger.info("%d. Specify a custom path", custom_option)

    # Get user selection
    choice_text = (
        input(f"\nSelect an SSH key (1-{custom_option}) [default: 1]: ").strip() or "1"
    )

    try:
        choice = int(choice_text)
        if 1 <= choice <= len(available_keys):
            selected_key = available_keys[choice - 1]
            logger.info("Selected SSH key: %s", selected_key)
            return selected_key
        elif choice == custom_option:
            custom_path = input("Enter the full path to your SSH private key: ")
            return (
                os.path.expanduser(custom_path)
                if custom_path
                else os.path.expanduser("~/.ssh/id_rsa")
            )
        else:
            logger.warning("Invalid choice, using the first key.")
            return available_keys[0]
    except ValueError:
        logger.warning("Invalid input, using the first key.")
        return available_keys[0]


# Direct script execution
try:
    if os.environ.get("SSH_KEY_PATH"):
        SSH_KEY_PATH = os.environ.get("SSH_KEY_PATH")
    else:
        SSH_KEY_PATH = select_ssh_key()

    auth_key = config.api_key or input("Please enter your access key: ")
    api_url = config.api_url or input("Please enter the Jinn API base URL: ")

    server_list, project_name = fetch_servers(auth_key, api_url)

    config_content = fetch_ssh_config(auth_key, api_url, bastionless=True)
    if config_content:
        default_config_name = f"{project_name}_ssh_config"
        config_filename = get_valid_filename(default_config_name)
        save_ssh_config(config_content, config_filename)
        update_main_ssh_config()
        logger.info("SSH configuration setup is complete.")

    if not server_list:
        logger.error("No valid hosts found. Check the API response and try again.")
    else:
        logger.info("\nSelected servers:")
        for hostname, attrs in server_list:
            logger.info("- %s (User: %s)", hostname, attrs["ssh_user"])

except Exception as e:
    logger.error("An error occurred: %s", str(e))
