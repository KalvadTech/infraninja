import pyinfra
from pyinfra.api import deploy
from infraninja.security.common.smtp_hardening import smtp_hardening as task2
from infraninja.security.common.acl import acl_setup as task1


@deploy("Test Security Setup")
def test_deploy():
    # define any deploys & functions below! add _sudo=True to any operations that require it
    task2(_sudo=True)

pyinfra.api.deploy(
    test_deploy(),
)
