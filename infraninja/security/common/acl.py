from pyinfra.api import deploy
from pyinfra.operations import server
from pyinfra import host
from pyinfra.facts.files import File

@deploy("Set ACL")
def acl_setup():
    # Check if setfacl is available
    if not server.shell(
        name="Check if setfacl exists",
        commands=["command -v setfacl"],
        _ignore_errors=True
    ):
        host.noop("Skip ACL setup - setfacl not found")
        return

    # Define the ACL paths and rules
    ACL_PATHS = {
        "/etc/fail2ban": "u:root:rwx",
        "/var/log/lynis-report.dat": "u:root:r",
        "/etc/audit/audit.rules": "g:root:rwx",
        "/etc/suricata/suricata.yaml": "u:root:rwx",
        "/var/log/suricata": "u:root:rwx",
        "/etc/iptables/rules.v4": "u:root:rwx",
        "/etc/ssh/sshd_config": "u:root:rw",
        "/etc/cron.d": "u:root:rwx",
        "/etc/rsyslog.conf": "u:root:rw",
        "/etc/modprobe.d": "u:root:rwx",
        "/etc/udev/rules.d": "u:root:rwx",
        "/etc/fstab": "u:root:rw",
    }

    for path, acl_rule in ACL_PATHS.items():
        # Check if path exists before attempting to set ACL
        if host.get_fact(File, path=path) is None:
            host.noop(f"Skip ACL for {path} - path does not exist")
            continue

        # Attempt to set the ACL
        try:
            server.shell(
                name=f"Set ACL for {path}",
                commands=[f"setfacl -m {acl_rule} {path}"],
            )
        except Exception as e:
            host.noop(f"Failed to set ACL for {path} - {str(e)}")
    return True
