from pyinfra.api.deploy import deploy
from infraninja.utils.pubkeys import SSHKeyManager


@deploy("Test Security Setup")
def test_deploy():
    # Create an instance of SSHKeyManager with the API credentials
    key_manager = SSHKeyManager(
        api_url="URLHERE", 
        api_key="APIKEYHERE"
    )
    
    key_manager.add_ssh_keys()


test_deploy()