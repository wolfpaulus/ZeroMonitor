"""
Zero-Monitor Main Module
Author: Wolf Paulus wolf@paulus.com
"""
from time import sleep
from collections import ChainMap
from yaml import safe_load
from monitor import Connection, Monitor
from display import Display, NeoDisplay
from ink import InkDisplay

from log import logger

if __name__ == "__main__":
    try:
        with open("monitor.yaml") as file:
            config = safe_load(file)
            logger.info("Configuration loaded successfully.")
    except OSError as err:
        logger.error(f"Error loading configuration file. {err}")
        exit(1)
    display = InkDisplay(config) if Display.has_epaper() else NeoDisplay(config)

    while True:
        for hi, host in enumerate(config.get("hosts")):  # iterate over hosts currently 7 configured
            hostname = host.get("hostname")
            try:
                with Connection(hostname) as conn:
                    for si, sensor in enumerate(config.get("sensors").values()):  # iterate over sensors
                        class_ = sensor.get("name")
                        sensor = ChainMap(host.get(class_, {}), sensor)
                        instance = Monitor.create_instance(class_, conn, sensor.get("cmd"), sensor.get("values"))
                        if instance is not None:
                            display.update(hi, si, instance.probe(), hostname)
                        else:
                            logger.error(f"Sensor {class_} not found. Skipping sensor probe for this host.")
                            display.update(hi, si, (-1, -1))

            except Exception as err:
                logger.warning(f"{host} seems to be offline. Skipping sensor probe(s) for this host.")
                for s, sensor in enumerate(config.get("sensors").values()):
                    display.update(hi, s, (-1, -1))
            sleep(config.get("host_timeout", 0.5))
