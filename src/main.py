"""
Zero-Monitor Main Module
"""

from time import sleep
from yaml import safe_load
from monitor import Connection, Monitor
from rpi_ws281x import PixelStrip, Color
from log import logger

COLORS = [
    Color(0, 0, 16), Color(0, 10, 6), Color(0, 16, 0), Color(12, 4, 0), Color(16, 0, 0), Color(10, 0, 6)
]
# ROWS = 4 COLS = 8
# Each host has one column
# host = h : 0 .. 7
# sensor = i : 0 .. 3
#
# 31 30 29 28 27 26 25 24   x = ROWS * COLS - 1 - h - (i * COLS)
# 23 22 21 20 19 18 17 16   == (ROWS - i) * COLS - h - 1
# 15 14 13 12 11 10 09 08.  E.g. h = 2, i = 3 : (4 - 3)*8 - 2 - 1 = 4
# 07 06 05 04 03 02 01 00

ROWS, COLS = 4, 8
SLEEP = 0.5
if __name__ == "__main__":
    try:
        with open("monitor.yaml") as file:
            config = safe_load(file)
            logger.info("Configuration loaded successfully.")
    except OSError as err:
        logger.error(f"Error loading configuration file. {err}")
        exit(1)
    try:
        strip = PixelStrip(num=32, pin=18)
        strip.begin()
    except Exception as err:
        logger.error(f"Error connecting to neopixels: {err}")
        exit(1)

    while True:
        for h, host in enumerate(config.get("hosts")):
            conn = Connection(host.get("hostname"))  # use with statement
            if conn and conn.client:
                for i, s in enumerate(host.get("sensors")):
                    sensor = Monitor.create_instance(s.get("sensor"), conn.client, s.get("cmd"), s.get("values"))
                    if sensor is not None:
                        color = sensor.probe()
                        strip.setPixelColor((ROWS - i) * COLS - h - 1, COLORS[color])
                    else:
                        logger.error(f"Sensor {s.get('sensor')} not found. Skipping sensor probe for this host.")
                        strip.setPixelColor((ROWS - i) * COLS - h - 1, Color(0, 0, 0))
                    strip.show()
                    sleep(SLEEP)
            else:
                for i, s in enumerate(host.get("sensors")):
                    strip.setPixelColor((ROWS - i) * COLS - h - 1, Color(0, 0, 0))
                logger.warning(f"{host} seems to be offline. Skipping sensor probe(s) for this host.")
            conn.close()
            # Update the strip with the new pixel colors
            strip.show()
            sleep(SLEEP)
        sleep(config.get("pause", 5 * 60))
