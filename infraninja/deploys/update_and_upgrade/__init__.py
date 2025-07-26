from pyinfra.api import deploy

from .update_and_upgrade import deploy_update, deploy_upgrade


@deploy("Update and Upgrade")
def update_and_upgrade():
    deploy_update()
    deploy_upgrade()
