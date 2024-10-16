from pyinfra.operations import apt, apk

@deploy('Common System Updates')
def system_update():
    os = host.fact.linux_name

    if os == 'Ubuntu':
        apt.update(name="Update Ubuntu package lists", sudo=True)
        apt.upgrade(name="Upgrade Ubuntu packages", sudo=True)
    elif os == 'Alpine':
        apk.update(name="Update Alpine package lists", sudo=True)
        apk.upgrade(name="Upgrade Alpine packages", sudo=True)
