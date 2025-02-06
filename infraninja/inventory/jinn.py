# inventory || jinn.py

import os
import logging
import requests
from typing import Dict, Any, List, Tuple
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


INVENTORY_ENDPOINT = "/inventory/servers/"
SSH_CONFIG_ENDPOINT = "/ssh-tools/ssh-config/?bastionless=true"
LOGIN_ENDPOINT = "/login/"
EXCLUDED_FILES = {"config", "known_hosts", "authorized_keys", "environment"}
SSH_CONFIG_DIR = os.path.expanduser("~/.ssh/config.d")
MAIN_SSH_CONFIG = os.path.expanduser("~/.ssh/config")


def get_groups_from_data(data):
    """Extract unique groups from server data."""
    groups = set()
    for server in data.get("result", []):
        if server.get("group", {}).get("name_en"):
            groups.add(server["group"]["name_en"])
    return sorted(list(groups))


def get_ssh_key(server_data: dict) -> str:
    """Dynamically find all possible SSH keys in ~/.ssh"""
    # 1. Check if key is specified in server data
    if server_data.get("ssh_key"):
        expanded_key = os.path.expanduser(server_data["ssh_key"])
        if os.path.exists(expanded_key):
            return expanded_key

    # 2. Check for project-specific keys
    key_dir = Path.home() / ".ssh" / "keys"
    project_keys = []
    if key_dir.exists():
        for key_file in key_dir.glob(f"{server_data['hostname']}*"):
            if key_file.is_file() and key_file.stat().st_mode & 0o400:
                project_keys.append(str(key_file))

    # 3. Find all potential keys in ~/.ssh
    ssh_dir = Path.home() / ".ssh"
    system_keys = []
    for key_file in ssh_dir.iterdir():
        if (
            key_file.is_file()
            and not key_file.name.endswith(".pub")
            and key_file.name not in EXCLUDED_FILES
            and key_file.stat().st_mode & 0o400
        ):
            system_keys.append(str(key_file))

    # Combine and deduplicate keys
    found_keys = list(set(project_keys + system_keys))

    # 4. Handle key selection
    if len(found_keys) > 1:
        logger.info("\nDiscovered SSH keys:")
        for i, key in enumerate(found_keys, 1):
            logger.info("%d. %s", i, key)
        while True:
            choice = input("Select key to use (number) or 'cancel' to abort: ").strip()
            if choice.lower() == "cancel":
                raise ValueError("SSH key selection cancelled")
            try:
                selected = found_keys[int(choice) - 1]
                if not os.path.isfile(selected):
                    raise ValueError("Selected path is not a file")
                return selected
            except (ValueError, IndexError):
                logger.warning("Invalid selection, please try again")

    if found_keys:
        return found_keys[0]

    raise FileNotFoundError("No valid SSH keys found in ~/.ssh")


def configure_ssh_settings(server: dict) -> dict:
    """Configure SSH settings including bastion proxy."""
    config = {}

    # Bastion configuration
    if server.get("bastion"):
        bastion = server["bastion"]
        proxy_command = (
            f"ssh -W %h:%p -p {bastion.get('port', 22)} "
            f"{bastion['ssh_user']}@{bastion['hostname']}"
        )
        config.update({"_ssh_proxy_command": proxy_command, "_ssh_forward_agent": True})

    # SSH key configuration
    try:
        config["ssh_key"] = get_ssh_key(server)
    except Exception as e:
        logger.error("SSH key error for %s: %s", server["hostname"], str(e))
        raise

    # Port configuration
    if server.get("ssh_port"):
        config["ssh_port"] = server["ssh_port"]

    return config


def fetch_ssh_config(base_url: str, api_key: str, bastionless: bool = True) -> str:
    """
    Fetch the SSH config from the API using an API key for authentication and return its content.
    """
    headers = {"Authentication": api_key}
    endpoint = f"{base_url.rstrip('/')}{SSH_CONFIG_ENDPOINT}"
    try:
        response = requests.get(
            endpoint, headers=headers, params={"bastionless": bastionless}, timeout=10
        )
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        raise RuntimeError("Failed to fetch SSH config: %s" % str(e))


def save_ssh_config(config_content: str, filename: str) -> None:
    """
    Save the SSH config content to a file in the SSH config directory.
    """
    os.makedirs(SSH_CONFIG_DIR, exist_ok=True)
    config_path = os.path.join(SSH_CONFIG_DIR, filename)
    with open(config_path, "w") as file:
        file.write(config_content)
    print("")
    logger.info("Saved SSH config to: %s", config_path)


