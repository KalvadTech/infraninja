from pyinfra.api.deploy import deploy
from pyinfra.operations import server
from pyinfra.facts.server import Command
from pyinfra.context import host


def check_reboot_required(host):
    """
    Check if a system reboot is required by examining various indicators.

    On Linux systems:
    - Checks for /var/run/reboot-required and /var/run/reboot-required.pkgs
    - On Alpine Linux, compares installed kernel with running kernel
    """
    # Shell command to check if reboot is required
    command = """
    # Get OS type
    OS_TYPE=$(uname -s)

    if [ "$OS_TYPE" = "Linux" ]; then
        # Check if it's Alpine Linux
        if [ -f /etc/alpine-release ]; then
            RUNNING_KERNEL=$(uname -r)
            INSTALLED_KERNEL=$(ls -1 /lib/modules | sort -V | tail -n1)
            if [ "$RUNNING_KERNEL" != "$INSTALLED_KERNEL" ]; then
                echo "reboot_required"
                exit 0
            fi
        fi

        # Check for standard Linux reboot required files
        if [ -f /var/run/reboot-required ] || [ -f /var/run/reboot-required.pkgs ] || [ -f /var/run/reboot-needed ]; then
            echo "reboot_required"
            exit 0
        fi

        # Check for pending package updates on systems using pacman (Arch Linux)
        if command -v pacman >/dev/null 2>&1; then
            if [ "$(checkupdates 2>/dev/null | wc -l)" -gt 0 ]; then
                echo "reboot_required"
                exit 0
            fi
        fi

        # Check for pending updates on systems using dnf (Fedora/RHEL)
        if command -v dnf >/dev/null 2>&1; then
            dnf needs-restarting -r >/dev/null 2>&1
            if [ $? -eq 1 ]; then
                echo "reboot_required"
                exit 0
            fi
        fi

        # Check for pending updates on systems using apt (Debian/Ubuntu)
        if command -v apt >/dev/null 2>&1; then
            if [ -f /var/run/reboot-required ]; then
                echo "reboot_required"
                exit 0
            fi
        fi
    fi

    echo "no_reboot_required"
    """

    stdout = host.get_fact(Command, command)

    # Ensure stdout is a list for consistent handling
    if isinstance(stdout, str):
        stdout = stdout.splitlines()

    if stdout and stdout[0].strip() == "reboot_required":
        return True

    return False


@deploy("Reboot the system")
def reboot_system(need_reboot=None, force_reboot=False, skip_reboot_check=False):
    """
    Reboot a system if necessary.

    Args:
        need_reboot: If True, always reboot. If False, never reboot.
                    If None, check if reboot is required.
        force_reboot: If True, override need_reboot and always reboot.
        skip_reboot_check: If True, skip the reboot check and use need_reboot value directly.
    """
    if force_reboot:
        need_reboot = True

    if need_reboot is None and not skip_reboot_check:
        # Check if reboot is required
        need_reboot = check_reboot_required(host)

    if need_reboot is True:
        server.reboot(
            name="Reboot the system",
            delay=90,
            interval=10,
        )
