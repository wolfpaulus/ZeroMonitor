"""
Monitor module for SSH connections
Author: Wolf Paulus <wolf@paulus.com>
"""

import os
from abc import abstractmethod
from paramiko import SSHClient, AutoAddPolicy, SSHConfig
from log import logger


class Connection:
    """Base class for SSH connection
    works as a context manager to ensure proper connection handling
    """

    def __init__(self, hostname: str) -> None:
        """Initialize the Connection class with a hostname"""
        self.hostname = hostname
        self.client = SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(AutoAddPolicy())
        self.config = SSHConfig()
        self.config.parse(open(os.path.expanduser("~/.ssh/config")))

    def connect(self) -> None:
        """Establish the SSH connection"""
        user_config = self.config.lookup(self.hostname)
        key_filename = os.path.expanduser(user_config["identityfile"][0])
        try:
            self.client.connect(
                hostname=user_config["hostname"],
                username=user_config["user"],
                port=int(user_config["port"]),
                key_filename=key_filename,
                timeout=10,
            )
        except OSError as err:
            logger.error(f"Error connecting to {self.hostname}: {err}")
            self.client = None

    def close(self) -> None:
        """Close the SSH connection"""
        if self.client is not None:
            self.client.close()
            self.client = None

    def __enter__(self):
        self.connect()
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class Monitor:
    """Base class for SSH connection monitoring"""

    @classmethod
    def create_instance(cls, class_name_str, *args, **kwargs):
        """
        Instantiates a sensor given its name as a string.
        Args:
            class_name_str: The name of the class as a string.
            *args: Positional arguments to pass to the constructor.
            **kwargs: Keyword arguments to pass to the constructor.
        Returns:
            An instance of the sensor, or None if the class name is not found.
        """
        try:
            cls_ = globals()[class_name_str]
            instance = cls_(*args, **kwargs)
            return instance
        except KeyError:
            logger.error(f"Monitor class '{class_name_str}' not found.")
            return None

    def __init__(self, client: SSHClient, cmd: str, values: list[int]) -> None:
        """Initialize the Monitor class with a hostname
        client, ssh client object
        cmd, command to execute on the remote host
        values, list of tree values: eg. low, medium, high
        """
        self.client = client
        self.cmd = cmd
        self.values = values

    @abstractmethod
    def probe(self) -> (int, int):
        """Probe the system for information
        Returns: tuple of (measured value, color_code based on thresholds)"""
        ...

    @staticmethod
    def color_code(v: int | int, values: list[int]) -> int:
        """Match the value with the corresponding color index
        Args: v: the value to match
            values: list of threshold values
        Returns: int, the index of the color corresponding to the value
        0 to 5, where 0 is below or at the first threshold and 5 is above the third threshold.
        -1 is an error case, i.e. the given value was negative.
        """
        if v < 0:
            return -1  # Error case, no value available
        elif v <= values[0]:
            return 0  # Below or at the first threshold
        elif v <= values[1] - (values[1] - values[0]) / 2:
            return 1  # Above first threshold but way below second threshold
        elif v <= values[1]:
            return 2  # Below or at the second threshold
        elif v <= values[2] - (values[2] - values[1]) / 2:
            return 3  # Above second threshold but way below third threshold
        elif v <= values[2]:
            return 4  # Below or at the third threshold
        else:
            return 5  # Above the third threshold.


class CpuTemperature(Monitor):
    """Monitor class for CPU temperature
    expected stdout content: something like:
    53692
    """

    def probe(self) -> (int, int):
        """Probe the CPU temperature in Celsius"""
        try:
            stdin, stdout, stderr = self.client.exec_command(self.cmd)
            temperature = round(int(stdout.read().decode()) / 1000)
            logger.debug(f"CPU temperature: {temperature}°C")
            return temperature, Monitor.color_code(temperature, self.values)
        except ValueError as e:
            logger.error(f"Error reading CPU temperature: {e}")
            return -1, -1


class CpuUsage(Monitor):
    """Monitor class for CPU usage
    expected stdout content: something like:
    2.78
    """

    def probe(self) -> (int, int):
        """Probe the CPU Usage in percent"""
        try:
            stdin, stdout, stderr = self.client.exec_command(self.cmd)
            usage = round(float(stdout.read().decode()) + 0.5)
            logger.debug(f"CPU usage: {usage} %")
            return usage, Monitor.color_code(usage, self.values)
        except ValueError as e:
            logger.error(f"Error reading CPU usage: {e}")
            return -1, -1


class MemoryUsage(Monitor):
    """Monitor class for Memory usage
    expected stdout content: something like:
                   total        used        free      shared  buff/cache   available
    Mem:          419228      192524       47784        3068      191792      226704
    Swap:              0           0           0
    """

    def probe(self) -> (int, int):
        """Probe the Memory"""
        try:
            stdin, stdout, stderr = self.client.exec_command(self.cmd)
            texts = stdout.read().decode().split("\n")
            if len(texts) < 3:
                logger.warn("Memory usage information is not available.\n{texts}")
                return -1, -1
            total, used = int(texts[1].split()[1]), int(texts[1].split()[2])
            usage = round(used * 100 / total)  # Round to nearest integer
            logger.debug(f"Memory usage: {usage} %")
            return usage, Monitor.color_code(usage, self.values)
        except ValueError as e:
            logger.error(f"Error reading Memory usage: {e}")
            return -1, -1


class DiskUsage(Monitor):
    """Monitor class for Disk usage
    expected stdout content: something like:
    Filesystem     1K-blocks    Used Available Use% Mounted on
    /dev/mmcblk0p2  14719576 3318572  10753180  24% /
    """

    def probe(self) -> (int, int):
        """Probe the Disk usage"""
        try:
            stdin, stdout, stderr = self.client.exec_command(self.cmd)
            texts = stdout.read().decode().split("\n")
            if len(texts) < 2:
                logger.warn("Disk usage information is not available.\n{texts}")
                return -1, -1
            usage = int(texts[1].split()[-2][:-1])  # Get the second last value (Used)
            logger.debug(f"Disk usage: {usage} %")
            return usage, Monitor.color_code(usage, self.values)
        except ValueError as e:
            logger.error(f"Error reading Disk usage: {e}")
            return -1, -1
