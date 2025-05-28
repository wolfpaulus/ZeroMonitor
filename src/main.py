"""
Zero-Monitor Main Module
Author: Wolf Paulus wolf@paulus.com
"""
import socket
from time import sleep
from collections import ChainMap
from yaml import safe_load
from monitor import Connection, Monitor
from display import NeoDisplay, InkDisplay
from log import logger

if __name__ == "__main__":

    print(socket.gethostname())
    try:
        with open("monitor.yaml") as file:
            config = safe_load(file)
            logger.info("Configuration loaded successfully.")
        display = NeoDisplay(config) if socket.gethostname() == "epsilon" else InkDisplay(config)
    except OSError as err:
        logger.error(f"Error loading configuration file. {err}")
        exit(1)

    while True:
        for h, host in enumerate(config.get("hosts")):  # iterate over hosts currently 7 configured
            display.activity()
            conn = Connection(host.get("hostname"))  # use with statement
            if conn and conn.client:
                for i, sensor in enumerate(config.get("sensors").values()):  # iterate over sensors
                    name = sensor.get("name")
                    sensor = ChainMap(host.get(name, {}), sensor)
                    instance = Monitor.create_instance(name, conn.client, sensor.get("cmd"), sensor.get("values"))
                    if instance is not None:
                        col, val = instance.probe()
                        display.update(h, i, col, 0.5)
                    else:
                        logger.error(f"Sensor {name} not found. Skipping sensor probe for this host.")
                        display.update(h, i, -1)
                conn.close()
            else:
                logger.warning(f"{host} seems to be offline. Skipping sensor probe(s) for this host.")
                for i, sensor in enumerate(config.get("sensors").values()):
                    display.update(h, i, -1)
            sleep(config.get("host_timeout", 0.5))
