from pyinfra.api import deploy
from pyinfra.operations import server
from pyinfra import host
from pyinfra.facts.files import File
from pyinfra.facts.server import LinuxDistribution


@deploy("Set ACL")
def acl_setup():
    # Get OS information
    distro = host.get_fact(LinuxDistribution)
    os_name = str(distro.get("name", "")).lower() if distro else ""
    is_freebsd = "freebsd" in os_name
    
    # For FreeBSD, check if the filesystem supports ACLs
    if is_freebsd:
        # Ensure acl_package is installed
        server.shell(
            name="Install ACL package on FreeBSD if needed",
            commands=["pkg install -y acl"],
            _ignore_errors=True,
        )
        
        # Check mount points for ACL support
        mount_check = server.shell(
            name="Check for ACL-enabled filesystems",
            commands=["mount | grep -E '(acls|NFS4ACLs)'"],
            _ignore_errors=True,
        )
        if not mount_check:
            host.noop("FreeBSD filesystems don't appear to have ACLs enabled. Skipping ACL setup.")
            return
    else:
        # Check if setfacl is available on Linux systems
        if not server.shell(
            name="Check if setfacl exists",
            commands=["command -v setfacl"],
            _ignore_errors=True,
        ):
            # Try to install ACL utilities on Linux
            if os_name in ["ubuntu", "debian"]:
                server.shell(
                    name="Install ACL utilities",
                    commands=["apt-get update && apt-get install -y acl"],
                            _ignore_errors=True,
                )
            elif os_name in ["centos", "rhel", "fedora"]:
                server.shell(
                    name="Install ACL utilities",
                    commands=["yum install -y acl"],
                            _ignore_errors=True,
                )
            elif os_name == "alpine":
                server.shell(
                    name="Install ACL utilities",
                    commands=["apk add acl"],
                            _ignore_errors=True,
                )
            
            # Check again if setfacl is now available
            if not server.shell(
                name="Verify setfacl exists after installation",
                commands=["command -v setfacl"],
                _ignore_errors=True,
                ):
                host.noop("Skip ACL setup - setfacl not available and could not be installed")
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
    
    # FreeBSD-specific paths replacements
    if is_freebsd:
        freebsd_paths = {
            "/etc/fail2ban": "/usr/local/etc/fail2ban",
            "/etc/ssh/sshd_config": "/etc/ssh/sshd_config",
            "/etc/cron.d": "/etc/cron.d",
            "/etc/fstab": "/etc/fstab",
            # Add more FreeBSD-specific path conversions as needed
        }
        
        # Create new paths dictionary with FreeBSD paths
        fbsd_acl_paths = {}
        for path, acl_rule in ACL_PATHS.items():
            if path in freebsd_paths and freebsd_paths[path]:
                fbsd_acl_paths[freebsd_paths[path]] = acl_rule
        
        ACL_PATHS = fbsd_acl_paths

    for path, acl_rule in ACL_PATHS.items():
        # Check if path exists before attempting to set ACL
        if host.get_fact(File, path=path) is None:
            host.noop(f"Skip ACL for {path} - path does not exist")
            continue

        # Attempt to set the ACL
        try:
            if is_freebsd:
                # FreeBSD uses a different ACL syntax
                user_or_group, user, perms = acl_rule.split(":")
                
                if user_or_group == "u":
                    acl_type = "user"
                elif user_or_group == "g":
                    acl_type = "group"
                else:
                    acl_type = user_or_group
                
                # Check if filesystem is UFS with SUJ or ZFS
                fs_check = server.shell(
                    name=f"Check filesystem type for {path}",
                    commands=[f"df -T {path} | grep -E '(ufs|zfs)'"],
                    _ignore_errors=True,
                        )
                
                if fs_check:
                    server.shell(
                        name=f"Set ACL for {path} on FreeBSD",
                        commands=[f"setfacl -m {acl_type}:{user}:{perms} {path}"],
                        _ignore_errors=True,
                                )
                else:
                    # Fallback to traditional permissions for non-ACL filesystems
                    if user == "root":
                        perm_map = {"r": "4", "w": "2", "x": "1"}
                        perm_value = sum(int(perm_map.get(p, "0")) for p in perms)
                        
                        if user_or_group == "u":
                            # Set user permissions using chmod
                            server.shell(
                                name=f"Set permissions for {path} using chmod",
                                commands=[f"chmod u={perms} {path}"],
                                _ignore_errors=True,
                                                )
                        elif user_or_group == "g":
                            # Set group permissions using chmod
                            server.shell(
                                name=f"Set permissions for {path} using chmod",
                                commands=[f"chmod g={perms} {path}"],
                                _ignore_errors=True,
                                                )
            else:
                # Linux systems
                server.shell(
                    name=f"Set ACL for {path}",
                    commands=[f"setfacl -m {acl_rule} {path}"],
                    _ignore_errors=True,
                        )
        except Exception as e:
            host.noop(f"Failed to set ACL for {path} - {str(e)}")
    
    return True
