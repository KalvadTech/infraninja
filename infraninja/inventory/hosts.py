# inventory/hosts.py

# Define your hosts here
# Replace 'your.server.ip' with actual server IP addresses
ubuntu_servers = [ ("your.server.ip", {"ssh_user": "user", "ssh_key": "/path/to/file"}) ]
alpine_servers = [ ("your.server.ip", {"ssh_user": "user", "ssh_key": "/path/to/file"}) ]

# Group hosts
groups = {
    "ubuntu": ubuntu_servers,
    "alpine": alpine_servers,
}

# All hosts
all_hosts = ubuntu_servers + alpine_servers
