"""
Zero-Monitor Main Module
"""
from time import sleep
from yaml import safe_load
from pi5neo import Pi5Neo
from monitor import Connection, Monitor

COLORS = [
    (0, 0, 16), (0, 10, 6), (0, 16, 0), (12, 4, 0), (16, 0, 0), (10, 0, 6)
]

if __name__ == "__main__":
    try:
        with open("monitor.yaml") as file:
            config = safe_load(file)
            print("Configuration loaded successfully.")
    except OSError as err:
        print(f"Error loading configuration file. {err}")
        exit(1)

    # Initialize the Pi5Neo class with 10 LEDs and an SPI speed of 800kHz
    neo = Pi5Neo('/dev/spidev0.0', config.get("pixels", 8), 800)

    while True:
        for i, host in enumerate(config.get("hosts")):
            conn = Connection(host.get("hostname"))  # use with statement
            for s in host.get("sensors"):
                sensor = Monitor.create_instance(s.get("sensor"), conn.client, s.get("cmd"), s.get("values"),)
                color = sensor.probe()
                print(f"Sensor: {s.get('sensor')}, Color Index: {color}")
                neo.set_led_color(i, *COLORS[color])
            conn.close()
        neo.update_strip()
        sleep(config.get("pause", 5*60))
