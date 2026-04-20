"""
Zero-Monitor Main Module
Author: Wolf Paulus wolf@paulus.com
"""
import sys
from time import sleep
from collections import ChainMap
from yaml import safe_load
from monitor import Connection, Monitor
from websvr import WebDisplay
from log import logger

ROWS, COLS = 4, 8


def calculate_position(mode: int, hi: int, si: int) -> tuple[int, int]:
    """Calculate the col, row position of the LED based on the mode, host index, and sensor index."""
    if mode == 1:  # one host with 32 sensors, filled row-wise
        return si % COLS, si // COLS
    elif mode == 2:  # four hosts with eight sensors each : one row per host
        return si % COLS, hi
    elif mode == 3:  # eight hosts with four sensors each : one column per host
        return hi, si
    else:  # thirty-two hosts with one sensor each, filled row-wise
        return hi % COLS, hi // COLS


if __name__ == "__main__":
    try:
        with open("monitor.yaml", encoding='utf-8') as file:
            config = safe_load(file)
            logger.info("Configuration loaded successfully.")
    except OSError as err:
        logger.error("Error loading configuration file. %s", err)
        sys.exit(1)

    from display import NeoDisplay  # noqa: E402 — imported here to avoid rpi_ws281x dependency at module level
    display = NeoDisplay(config)
    web_display = WebDisplay(config)

    mode = config.get("displays", {}).get("neopixel", {}).get("mode", 1)
    if mode == 1:
        max_hosts = 1
        max_sensors = 32
    elif mode == 2:
        max_hosts = 4
        max_sensors = 8
    elif mode == 3:
        max_hosts = 8
        max_sensors = 4
    else:
        max_hosts = 32
        max_sensors = 1

    while True:
        for hi, host in enumerate(config.get("hosts")):  # iterate over hosts, currently 7 configured
            if hi >= max_hosts:
                break  # Skipping remaining hosts.",
            hostname = host.get("hostname")
            try:
                with Connection(hostname) as conn:
                    if conn is not None:
                        for si, sensor in enumerate(config.get("sensors").values()):  # iterate over sensors
                            if si >= max_sensors:
                                break  # Skipping remaining sensors for this host.",
                            col, row = calculate_position(mode, hi, si)
                            class_ = sensor.get("name")
                            sensor = ChainMap(host.get(class_, {}), sensor)
                            instance = Monitor.create_instance(class_, conn, sensor.get("cmd"), sensor.get("values"))
                            if instance is not None:
                                display.update(col, row, instance.probe())
                                web_display.update(col, row, instance.probe())
                            else:
                                logger.error("Sensor %s not found. Skipping sensor probe for this host.", class_)
                                display.update(col, row, (-1, -1))
                                web_display.update(col, row, (-1, -1))
                    else:
                        logger.error("Connection to %s failed. Skipping sensor probe(s) for this host.", hostname)
                        for si, sensor in enumerate(config.get("sensors").values()):
                            col, row = calculate_position(mode, hi, si)
                            display.update(col, row, (-1, -1))
                            web_display.update(col, row, (-1, -1))

            except (OSError, ConnectionError) as err:
                logger.error("%s : %s", host.get("hostname"), err)
                for si, sensor in enumerate(config.get("sensors").values()):
                    col, row = calculate_position(mode, hi, si)
                    display.update(col, row, (-1, -1))
                    web_display.update(col, row, (-1, -1))
            sleep(config.get("host_timeout", 0.5))
