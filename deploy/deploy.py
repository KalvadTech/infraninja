from pyinfra.api.deploy import deploy
from infraninja.security.ubuntu.fail2ban_setup import fail2ban_setup


@deploy("Test Security Setup")
def test_deploy():

    fail2ban_setup(_sudo=True)


test_deploy()