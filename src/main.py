"""
Zero-Monitor Main Module
Author: Wolf Paulus wolf@paulus.com
"""
import socket
from time import sleep
from collections import ChainMap
from yaml import safe_load
from monitor import Connection, Monitor
from display import NeoDisplay, NeoDisplayMac

from log import logger

if __name__ == "__main__":

    try:
        from waveshare import DS3231
        RTC = DS3231.DS3231(add=0x68)
        logger.info(f"Temperature {RTC.Read_Temperature():.2f} Celsius")
    except Exception as e:
        logger.error(f"Error initializing DS3231: {e}")
        RTC = None
    try:
        with open("monitor.yaml") as file:
            config = safe_load(file)
            logger.info("Configuration loaded successfully.")
        if socket.gethostname() == "imac":
            display = NeoDisplayMac(config)
        elif RTC is not None:  # The device is not equipped with the e-Paper display
            from ink import InkDisplay
            logger.info("Using InkDisplay for e-ink display.")
            display = InkDisplay(config)
        else:
            logger.info("Using NeoDisplay for LED strip.")
            display = NeoDisplay(config)
    except OSError as err:
        logger.error(f"Error loading configuration file. {err}")
        exit(1)

    while True:
        for h, host in enumerate(config.get("hosts")):  # iterate over hosts currently 7 configured
            hostname = host.get("hostname")
            conn = Connection(hostname)  # use with statement
            if conn and conn.client:
                for s, sensor in enumerate(config.get("sensors").values()):  # iterate over sensors
                    name = sensor.get("name")
                    sensor = ChainMap(host.get(name, {}), sensor)
                    instance = Monitor.create_instance(name, conn.client, sensor.get("cmd"), sensor.get("values"))
                    if instance is not None:
                        col, val = instance.probe()
                        display.update(h, s, (col,val), 0.5, hostname)
                    else:
                        logger.error(f"Sensor {name} not found. Skipping sensor probe for this host.")
                        display.update(h, s, (-1,-1))
                conn.close()
            else:
                logger.warning(f"{host} seems to be offline. Skipping sensor probe(s) for this host.")
                for s, sensor in enumerate(config.get("sensors").values()):
                    display.update(h, s, (-1,-1))
            sleep(config.get("host_timeout", 0.5))
