from pyinfra.api.deploy import deploy
from pyinfra.operations import server


@deploy("ARP Poisoning Protection Rules for Alpine")
def arp_poisoning_protectio():
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
