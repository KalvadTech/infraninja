from pyinfra.api.deploy import deploy
from pyinfra.operations import server


@deploy("ARP Poisoning Protection Rules for Alpine")
def arp_poisoning_protectio():
    """
    Enable ARP poisoning protection through sysctl configuration.

    Configures kernel parameters to protect against ARP spoofing attacks
    by enabling strict ARP response handling and announcement policies.
    Settings are made persistent across reboots.

    .. code:: python

        from infraninja.security.common.arp_poisoning_protection import arp_poisoning_protectio
        arp_poisoning_protectio()

    :returns: None
    :rtype: None
    """
    # Enable ARP spoofing protection
    server.sysctl(
        name="Enable ARP spoofing protection (arp_ignore)",
        key="net.ipv4.conf.all.arp_ignore",
        value=1,
        persist=True,
    )
    server.sysctl(
        name="Enable ARP spoofing protection (arp_announce)",
        key="net.ipv4.conf.all.arp_announce",
        value=2,
        persist=True,
    )
