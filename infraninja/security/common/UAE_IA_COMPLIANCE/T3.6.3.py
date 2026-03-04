from pyinfra.api import deploy
from pyinfra.operations import files


@deploy("T3.6.3: Log privileged operations and unauthorized access attempts")
def t3_6_3():  # noqa: N802
    # T3.6.3: Log privileged operations and unauthorized access attempts
    files.line(
        name="Log privileged operations and unauthorized access",
        path="/etc/audit/audit.rules",
        line="-w /sbin/ifconfig -p x -k network",
    )
