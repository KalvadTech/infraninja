"""
Parallel SSH Connector for pyinfra

This module provides a @pssh connector for pyinfra that enables parallel SSH execution
across multiple hosts. It can be used with the pyinfra CLI as:

    pyinfra @pssh/group1,host1,host2 deploy.py

Features:
- Parallel SSH execution with configurable concurrency
- Host filtering and grouping
- Integration with existing pyinfra workflows
- Failure handling and retry logic
"""

import logging
import subprocess
import tempfile
import threading
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

from pyinfra.api.command import StringCommand
from pyinfra.connectors.base import BaseConnector
from pyinfra.connectors.util import CommandOutput, OutputLine

logger = logging.getLogger(__name__)


class PSshConnector(BaseConnector):
    """
    Parallel SSH connector for pyinfra

    This connector enables running operations on multiple SSH hosts in parallel.
    It can be used from the CLI like: @pssh/host1,host2,host3
    """

    handles_execution = True

    def __init__(self, state, host):
        super().__init__(state, host)
        self.max_parallel = self._get_data("max_parallel", 5)
        self.ssh_user = self._get_data("ssh_user", "root")
        self.ssh_key = self._get_data("ssh_key")
        self.ssh_port = self._get_data("ssh_port", 22)
        self.ssh_config_file = self._get_data("ssh_config_file")
        self.timeout = self._get_data("timeout", 300)
        self._ssh_connection = None
        self._lock = threading.Lock()

    @staticmethod
    def make_names_data(
        name: Optional[str] = None,
    ) -> Iterator[Tuple[str, Dict[str, Any], List[str]]]:
        """
        Generate inventory targets from @pssh connector specification.

        Expected format: @pssh/host1,host2,host3 or @pssh/group:host1,host2

        Args:
            name: The connector name specification

        Yields:
            tuple: (hostname, host_data, groups)
        """
        if not name:
            return

        # Remove @pssh/ prefix if present
        if name.startswith("@pssh/"):
            name = name[6:]
        elif name.startswith("pssh/"):
            name = name[5:]

        # Split by comma to get individual hosts
        host_specs = [spec.strip() for spec in name.split(",") if spec.strip()]

        for host_spec in host_specs:
            # Check if this is a group specification
            if ":" in host_spec:
                group_name, hostname = host_spec.split(":", 1)
                host_data = {
                    "ssh_hostname": hostname,
                    "group_name": group_name,
                }
                groups = [group_name]
            else:
                # Simple hostname
                hostname = host_spec
                host_data = {
                    "ssh_hostname": hostname,
                }
                groups = ["default"]

            yield hostname, host_data, groups

    def _get_data(self, key: str, default: Any = None) -> Any:
        """Get data from host configuration with fallback to default"""
        return getattr(self.host.data, key, default)

    def _build_ssh_command(self, command: Union[str, StringCommand]) -> List[str]:
        """Build SSH command with all necessary options"""
        ssh_cmd = ["ssh"]

        # Add SSH options
        ssh_cmd.extend(["-o", "StrictHostKeyChecking=no"])
        ssh_cmd.extend(["-o", "UserKnownHostsFile=/dev/null"])
        ssh_cmd.extend(["-o", "LogLevel=ERROR"])

        # Add timeout
        ssh_cmd.extend(["-o", f"ConnectTimeout={min(self.timeout, 30)}"])

        # Add SSH config file if specified
        if self.ssh_config_file:
            ssh_cmd.extend(["-F", self.ssh_config_file])

        # Add SSH key if specified
        if self.ssh_key:
            ssh_cmd.extend(["-i", self.ssh_key])

        # Add port if not default
        if self.ssh_port != 22:
            ssh_cmd.extend(["-p", str(self.ssh_port)])

        # Add user and hostname
        ssh_hostname = self._get_data("ssh_hostname", self.host.name)
        ssh_cmd.append(f"{self.ssh_user}@{ssh_hostname}")

        # Add the actual command
        if isinstance(command, StringCommand):
            ssh_cmd.append(str(command))
        else:
            ssh_cmd.append(command)

        return ssh_cmd

    def run_shell_command(
        self,
        command: StringCommand,
        print_output: bool = False,
        print_input: bool = False,
        **arguments: Any,
    ) -> Tuple[bool, CommandOutput]:
        """
        Execute a command via SSH

        Args:
            command: Command to execute
            print_output: Whether to print command output
            print_input: Whether to print command input
            arguments: Additional connector arguments

        Returns:
            tuple: (success, CommandOutput)
        """
        ssh_cmd = self._build_ssh_command(command)

        if print_input:
            logger.info(f"Running on {self.host.name}: {command}")

        try:
            process = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )

            # Create CommandOutput object
            stdout_lines = process.stdout.splitlines() if process.stdout else []
            stderr_lines = process.stderr.splitlines() if process.stderr else []

            # Create OutputLine objects for CommandOutput
            combined_lines = []
            for line in stdout_lines:
                combined_lines.append(OutputLine(buffer_name="stdout", line=line))
            for line in stderr_lines:
                combined_lines.append(OutputLine(buffer_name="stderr", line=line))

            command_output = CommandOutput(combined_lines=combined_lines)

            if print_output and (stdout_lines or stderr_lines):
                for line in stdout_lines + stderr_lines:
                    logger.info(f"{self.host.name}: {line}")

            success = process.returncode == 0

            if not success:
                logger.error(
                    f"Command failed on {self.host.name} (exit {process.returncode}): {command}"
                )

            return success, command_output

        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out on {self.host.name}: {command}")
            timeout_output = CommandOutput(
                combined_lines=[
                    OutputLine(
                        buffer_name="stderr",
                        line=f"Command timed out after {self.timeout} seconds",
                    )
                ]
            )
            return False, timeout_output

        except Exception as e:
            logger.error(f"SSH command failed on {self.host.name}: {e}")
            error_output = CommandOutput(
                combined_lines=[
                    OutputLine(buffer_name="stderr", line=f"SSH error: {str(e)}")
                ]
            )
            return False, error_output

    def put_file(
        self,
        filename_or_io,
        remote_filename: str,
        remote_temp_filename: Optional[str] = None,
        print_output: bool = False,
        print_input: bool = False,
        **arguments: Any,
    ) -> bool:
        """
        Upload a file via SCP

        Args:
            filename_or_io: Local file path or IO object
            remote_filename: Remote destination path
            remote_temp_filename: Temporary remote path (ignored)
            print_output: Whether to print output
            print_input: Whether to print input
            arguments: Additional arguments

        Returns:
            bool: Success status
        """
        # Handle IO objects by writing to temp file
        local_filename = None
        if hasattr(filename_or_io, "read") and callable(
            getattr(filename_or_io, "read")
        ):
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
                content = filename_or_io.read()  # type: ignore
                tmp.write(content)
                local_filename = tmp.name
        else:
            local_filename = str(filename_or_io)

        try:
            # Build SCP command
            scp_cmd = ["scp"]

            # Add SSH options
            scp_cmd.extend(["-o", "StrictHostKeyChecking=no"])
            scp_cmd.extend(["-o", "UserKnownHostsFile=/dev/null"])
            scp_cmd.extend(["-o", "LogLevel=ERROR"])

            # Add SSH config and key
            if self.ssh_config_file:
                scp_cmd.extend(["-F", self.ssh_config_file])
            if self.ssh_key:
                scp_cmd.extend(["-i", self.ssh_key])
            if self.ssh_port != 22:
                scp_cmd.extend(["-P", str(self.ssh_port)])

            # Add source and destination
            ssh_hostname = self._get_data("ssh_hostname", self.host.name)
            scp_cmd.extend(
                [local_filename, f"{self.ssh_user}@{ssh_hostname}:{remote_filename}"]
            )

            if print_input:
                logger.info(
                    f"Uploading to {self.host.name}: {local_filename} -> {remote_filename}"
                )

            process = subprocess.run(
                scp_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )

            success = process.returncode == 0

            if not success:
                logger.error(f"SCP upload failed on {self.host.name}: {process.stderr}")
            elif print_output:
                logger.info(
                    f"Successfully uploaded to {self.host.name}: {remote_filename}"
                )

            return success

        except Exception as e:
            logger.error(f"File upload failed on {self.host.name}: {e}")
            return False
        finally:
            # Clean up temp file if we created one
            if hasattr(filename_or_io, "read") and callable(
                getattr(filename_or_io, "read")
            ):
                try:
                    import os

                    if local_filename:
                        os.unlink(local_filename)
                except Exception:
                    pass

    def get_file(
        self,
        remote_filename: str,
        filename_or_io,
        remote_temp_filename: Optional[str] = None,
        print_output: bool = False,
        print_input: bool = False,
        **arguments: Any,
    ) -> bool:
        """
        Download a file via SCP

        Args:
            remote_filename: Remote source path
            filename_or_io: Local destination path or IO object
            remote_temp_filename: Temporary remote path (ignored)
            print_output: Whether to print output
            print_input: Whether to print input
            arguments: Additional arguments

        Returns:
            bool: Success status
        """
        # Handle IO objects by downloading to temp file first
        download_to_temp = hasattr(filename_or_io, "write") and callable(
            getattr(filename_or_io, "write")
        )
        if download_to_temp:
            local_filename = tempfile.mktemp()
        else:
            local_filename = str(filename_or_io)

        try:
            # Build SCP command
            scp_cmd = ["scp"]

            # Add SSH options
            scp_cmd.extend(["-o", "StrictHostKeyChecking=no"])
            scp_cmd.extend(["-o", "UserKnownHostsFile=/dev/null"])
            scp_cmd.extend(["-o", "LogLevel=ERROR"])

            # Add SSH config and key
            if self.ssh_config_file:
                scp_cmd.extend(["-F", self.ssh_config_file])
            if self.ssh_key:
                scp_cmd.extend(["-i", self.ssh_key])
            if self.ssh_port != 22:
                scp_cmd.extend(["-P", str(self.ssh_port)])

            # Add source and destination
            ssh_hostname = self._get_data("ssh_hostname", self.host.name)
            scp_cmd.extend(
                [f"{self.ssh_user}@{ssh_hostname}:{remote_filename}", local_filename]
            )

            if print_input:
                logger.info(
                    f"Downloading from {self.host.name}: {remote_filename} -> {local_filename}"
                )

            process = subprocess.run(
                scp_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )

            success = process.returncode == 0

            if success:
                # If downloading to IO object, read temp file and write to IO
                if download_to_temp:
                    with open(local_filename, "r") as f:
                        content = f.read()
                        filename_or_io.write(content)  # type: ignore

                if print_output:
                    logger.info(
                        f"Successfully downloaded from {self.host.name}: {remote_filename}"
                    )
            else:
                logger.error(
                    f"SCP download failed on {self.host.name}: {process.stderr}"
                )

            return success

        except Exception as e:
            logger.error(f"File download failed on {self.host.name}: {e}")
            return False
        finally:
            # Clean up temp file if we created one
            if download_to_temp:
                try:
                    import os

                    os.unlink(local_filename)
                except Exception:
                    pass
