"""Display management module for LED strip control.
Author: Wolf Paulus <wolf@paulus.com>
"""

from abc import ABC, abstractmethod
from time import sleep
from datetime import datetime
from rpi_ws281x import PixelStrip, Color
from waveshare import DS3231
from log import logger


class Display(ABC):
    """Abstract base class for display management."""

    @abstractmethod
    def update(self, hi: int, si: int, values: tuple[int, int]) -> None:
        """Update the display for a given host and sensor.
        Args:
            hi (int): Host index.
            si (int): Sensor index.
            values (tuple[int,int]): Values to display, e.g., (value, color_code).
        """
        pass

    @staticmethod
    def has_epaper() -> bool:
        """Check if the display has an e-Paper display."""
        try:
            rtc = DS3231.DS3231(add=0x68)
            logger.info(
                f"E-Paper Display Temperature {rtc.Read_Temperature():.2f} Celsius"
            )
            return True
        except Exception as e:
            logger.error(f"Error initializing DS3231: {e}")
            return False


class NeoDisplay(Display):
    """Display class to manage the LED strip and its configuration.
    https://www.waveshare.com/wiki/RGB_LED_HAT

    ROWS = 4 COLS = 8 Each host has one column
    host = h : 0 .. 7 sensor = i : 0 .. 3
    31 30 29 28 27 26 25 24   x = ROWS * COLS - 1 - h - (i * COLS)
    23 22 21 20 19 18 17 16   == (ROWS - i) * COLS - h - 1
    15 14 13 12 11 10 09 08.  E.g. h = 2, i = 3 : (4 - 3)*8 - 2 - 1 = 4
    07 06 05 04 03 02 01 00
    """

    ROWS, COLS = 4, 8
    COLORS = [
        Color(0, 0, 31),
        Color(0, 15, 15),
        Color(0, 31, 0),
        Color(15, 15, 0),
        Color(31, 0, 0),
        Color(31, 0, 31),
        Color(0, 0, 0),
    ]

    def __init__(self, cfg: dict):
        try:
            self.on = datetime.strptime(
                cfg.get("displays",{}).get("neopixel").get("on_"), "%H:%M"
            ).time()
            self.off = datetime.strptime(
                cfg.get("displays",{}).get("neopixel").get("off_"), "%H:%M"
            ).time()
            self.timeout = (
                cfg.get("displays",{}).get("neopixel").get("sensor_timeout", 0.5)
            )
            self.brightness = cfg.get("displays",{}).get("neopixel").get("brightness", 63)
            self.strip = PixelStrip(
                num=32,
                pin=18,
                freq_hz=800_000,
                dma=10,
                invert=False,
                brightness=self.brightness,
                channel=0,
            )
            self.strip.begin()
        except Exception as err:
            logger.error(f"Error connecting to neo-pixels: {err}")
            exit(1)

    def update(self, hi: int, si: int, values: tuple[int, int]) -> None:
        """Update the display for a given host and sensor.
        Args:
            hi (int): Host index.
            si (int): Sensor index.
            values (tuple[int,int]): Values to display, e.g., (value, color_code).
        """
        sleep(self.timeout)
        if self.on <= datetime.now().time() < self.off:
            self.strip.setBrightness(self.brightness)
            index = (
                NeoDisplay.COLS * NeoDisplay.ROWS - 1 - hi - si * NeoDisplay.COLS
            )  # Calculate the index based on host and sensor
            # hi = 0, si = 3 -> 31 - 0 - 3 * 8 = 7
            # hi = 3, si = 0 -> 31 - 3 - 0 * 8 = 28
            # hi = 7, si = 3 -> 31 - 7 - 3 * 8 = 0
            self.strip.setPixelColor(index, NeoDisplay.COLORS[-1])
            self.strip.show()
            sleep(0.25)
            self.strip.setPixelColor(index, NeoDisplay.COLORS[values[1]])
        else:
            self.strip.setBrightness(0)
        self.strip.show()
