import json
import logging
from datetime import date, datetime

from infraninja.deploys.info_fetch.custom_facts import (
    CPUInfo,
    DiskInfo,
    MemInfo,
    NetworkInfo,
    OsRelease,
)
from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.server import (
    Groups,
    Hostname,
    KernelModules,
    LinuxName,
    Mounts,
    Os,
    SecurityLimits,
    Selinux,
    Sysctl,
    Users,
)

logger = logging.getLogger("pyinfra")


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""

    def default(self, o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        return super().default(o)


def serialize_fact_safely(fact_data):
    """Safely serialize fact data, converting datetime objects to strings"""
    if fact_data is None:
        return None

    # If it's already a string, return as-is
    if isinstance(fact_data, str):
        return fact_data

    # If it's a simple type, return as-is
    if isinstance(fact_data, (int, float, bool)):
        return fact_data

    # If it's a datetime, convert to ISO string
    if isinstance(fact_data, (datetime, date)):
        return fact_data.isoformat()

    # If it's a list or dict, try to serialize it with our custom encoder
    try:
        return json.loads(json.dumps(fact_data, cls=DateTimeEncoder))
    except (TypeError, ValueError):
        # If serialization fails, convert to string
        return str(fact_data)


def get_fact_safely(fact_type, **kwargs):
    """Helper function to safely get facts and serialize them"""
    try:
        fact_data = host.get_fact(fact_type, **kwargs)
        return serialize_fact_safely(fact_data)
    except Exception as e:
        print(f"Failed to get fact {fact_type.__name__}: {str(e)}")
        return None


@deploy("Fetch Server Information")
def deploy_info_fetch():
    """
    Collect comprehensive server information and return as JSON.

    This deploy gathers system facts and returns them in a structured format
    that can be parsed and stored by Jinn.

    Returns:
        JSON string containing:
        - facts: Dictionary of all collected facts
        - display: Human-readable formatted string of key facts
    """

    # Get system information safely
    facts_to_collect = {
        "os_info": (Os, {}),
        "hostname": (Hostname, {}),
        "linux_name": (LinuxName, {}),
        "mem_usage": (MemInfo, {"measurement": "gb", "occurence": "usage"}),
        "mem_total": (MemInfo, {"measurement": "gb", "occurence": "total"}),
        "cpu_usage": (CPUInfo, {"measurement": "percent", "occurence": "usage"}),
        "cpu_mhz": (CPUInfo, {"measurement": "mhz", "occurence": "total"}),
        "cpu_load": (CPUInfo, {"measurement": "load", "occurence": "usage"}),
        "cpu_cores": (CPUInfo, {"measurement": "cores", "occurence": "total"}),
        "disk_usage": (DiskInfo, {"measurement": "percent", "occurence": "usage"}),
        "disk_total": (DiskInfo, {"measurement": "gb", "occurence": "total"}),
        "disk_usage_gb": (DiskInfo, {"measurement": "gb", "occurence": "usage"}),
        "os_release": (OsRelease, {}),
        "mounts": (Mounts, {}),
        "groups": (Groups, {}),
        "kernel_modules": (KernelModules, {}),
        "sysctl": (Sysctl, {}),
        "users": (Users, {}),
        "selinux": (Selinux, {}),
        "security_limits": (SecurityLimits, {}),
        "network_usage": (NetworkInfo, {}),
        "network_usage_interfaces": (NetworkInfo, {"occurence": "interfaces"}),
        "network_usage_ip_info": (NetworkInfo, {"occurence": "ip_info"}),
    }

    # Collect all facts safely
    collected_facts = {}
    for fact_name, (fact_type, kwargs) in facts_to_collect.items():
        collected_facts[fact_name] = get_fact_safely(fact_type, **kwargs)

    # Process CPU load status
    load_status = "Unset"
    if collected_facts["cpu_load"] and collected_facts["cpu_cores"]:
        try:
            load_1 = float(json.loads(collected_facts["cpu_load"])[0])
            load_status = (
                "Overloaded"
                if load_1 > float(collected_facts["cpu_cores"])
                else "Not Overloaded"
            )
        except (json.JSONDecodeError, IndexError) as e:
            print(f"Failed to process CPU load: {str(e)}")

    # Process network usage
    network_received = network_transmitted = 0
    if collected_facts["network_usage"]:
        try:
            network_data = json.loads(collected_facts["network_usage"])
            if isinstance(network_data, list) and len(network_data) >= 2:
                network_received = float(network_data[0]) / 1024
                network_transmitted = float(network_data[1]) / 1024
        except (json.JSONDecodeError, IndexError) as e:
            print(f"Failed to process network usage: {str(e)}")

    # Prepare facts for display
    display_facts = {
        "OS Info": collected_facts["os_info"],
        "OS Release": collected_facts["os_release"].get("pretty_name")
        if collected_facts["os_release"]
        else None,
        "Hostname": collected_facts["hostname"],
        "Linux Name": collected_facts["linux_name"],
        "Memory Usage": f"{collected_facts['mem_usage']}GB"
        if collected_facts["mem_usage"]
        else None,
        "Memory Total": f"{collected_facts['mem_total']}GB"
        if collected_facts["mem_total"]
        else None,
        "CPU Usage": f"{collected_facts['cpu_usage']}%"
        if collected_facts["cpu_usage"]
        else None,
        "CPU MHz": collected_facts["cpu_mhz"],
        "CPU Cores": collected_facts["cpu_cores"],
        "CPU Load Status": load_status,
        "Disk Usage": collected_facts["disk_usage"],
        "Disk Total": collected_facts["disk_total"],
        "Disk Used": collected_facts["disk_usage_gb"],
        "Network Received (kb/s)": network_received,
        "Network Transmitted (kb/s)": network_transmitted,
        "Groups": len(collected_facts["groups"]) if collected_facts["groups"] else None,
        "Users": len(collected_facts["users"]) if collected_facts["users"] else None,
        "Selinux": collected_facts["selinux"],
        "Security Limits": len(collected_facts["security_limits"])
        if collected_facts["security_limits"]
        else None,
        "Mounts": len(collected_facts["mounts"]) if collected_facts["mounts"] else None,
    }

    # Create a beautified string of facts for returning (only non-None values)
    beautified_facts = "\n".join(
        [f"{key}: {value}" for key, value in display_facts.items() if value is not None]
    )

    # Store all collected facts (ensure they're properly serialized)
    serialized_facts = {
        key: serialize_fact_safely(value) for key, value in collected_facts.items()
    }

    # Create result dictionary with both facts and display
    result = {"facts": serialized_facts, "display": beautified_facts}

    logger.warning("INFO_FETCH_RESULT_START")
    logger.warning(json.dumps(result, cls=DateTimeEncoder))
    logger.warning("INFO_FETCH_RESULT_END")

    return result
