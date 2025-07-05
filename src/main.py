"""
Zero-Monitor Main Module
Author: Wolf Paulus wolf@paulus.com
"""
import sys
from time import sleep
from collections import ChainMap
from yaml import safe_load
from monitor import Connection, Monitor
from display import Display, NeoDisplay
from ink import InkDisplay

from log import logger

if __name__ == "__main__":
    try:
        with open("monitor.yaml", encoding='utf-8') as file:
            config = safe_load(file)
            logger.info("Configuration loaded successfully.")
    except OSError as err:
        logger.error("Error loading configuration file. %s", err)
        sys.exit(1)
    display = InkDisplay(
        config) if Display.has_epaper() else NeoDisplay(config)

    while True:
        for hi, host in enumerate(config.get("hosts")):  # iterate over hosts, currently 7 configured
            hostname = host.get("hostname")
            try:
                with Connection(hostname) as conn:
                    if conn is not None:
                        for si, sensor in enumerate(config.get("sensors").values()):  # iterate over sensors
                            class_ = sensor.get("name")
                            sensor = ChainMap(host.get(class_, {}), sensor)
                            instance = Monitor.create_instance(class_, conn, sensor.get("cmd"), sensor.get("values"))
                            if instance is not None:
                                display.update(hi, si, instance.probe())
                            else:
                                logger.error("Sensor %s not found. Skipping sensor probe for this host.", class_)
                                display.update(hi, si, (-1, -1))
                    else:
                        logger.error("Connection to %s failed. Skipping sensor probe(s) for this host.", hostname)
                        for si, sensor in enumerate(config.get("sensors").values()):
                            display.update(hi, si, (-1, -1))

            except (OSError, ConnectionError) as err:
                logger.error("%s : %s", host.get("hostname"), err)
                for si, sensor in enumerate(config.get("sensors").values()):
                    display.update(hi, si, (-1, -1))
            sleep(config.get("host_timeout", 0.5))
