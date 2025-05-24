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
ROWS, COLS = 4, 8

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
        for i, host in enumerate(config.get("hosts")):
            conn = Connection(host.get("hostname"))  # use with statement
            if conn and conn.client:
                for j, s in enumerate(host.get("sensors")):
                    sensor = Monitor.create_instance(s.get("sensor"), conn.client, s.get("cmd"), s.get("values"))
                    if sensor is not None:
                        color = sensor.probe()
                        strip.setPixelColor((ROWS -j) * COLS -i, COLORS[color])
            else:
                logger.warning(f"{host} seems to be offline. Skipping sensor probe(s) for this host.")
            conn.close()
        strip.show()
        sleep(config.get("pause", 5*60))
