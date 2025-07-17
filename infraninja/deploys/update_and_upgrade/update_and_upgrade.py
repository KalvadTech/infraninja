from pyinfra import host, operations
from pyinfra.api import DeployError, deploy
from pyinfra.facts.server import OsRelease


@deploy("Update")
def deploy_update():
    os_id = host.get_fact(OsRelease).get("id")
    os_id_like = host.get_fact(OsRelease).get("id_like")
    if os_id_like:
        if "debian" in os_id_like:
            operations.server.apt.update(
                name="Update apt repositories",
            )
        elif "rhel" in os_id_like:
            operations.server.dnf.update(
                name="Update dnf repositories",
            )
        elif "arch" in os_id_like:
            operations.server.pacman.update(
                name="Update pacman repositories",
            )
        else:
            raise DeployError(f"Unsupported OS: {os_id} {os_id_like}")
    else:
        if os_id == "alpine":
            operations.server.apk.update(
                name="Update apk repositories",
            )
        elif os_id == "freebsd":
            # TODO: Add freebsd-update operation once released
            operations.server.shell(
                name="Run freebsd-update",
                commands=["freebsd-update fetch"],
            )
            # TODO: Add pkg update operation once released
            operations.server.shell(
                name="Run pkg update",
                commands=["pkg update"],
            )
        else:
            raise DeployError(f"Unsupported OS: {os_id} {os_id_like}")


@deploy("Upgrade")
def deploy_upgrade():
    os_id = host.get_fact(OsRelease).get("id")
    os_id_like = host.get_fact(OsRelease).get("id_like")
    if os_id_like:
        if "debian" in os_id_like:
            operations.server.apt.upgrade(
                name="Upgrade apt repositories",
            )
        elif "rhel" in os_id_like:
            operations.server.dnf.upgrade(
                name="Upgrade dnf repositories",
            )
        elif "arch" in os_id_like:
            operations.server.pacman.upgrade(
                name="Upgrade pacman repositories",
            )
        else:
            raise DeployError(f"Unsupported OS: {os_id} {os_id_like}")
    else:
        if os_id == "alpine":
            operations.server.apk.upgrade(
                name="Upgrade apk repositories",
            )
        elif os_id == "freebsd":
            # TODO: Add freebsd-update install operation once released because it will require a reboot

            # TODO: Add pkg upgrade operation once released
            operations.server.shell(
                name="Run pkg upgrade",
                commands=["pkg upgrade"],
            )
        else:
            raise DeployError(f"Unsupported OS: {os_id} {os_id_like}")
