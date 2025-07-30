# In infraninja/deploys/jinn_test/deploy.py (or similar location)
from pyinfra.api.deploy import deploy
from pyinfra.operations import server


@deploy("JINN Test Deploy")
def jinn_test_deploy():
    """
    A test deploy specifically for Jinn integration testing.
    This deploy will automatically appear in Jinn's GUI.
    """

    # Example operations - customize as needed
    server.shell(
        name="Display Jinn test message",
        commands=["echo 'Hello from JINN TEST DEPLOY!'"],
    )

    server.shell(name="Show current date", commands=["date"])

    server.shell(name="Display system info", commands=["uname -a"])
