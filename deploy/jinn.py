from infraninja.inventory.jinn import Jinn

jinn = Jinn(
    api_url="https://api.example.com",
    ssh_key_path="~/.ssh/id_rsa",
    api_key="api",
)
hosts = jinn.get_servers()
