"""
    Monitor module for SSH connections
    Author: Wolf Paulus <wolf@paulus.com>
"""
import os
from abc import abstractmethod
from paramiko import SSHClient, AutoAddPolicy, SSHConfig
from log import logger

class Connection:
    """ Base class for SSH connection """

    def __init__(self, hostname: str) -> None:
        """ Initialize the Connection class with a hostname """
        self.hostname = hostname
        self.client = SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(AutoAddPolicy())
        self.config = SSHConfig()
        self.config.parse(open(os.path.expanduser("~/.ssh/config")))
        user_config = self.config.lookup(hostname)
        key_filename = os.path.expanduser(user_config["identityfile"][0])
        try:
            self.client.connect(
                hostname=user_config["hostname"],
                username=user_config["user"],
                port=int(user_config["port"]),
                key_filename=key_filename,
                timeout=5
            )
        except OSError as err:
            logger.error(f"Error connecting to {hostname}: {err}")
            self.client = None

    def close(self) -> None:
        """ Close the SSH connection """
        if self.client is not None:
            self.client.close()
            self.client = None


class Monitor:
    """ Base class for SSH connection monitoring """

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
            return None

    def __init__(self, client: SSHClient, cmd: str, values: list[int]) -> None:
        """ Initialize the Monitor class with a hostname """
        self.client = client
        self.cmd = cmd
        self.values = values

    @abstractmethod
    def probe(self) -> int:
        """ Probe the system for information """
        ...

    @staticmethod
    def match(v: float | int, values: list[int]) -> int:
        """ Match the value with the corresponding color index"""
        if v < 0:
            return -1
        elif v <= values[0]:
            return 0
        elif v <= values[1] - (values[1] - values[0]) / 2:
            return 1
        elif v <= values[1]:
            return 2
        elif v <= values[2] - (values[2] - values[1]) / 2:
            return 3
        elif v <= values[2]:
            return 4
        else:
            return 5


class CpuTemperature(Monitor):
    """ Monitor class for CPU temperature """

    def probe(self) -> int:
        """ Probe the CPU temperature in Celsius """
        stdin, stdout, stderr = self.client.exec_command(self.cmd)
        temp = int(stdout.read().decode()) / 1000
        logger.debug(f"CPU temperature: {temp}°C")
        return Monitor.match(temp, self.values)


class CpuUsage(Monitor):
    def probe(self) -> int:
        """ Probe the CPU Usage in percent """
        stdin, stdout, stderr = self.client.exec_command(self.cmd)
        usage = round(float(stdout.read().decode()) + 0.5)  # Round to nearest integer
        logger.debug(f"CPU usage: {usage} %")
        return Monitor.match(usage, self.values)

class MemoryUsage(Monitor):
    """ Monitor class for Memory usage
    Expect something like:
                      total        used        free      shared  buff/cache   available
        Mem:       16425908      812996    11896784      142728     3716128    15249844
        Swap:      11956140           0    11956140
        u     = x
        total = 100
    """
    def probe(self) -> int:
        """ Probe the Memory """
        stdin, stdout, stderr = self.client.exec_command(self.cmd)
        texts = stdout.read().decode().split("\n")
        if len(texts) < 3:
            logger.error("Memory usage information is not available.")
            return -1
        total, used = int(texts[1].split()[1]), int(texts[1].split()[2])
        usage = round(used * 100 / total + 0.5)  # Round to nearest integer
        logger.debug(f"Memory usage: {usage} %")
        return Monitor.match(usage, self.values)

class DiskUsage(Monitor):
    """ Monitor class for Disk usage
    Expect something like:
        Filesystem     1K-blocks    Used Available Use% Mounted on
        /dev/mmcblk0p2  14719576 3318572  10753180  24% /
    """
    def probe(self) -> int:
        """ Probe the Disk usage """
        stdin, stdout, stderr = self.client.exec_command(self.cmd)
        texts = stdout.read().decode().split("\n")
        if len(texts) < 2:
            logger.error("Disk usage information is not available.")
            return -1
        usage = int(texts[1].split()[-2][:-1])  # Get the second last value (Used)
        logger.debug(f"Disk usage: {usage} %")
        return Monitor.match(usage, self.values)

if __name__ == "__main__":
    v1 = [50, 65, 80]
    v2 = [60, 70, 80]
    cmd1 = "cat /sys/class/thermal/thermal_zone2/temp"
    cmd2 = "cat /sys/class/thermal/thermal_zone0/temp"
    cmd3 = 'mpstat -P ALL 1 1 | awk \'$1 == "Average:" && $2 == "all" { print 100 - $NF }\''

    conn = Connection("alpha")
    if conn.client:
        monitor = CpuTemperature(conn.client, cmd1, v1)
        print(monitor.probe())
        monitor = CpuUsage(conn.client, cmd3, v1)
        print(monitor.probe())
        conn.close()
    conn = Connection("beta")
    if conn.client:
        monitor = CpuTemperature(conn.client, cmd1, v1)
        print(monitor.probe())
        monitor = CpuUsage(conn.client, cmd3, v1)
        print(monitor.probe())
        conn.close()
    conn = Connection("apollo")
    if conn.client:
        monitor = CpuTemperature(conn.client, cmd2, v2)
        print(monitor.probe())
        monitor = CpuUsage(conn.client, cmd3, v1)
        print(monitor.probe())
        conn.close()
    conn = Connection("artemis")
    if conn.client:
        monitor = CpuTemperature(conn.client, cmd2, v2)
        print(monitor.probe())
        monitor = CpuUsage(conn.client, cmd3, v1)
        print(monitor.probe())
        conn.close()
