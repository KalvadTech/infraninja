from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.server import RebootRequired
from pyinfra.operations import server


@deploy("Reboot the system")
def reboot_system(need_reboot=None, force_reboot=False, skip_reboot_check=False):
    """
    Reboot a system if necessary based on various conditions.

    Provides intelligent system reboot functionality with multiple options
    for controlling when and whether to reboot. Can automatically detect
    if a reboot is needed or use manual override parameters.

    .. code:: python

        from infraninja.security.common.reboot_system import reboot_system

        # Auto-detect if reboot is needed
        reboot_system()

        # Force reboot regardless of conditions
        reboot_system(force_reboot=True)

        # Never reboot even if needed
        reboot_system(need_reboot=False)

    :param need_reboot: If True, always reboot. If False, never reboot. If None, check if reboot is required.
    :type need_reboot: bool, optional
    :param force_reboot: If True, override need_reboot and always reboot
    :type force_reboot: bool
    :param skip_reboot_check: If True, skip the reboot check and use need_reboot value directly
    :type skip_reboot_check: bool
    :returns: None
    :rtype: None
    """
    if force_reboot:
        need_reboot = True

    if need_reboot is None and not skip_reboot_check:
        # Check if reboot is required using pyinfra's built-in fact
        need_reboot = host.get_fact(RebootRequired)

    if need_reboot is True:
        server.reboot(
            name="Reboot the system",
            delay=90,
            interval=10,
        )
