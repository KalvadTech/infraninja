from pyinfra.api import deploy

from .update_and_upgrade import deploy_update, deploy_upgrade


@deploy("Update and Upgrade")
def deploy_update_and_upgrade(state, host, extra_args=None):
    deploy_update(state=state, host=host, extra_args=extra_args)
    deploy_upgrade(state=state, host=host, extra_args=extra_args)
