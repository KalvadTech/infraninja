#!/usr/bin/env python3

import requests
from pyinfra.operations import server
from pyinfra.api import deploy, DeployError
from .defaults import DEFAULTS

@deploy("Setup SSH keys", data_defaults=DEFAULTS)
def ssh_keys():
    if host.data.ssh_keys_user is None:
        raise DeployError("ssh_keys_user is not set")
    keys = host.data.ssh_keys
    for github_user in host.data.github_users:
        url = "https://github.com/{}.keys".format(github_user)
        response = requests.request("GET", url)
        if response.status_code != 200:
            raise DeployError(f"Failed to fetch SSH keys for {github_user}")
        for key in response.text.split("\n"):
            if key != "":
                keys.append(f"{key} {github_user}@github")
    server.user_authorized_keys(
        host.data.ssh_keys_user, keys, delete_keys=host.data.delete_ssh_keys
    )
