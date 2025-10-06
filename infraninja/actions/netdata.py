"""Netdata monitoring deployment action"""

from importlib.resources import files as resource_files
from typing import Any, Dict

from pyinfra import host
from pyinfra.operations import files, server

from infraninja.actions.base import Action

DEFAULTS = {
    "claim_token": "XXXXX",
    "claim_rooms": "XXXXX",
    "claim_url": "https://app.netdata.cloud",
    "reclaim": False,
    "dbengine_multihost_disk_space": 2048,
    "stream": {
        "enabled": False,
        "destination": "streaming.netdata.cloud",
        "api_key": "XXXXX",
    },
}


class NetdataAction(Action):
    """
    Deploy Netdata real-time monitoring and observability platform.

    Installs and configures Netdata for comprehensive system monitoring,
    metrics collection, and alerting capabilities.

    Example:
        .. code:: python

            from infraninja.actions.netdata import NetdataAction

            action = NetdataAction()
            action.execute()
    """

    slug = "deploy-netdata"
    name = {
        "en": "Deploy Netdata Monitoring",
        "ar": "نشر مراقبة Netdata",
        "fr": "Déployer la surveillance Netdata",
    }
    tags = ["monitoring", "observability", "metrics", "alerting"]
    category = "monitoring"
    color = "#00AB44"
    logo = "fa-chart-line"
    description = {
        "en": "Deploy Netdata real-time monitoring platform for comprehensive system observability and performance metrics",
        "ar": "نشر منصة مراقبة Netdata في الوقت الفعلي لرصد النظام الشامل ومقاييس الأداء",
        "fr": "Déployer la plateforme de surveillance en temps réel Netdata pour l'observabilité complète du système",
    }
    os_available = ["ubuntu", "debian", "alpine", "freebsd", "rhel", "centos", "fedora", "arch"]

    def execute(self, data_defaults: Dict[str, Any] = None) -> Any:
        """
        Execute Netdata deployment.

        Downloads and installs Netdata monitoring system, configures it
        with templates, and ensures the service is running.

        Args:
            data_defaults: Default data configuration (default: DEFAULTS)

        Returns:
            Result of the deployment operation
        """
        if data_defaults is None:
            data_defaults = DEFAULTS

        # Merge data_defaults with host.data
        for key, value in data_defaults.items():
            if key not in host.data:
                host.data[key] = value

        # Download the installation script
        files.download(
            name="Download the installation script",
            src="https://my-netdata.io/kickstart.sh",
            dest="~/kickstart.sh",
            mode="+x",
        )

        # Install Netdata
        server.shell(
            name="Install Netdata",
            commands=["~/kickstart.sh --dont-wait"],
        )

        # Cleanup installation script
        files.file(
            name="Cleanup installation script",
            path="~/kickstart.sh",
            present=False,
        )

        # Get template path using importlib.resources
        template_path = resource_files("infraninja.templates").joinpath("netdata.conf.j2")

        netdata_config = files.template(
            name="Template the netdata.conf file",
            src=str(template_path),
            dest="/etc/netdata/netdata.conf",
            user="root",
            group="root",
            mode="644",
        )

        # Restart Netdata service
        server.service(
            name="Restart Netdata",
            service="netdata",
            running=True,
            restarted=True,
            enabled=True,
            _if=netdata_config.changed,
        )
