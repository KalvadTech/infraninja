from pyinfra.api.deploy import deploy
from infraninja.security.common.update_packages import system_update as task1

@deploy("Test Security Setup")
def test_deploy():
    task1(_sudo=True)
    


test_deploy()