import json

from pyinfra.api.facts import FactBase


class OsRelease(FactBase):
    """
    Custom fact to get OS release information by parsing /etc/os-release.
    Returns a dictionary with lowercased keys, plus convenience aliases when present.
    """

    def command(self):
        return "cat /etc/os-release"

    def process(self, output):
        result = {}
        try:
            for raw in output:
                line = (raw or "").strip()
                if not line or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip().lower()
                # Trim surrounding quotes if any
                value = value.strip().strip('"').strip("'")
                result[key] = value

            # Some friendly aliases if available
            if "pretty_name" in result:
                result["pretty_name"] = result["pretty_name"]
            if "name" in result:
                result["name"] = result["name"]
            if "version" in result:
                result["version"] = result["version"]
        except Exception as e:
            print(f"Failed to parse /etc/os-release: {e}")
        return result


class MemInfo(FactBase):
    """
    Returns the memory usage.
    """

    def command(self, measurement="percent", occurence="usage"):
        valid_measurements = {"percent", "gb", "mb"}
        valid_occurences = {"usage", "total"}

        if measurement not in valid_measurements:
            raise ValueError(
                f"Invalid measurement: {measurement}. Expected one of {valid_measurements}."
            )
        if occurence not in valid_occurences:
            raise ValueError(
                f"Invalid occurence: {occurence}. Expected one of {valid_occurences}."
            )

        if occurence == "usage":
            # Get the memory usage percentage or absolute
            operation = "(used/total)*100"

            if measurement == "gb":
                operation = "used/1024/1024"
            elif measurement == "mb":
                operation = "used/1024"
            return f"awk '/MemTotal/ {{{{total=$2}}}} /MemAvailable/ {{{{available=$2}}}} END {{{{used=total-available; printf \"%.2f\\n\", {operation}}}}}' /proc/meminfo"

        elif occurence == "total":
            # Get the total memory
            operation = "$2/1024/1024"
            if measurement == "mb":
                operation = "$2/1024"
            return f"awk '/MemTotal/ {{printf \"%.2f\\n\", {operation}}}' /proc/meminfo"

    def process(self, output):
        try:
            return (output[0]).replace(",", ".")
        except Exception as e:
            print(e)
            return output


class CPUInfo(FactBase):
    """
    Returns the processor usage/info.
    """

    def command(self, occurence="usage", measurement="percent"):
        valid_measurements = {"percent", "mhz", "load", "cores", "time"}
        valid_occurences = {"usage", "total"}

        if measurement not in valid_measurements:
            raise ValueError(
                f"Invalid measurement: {measurement}. Expected one of {valid_measurements}."
            )
        if occurence not in valid_occurences:
            raise ValueError(
                f"Invalid occurence: {occurence}. Expected one of {valid_occurences}."
            )

        if occurence == "usage":
            if measurement == "percent":
                return 'awk -v RS="" \'{printf "%.2f\\n", ($2+$4)*100/($2+$4+$5)}\' /proc/stat'
            elif measurement == "load":
                # Load averages (1, 5, 15 minutes)
                return (
                    'echo "["$(cat /proc/loadavg | awk \'{print $1"| "$2"| "$3}\')"]"'
                )
            elif measurement == "time":
                # CPU time fields: user, nice, system, idle, etc.
                return "cat /proc/stat | grep '^cpu ' | awk '{$1=\"\"; print substr($0,2)}'"

        elif occurence == "total":
            if measurement == "mhz":
                return "cat /proc/cpuinfo | grep \"MHz\" | awk '{print $4}'"
            elif measurement == "cores":
                return "nproc"

    def process(self, output):
        try:
            return (output[0]).replace(",", ".").replace("|", ",")
        except Exception as e:
            print(e)
            return output


