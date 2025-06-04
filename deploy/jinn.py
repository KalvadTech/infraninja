from infraninja.inventory.jinn import Jinn

jinn = Jinn(
    api_url="https://jinn-api-staging.kalvad.cloud",
    ssh_key_path="~/.ssh/id_rsa",
    api_key="API",
)
hosts = jinn.get_servers()
