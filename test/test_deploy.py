import pyinfra
from pyinfra.api import deploy

from infraninja.utils.pubkeys import add_ssh_keys as task1


@deploy("Test Security Setup")
def test_deploy():
    # define any deploys & functions below! add sudo=True to any operations that require it
    task1()


pyinfra.api.deploy(
    test_deploy(),
)
