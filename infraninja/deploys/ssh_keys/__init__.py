#!/usr/bin/env python3

import requests
from pyinfra.operations import server
from pyinfra.api import deploy, DeployError
from .defaults import DEFAULTS
from pyinfra import host


@deploy("Setup SSH keys", data_defaults=DEFAULTS)
def ssh_keys():
    infraninja = host.data.get("infraninja")["ssh_keys"]
    print(infraninja)
    if infraninja["user"] is None:
        raise DeployError("user is not set")
    keys = infraninja["ssh_keys"]
    for github_user in infraninja["github_users"]:
        url = "https://github.com/{}.keys".format(github_user)
        response = requests.request("GET", url)
        if response.status_code != 200:
            raise DeployError(f"Failed to fetch SSH keys for {github_user}")
        for key in response.text.split("\n"):
            if key != "":
                keys.append(f"{key} {github_user}@github")
    server.user_authorized_keys(
        infraninja["user"],
        keys,
        delete_keys=infraninja["delete"],
    )
