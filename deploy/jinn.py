from infraninja.inventory.jinn import Jinn

jinn = Jinn(
    api_url="https://jinn-api-staging.kalvad.cloud",
    ssh_key_path="/path/to/your/private/key",
    api_key="your_api_key",
)
hosts = jinn.get_servers()
