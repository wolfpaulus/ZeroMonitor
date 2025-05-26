"""
Zero-Monitor Main Module
"""

from time import sleep
from yaml import safe_load
from monitor import Connection, Monitor
from rpi_ws281x import PixelStrip, Color
from log import logger

COLORS = [
    Color(0, 0, 15),
    Color(0, 9, 6),
    Color(0, 15, 0),
    Color(13, 4, 0),
    Color(15, 0, 0),
    Color(9, 0, 6),
    Color(0, 0, 0),
]
# ROWS = 4 COLS = 8 Each host has one column
# host = h : 0 .. 7 sensor = i : 0 .. 3
#
# 31 30 29 28 27 26 25 24   x = ROWS * COLS - 1 - h - (i * COLS)
# 23 22 21 20 19 18 17 16   == (ROWS - i) * COLS - h - 1
# 15 14 13 12 11 10 09 08.  E.g. h = 2, i = 3 : (4 - 3)*8 - 2 - 1 = 4
# 07 06 05 04 03 02 01 00

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
        strip = PixelStrip(num=32, pin=18, freq_hz=800_000, dma=10, invert=False, brightness=config.get("brightness",16), channel=0)
        strip.begin()
    except Exception as err:
        logger.error(f"Error connecting to neopixels: {err}")
        exit(1)

    while True:
        for h, host in enumerate(config.get("hosts")): # iterate over hosts currently 7 configured
            strip.setPixelColor(0,Color(1,10,7) if h%2 == 0 else Color(0, 0, 0))
            conn = Connection(host.get("hostname"))  # use with statement
            if conn and conn.client:
                for i, sensor in enumerate(config.get("sensors").values()): # iterate over sensors
                    sensor = sensor.copy()
                    # update the sensor with host overrides
                    sensor_name = sensor.get("name")
                    if specific_sensor := host.get(sensor_name):
                        for k,v in specific_sensor.items():
                            sensor[k]= v
                    instance = Monitor.create_instance(sensor_name, conn.client, sensor.get("cmd"), sensor.get("values"))
                    pix = (ROWS - i) * COLS - h - 1
                    strip.setPixelColor(pix, Color(0, 0, 0))
                    strip.show()  # activity indicator
                    if instance is not None:
                        strip.setPixelColor(pix, COLORS[instance.probe()])
                    else:
                        logger.error(f"Sensor {sensor_name} not found. Skipping sensor probe for this host.")
                        strip.setPixelColor(pix, Color(0, 0, 0))
                    sleep(config.get("sensor_timeout", 0.5))
                    strip.show()
                conn.close()
            else:
                logger.warning(f"{host} seems to be offline. Skipping sensor probe(s) for this host.")
                for i in range(ROWS):
                    strip.setPixelColor((ROWS - i) * COLS - h - 1, Color(0, 0, 0))
                strip.show()
            sleep(config.get("host_timeout", 0.5))

