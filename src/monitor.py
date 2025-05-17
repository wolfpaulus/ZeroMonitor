"""
    Monitor module for SSH connections
    Author: Wolf Paulus <wolf@paulus.com>
"""
import os
from abc import abstractmethod

from paramiko import SSHClient, AutoAddPolicy, SSHConfig


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
        self.client.connect(
            hostname=user_config["hostname"],
            username=user_config["user"],
            port=int(user_config["port"]),
            key_filename=key_filename,
        )

    def close(self) -> None:
        """ Close the SSH connection """
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

    def __init__(self, client: SSHClient, cmd:str, values: list[int]) -> None:
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
        if v <= values[0]:
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
        print(f"CPU temperature: {temp}°C")
        return Monitor.match(temp, self.values)


if __name__ == "__main__":
    v1 = [50,65,80]
    v2 = [60,70,80]
    cmd1="cat /sys/class/thermal/thermal_zone2/temp"
    cmd2="cat /sys/class/thermal/thermal_zone0/temp"
    conn = Connection("alpha")
    monitor = CpuTemperature(conn.client,cmd1, v1)
    print(monitor.probe())
    conn = Connection("beta")
    monitor = CpuTemperature(conn.client, cmd1, v1)
    print(monitor.probe())
    conn.close()
    conn = Connection("apollo")
    monitor = CpuTemperature(conn.client, cmd2, v2)
    print(monitor.probe())
    conn.close()
    conn = Connection("artemis")
    monitor = CpuTemperature(conn.client, cmd2, v2)
    print(monitor.probe())
    conn.close()