def update_main_ssh_config():
    """
    Ensure the main .ssh/config includes the SSH config directory.
    """
    include_line = f"\nInclude {SSH_CONFIG_DIR}/*\n"
    if os.path.exists(MAIN_SSH_CONFIG):
        with open(MAIN_SSH_CONFIG, "r") as file:
            if include_line in file.read():
                return  # Already included

    with open(MAIN_SSH_CONFIG, "a") as file:
        file.write(include_line)
    logger.info("Updated main SSH config to include: %s/*", SSH_CONFIG_DIR)


def fetch_servers(
    access_key: str, base_url: str, selected_group: str = None
) -> List[Tuple[str, Dict[str, Any]]]:
    try:
        # API call for servers
        headers = {"Authentication": access_key}
        response = requests.get(
            f"{base_url.rstrip('/')}{INVENTORY_ENDPOINT}", headers=headers, timeout=10
        )
        response.raise_for_status()
        data = response.json()

        # Get groups
        groups = get_groups_from_data(data)
        if not groups:
            logger.error("No groups found in API response")
            return []

        # Group selection logic
        logger.info("\nAvailable groups:")
        for i, group in enumerate(groups, 1):
            logger.info("%d. %s", i, group)

        selected_groups = [selected_group] if selected_group else []
        if not selected_groups:
            while True:
                choice = input(
                    "\nEnter group numbers (space-separated) or '*' for all groups: "
                ).strip()
                if choice in ("*", ""):
                    selected_groups = groups
                    break
                try:
                    choices = [int(x) for x in choice.split()]
                    if all(1 <= x <= len(groups) for x in choices):
                        selected_groups = [groups[i - 1] for i in choices]
                        break
                    logger.warning("Invalid choice. Please select valid numbers.")
                except ValueError:
                    logger.warning("Please enter valid numbers or '*'.")

        logger.info("\nSelected groups: %s", ", ".join(selected_groups))

        # Build host list
        hosts = []
        server_names = []

        for server in data.get("result", []):
            try:
                if not all(
                    [
                        server.get("group", {}).get("name_en") in selected_groups,
                        server.get("is_active", False),
                        server.get("hostname"),
                    ]
                ):
                    continue

                ssh_config = configure_ssh_settings(server)

                hostname = server["hostname"]
                server_names.append(hostname)
                hosts.append(
                    (
                        hostname,
                        {
                            "ssh_user": server.get("ssh_user"),
                            "ssh_key": ssh_config["ssh_key"],
                            "_ssh_proxy_command": ssh_config.get("_ssh_proxy_command"),
                            "ssh_port": server["ssh_port"],
                            **server.get("attributes", {}),
                        },
                    )
                )

            except KeyError as e:
                logger.error("Skipping server due to missing key: %s", str(e))
                continue
            except Exception as e:
                logger.error("Skipping %s: %s", server.get("hostname"), str(e))
                continue

        return hosts

    except requests.exceptions.RequestException as e:
        logger.error("API request failed: %s", str(e))
        return []
    except Exception as e:
        logger.error("Critical error: %s", str(e))
        return []


def get_valid_filename(default_name: str = "bastionless_ssh_config") -> str:
    """Get a valid filename from user input."""
    while True:
        filename = input(
            f"Enter filename for SSH config [default: {default_name}]: "
        ).strip()
        if not filename:
            return default_name

        # Remove any directory components for security
        filename = os.path.basename(filename)

        # Check if filename is valid
        if not all(c.isalnum() or c in "-_." for c in filename):
            logger.warning(
                "Filename contains invalid characters. Use only letters, numbers, dots, hyphens, and underscores."
            )
            continue

        return filename


def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system("clear" if os.name == "posix" else "cls")


# Show MOTD first
clear_screen()

# Get credentials and fetch servers
try:
    access_key = input("Please enter your access key: ")
    base_url = input("Please enter the Jinn API base URL: ")

    # Set environment variable for base_url
    os.environ["JINN_API_BASE_URL"] = base_url

    ssh_config = fetch_ssh_config(base_url, access_key, bastionless=True)

    if ssh_config:
        filename = get_valid_filename()
        save_ssh_config(ssh_config, filename)
        update_main_ssh_config()  # Add this line to ensure the config is included
        logger.info("SSH configuration setup is complete.")

    # Fetch and select groups
    hosts = fetch_servers(access_key, base_url)

    # Wait and refresh before SSH key selection

    if not hosts:
        logger.error("No valid hosts found. Check the API response and try again.")
    else:
        logger.info("\nSelected servers:")
        for hostname, attrs in hosts:
            logger.info("- %s (User: %s)", hostname, attrs["ssh_user"])
        logger.info("--> Connecting to hosts...")

except Exception as e:
    logger.error("An error occurred: %s", str(e))