class DiskInfo(FactBase):
    """
    Returns the disk usage.
    """

    def command(self, occurence="usage", measurement="percent"):
        valid_occurences = {"usage", "total"}
        valid_measurements = {"percent", "gb", "mb"}

        if occurence not in valid_occurences:
            raise ValueError(
                f"Invalid occurence: {occurence}. Expected one of {valid_occurences}."
            )
        if measurement not in valid_measurements:
            raise ValueError(
                f"Invalid measurement: {measurement}. Expected one of {valid_measurements}."
            )

        if occurence == "usage":
            if measurement == "percent":
                return "df --total --output=pcent | awk 'END{print $1}'"
            elif measurement == "gb":
                return "df --total --block-size=1G | awk '/total/ {print $3\"GB\"}'"
            elif measurement == "mb":
                return "df --total --block-size=1M | awk '/total/ {print $3\"MB\"}'"

        elif occurence == "total":
            if measurement == "gb":
                return "df --total --block-size=1G | awk '/total/ {print $2\"GB\"}'"
            elif measurement == "mb":
                return "df --total --block-size=1M | awk '/total/ {print $2\"MB\"}'"

    def process(self, output):
        try:
            return (output[0]).replace(",", ".")
        except Exception as e:
            print(e)
            return output


class NetworkInfo(FactBase):
    """
    Returns the network usage/details.
    Options:
    - occurence="bandwidth": returns bandwidth info for specified interface
    - occurence="interfaces": returns list of network interfaces
    - occurence="ip_info": returns detailed JSON info about all interfaces
    - occurence="stats": returns network statistics
    """

    def command(self, occurence="bandwidth", interface="lo"):
        self.occurence = occurence
        self.interface = interface

        if occurence == "bandwidth":
            command = f'awk -v iface="{interface}" \'$1 ~ iface {{print "[" $2 "| " $10 "]"}}\' /proc/net/dev'
        elif occurence == "interfaces":
            command = "ls /sys/class/net/"
        elif occurence == "ip_info":
            command = "ip -j addr"
        elif occurence == "stats":
            command = "for iface in $(ls /sys/class/net/); do "
        return command

    def process(self, output):
        try:
            if self.occurence == "bandwidth":
                return output[0].replace(",", ".").replace("|", ",")
            elif self.occurence == "ip_info":
                return json.loads("".join(output))
            else:
                return output
        except Exception as e:
            print(e)
            return output


class PartitionsInfo(FactBase):
    """
    Returns the partitions information in either JSON or simple format.
    """

    def command(self, format="simple", include_loop=False):
        self.format = format
        self.include_loop = include_loop

        valid_formats = {"simple", "json"}
        if format not in valid_formats:
            raise ValueError(
                f"Invalid format: {format}. Expected one of {valid_formats}."
            )

        return "lsblk -J -o NAME,SIZE,MOUNTPOINTS,MAJ:MIN,RM,RO,FSUSE%"

    def get_mountpoint(self, device):
        mountpoints = device.get("mountpoints", [])
        if mountpoints and mountpoints[0] is not None:
            return mountpoints[0]
        return "-"

    def get_fsuse(self, device):
        fsuse = device.get("fsuse%", "-")
        return fsuse if fsuse is not None else "-"

    def process(self, output):
        try:
            json_data = json.loads("".join(output))

            if self.format == "json":
                return json_data

            result = []
            result.append(
                "NAME         MAJ:MIN   RM  RO  SIZE     MOUNTPOINT                   USE%"
            )
            result.append("\u2500" * 85)

            for device in json_data["blockdevices"]:
                # Skip loop devices if not included
                if not self.include_loop and device["name"].startswith("loop"):
                    continue

                mountpoint = self.get_mountpoint(device)
                result.append(
                    f"{device['name']:<14}"
                    f"{device.get('maj:min', '-'):<9}"
                    f"{device.get('rm', '0'):<4}"
                    f"{device.get('ro', '0'):<4}"
                    f"{device['size']:<8}"
                    f"{mountpoint:<28}"
                    f"|{self.get_fsuse(device)}"
                )

                if "children" in device:
                    for child in device["children"]:
                        mountpoint = self.get_mountpoint(child)
                        result.append(
                            f"\u2514\u2500{child['name']:<12}"
                            f"{child.get('maj:min', '-'):<9}"
                            f"{child.get('rm', '0'):<4}"
                            f"{child.get('ro', '0'):<4}"
                            f"{child['size']:<8}"
                            f"{mountpoint:<28}"
                            f"|{self.get_fsuse(child)}"
                        )

            return "\n".join(result)

        except Exception as e:
            print(f"Error processing partition info: {e}")
            return None
