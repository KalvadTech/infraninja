import os
import requests
import getpass
from pyinfra.operations import server
from pyinfra.api import deploy
from pyinfra import host
from pyinfra.facts.server import User, Users
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


@deploy("Add SSH keys to authorized_keys")
def add_ssh_keys():
    # Get base_url from environment variable
    base_url = os.getenv("JINN_API_BASE_URL")
    if not base_url:
        logger.error("Error: JINN_API_BASE_URL environment variable not set")
        return False

    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")

    login_endpoint = f"{base_url}/login/"
    login_data = {"username": username, "password": password}

    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    try:
        response = requests.post(login_endpoint, json=login_data, headers=headers)

        if response.status_code != 200:
            print(f"Login failed: {response.text}")
            return

        response_data = response.json()
        session_key = response_data.get("session_key")

        if not session_key:
            print("Error: Session key missing in response.")
            return

        auth_headers = {
            "Authorization": f"Bearer {session_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        cookies = {"sessionid": session_key}

        ssh_endpoint = f"{base_url}/ssh-tools/ssh-keylist/"
        ssh_response = requests.get(ssh_endpoint, headers=auth_headers, cookies=cookies)

        if ssh_response.status_code != 200:
            print(f"Failed to retrieve SSH keys: {ssh_response.text}")
            return

        ssh_data = ssh_response.json()

        try:
            # Get current user details using proper fact classes
            current_user = host.get_fact(User)
            user_details = host.get_fact(Users)[current_user]

            # Extract public keys from response
            public_keys = [key_data["key"] for key_data in ssh_data["result"]]

            # Add keys using server operation
            server.user_authorized_keys(
                name=f"Add SSH keys for {current_user}",
                user=current_user,
                group=user_details["group"],
                public_keys=public_keys,
                delete_keys=False,
            )

        except (KeyError, AttributeError) as e:
            print(f"Error getting user details: {e}")
            return False
        except Exception as e:
            print(f"Error setting up SSH keys: {e}")
            return False

        return True

    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
