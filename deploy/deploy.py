from pyinfra.api.deploy import deploy
from infraninja.security.common.ssh_hardening import SSHHardener
from infraninja.security.common.disable_services import ServiceDisabler


@deploy("Test Security Setup")
def test_deploy():
    config={
        "PermitRootLogin": "prohibit-password",
    }

    ssh_hardener = SSHHardener(config)
    ssh_hardener.deploy(_sudo=True)

    service_disabler = ServiceDisabler()
    service_disabler.deploy(_sudo=True)


test_deploy()