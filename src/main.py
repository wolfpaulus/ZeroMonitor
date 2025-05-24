"""
Zero-Monitor Main Module
"""
from time import sleep
from yaml import safe_load
from monitor import Connection, Monitor
from rpi_ws281x import PixelStrip, Color

COLORS = [
    Color(0, 0, 16), Color(0, 10, 6), Color(0, 16, 0), Color(12, 4, 0), Color(16, 0, 0), Color(10, 0, 6)
]


if __name__ == "__main__":
    try:
        strip = PixelStrip(num=32, pin=18)
        strip.begin()
        with open("monitor.yaml") as file:
            config = safe_load(file)
            print("Configuration loaded successfully.")
    except OSError as err:
        print(f"Error loading configuration file. {err}")
        exit(1)

    while True:
        for i, host in enumerate(config.get("hosts")):
            conn = Connection(host.get("hostname"))  # use with statement
            if conn and conn.client:
                for s in host.get("sensors"):
                    sensor = Monitor.create_instance(s.get("sensor"), conn.client, s.get("cmd"), s.get("values"))
                    if sensor is not None:
                        color = sensor.probe()
                        print(f"Sensor: {s.get('sensor')}, Color Index: {color}")
                        strip.setPixelColor(i, COLORS[color])
            else:
                print(f"{host} seems to be offline. Skipping sensor probe for this host. . ")
            conn.close()
        strip.show()
        sleep(config.get("pause", 5*60))
