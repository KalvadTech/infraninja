import pyinfra
from pyinfra.api import deploy
from infraninja.utils.pubkeys import add_ssh_keys as task2


@deploy("Test Security Setup")
def test_deploy():
    # define any deploys & functions above, and call below! add _sudo=True to any operations that require it
    task2()


pyinfra.api.deploy(
    test_deploy(),
)
