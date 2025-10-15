"""Netdata monitoring deployment action"""

from importlib.resources import files as resource_files
from typing import Any, Dict

from pyinfra import host
from pyinfra.operations import files, server

from infraninja.actions.base import Action


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
    os_available = [
        "ubuntu",
        "debian",
        "alpine",
        "freebsd",
        "rhel",
        "centos",
        "fedora",
        "arch",
    ]

    def execute(
        self,
        claim_token: str = "XXXXX",
        claim_rooms: str = "XXXXX",
        claim_url: str = "https://app.netdata.cloud",
        reclaim: bool = False,
        dbengine_multihost_disk_space: int = 2048,
        stream_enabled: bool = False,
        stream_destination: str = "streaming.netdata.cloud",
        stream_api_key: str = "XXXXX",
    ) -> Any:
        """
        Execute Netdata deployment.

        Downloads and installs Netdata monitoring system, configures it
        with templates, and ensures the service is running.

        Args:
            claim_token: Netdata Cloud claim token
            claim_rooms: Netdata Cloud rooms to join
            claim_url: Netdata Cloud URL
            reclaim: Whether to reclaim the node
            dbengine_multihost_disk_space: Disk space for multi-host DB engine in MB
            stream_enabled: Whether streaming is enabled
            stream_destination: Streaming destination
            stream_api_key: Streaming API key

        Returns:
            Result of the deployment operation
        """
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
        template_path = resource_files("infraninja.templates").joinpath(
            "netdata.conf.j2"
        )

        netdata_config = files.template(
            name="Template the netdata.conf file",
            src=str(template_path),
            dest="/etc/netdata/netdata.conf",
            user="root",
            group="root",
            mode="644",
            jinja_env_kwargs={
                "claim_token": claim_token,
                "claim_rooms": claim_rooms,
                "claim_url": claim_url,
                "reclaim": reclaim,
                "dbengine_multihost_disk_space": dbengine_multihost_disk_space,
                "stream": {
                    "enabled": stream_enabled,
                    "destination": stream_destination,
                    "api_key": stream_api_key,
                },
            },
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
