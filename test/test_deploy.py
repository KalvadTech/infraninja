from pyinfra.api import deploy
from infraninja.security import security_setup
from infraninja.docker import install_docker
from infraninja.common import system_update

@deploy('Test Security Setup and Docker')
def test_deploy():
    # Run the security setup
    security_setup()
    
    # Install Docker
    install_docker()

    # Run common system updates
    system_update()

# Specify the VMs as inventory
inventory = [
    "vagrant@ubuntu",  # Ubuntu VM
    "vagrant@alpine",  # Alpine VM
]

# Execute the deploy on the VMs
pyinfra.api.deploy(
    test_deploy(),
    inventory=inventory,
    user='vagrant',
    sudo=True,
)
