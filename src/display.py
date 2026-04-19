"""Display management module for LED strip control.
Author: Wolf Paulus <wolf@paulus.com>
Version: 1.0
"""
import sys
from abc import ABC, abstractmethod
from time import sleep
from datetime import datetime
from rpi_ws281x import PixelStrip, Color  # type: ignore
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
    COLOR_OFF = Color(0, 0, 0)
    COLORS = [
        Color(0, 0, 31),    # 0: blue    — low/idle
        Color(0, 15, 15),   # 1: cyan    — below normal
        Color(0, 31, 0),    # 2: green   — normal
        Color(15, 15, 0),   # 3: yellow  — above normal
        Color(31, 0, 0),    # 4: red     — high
        Color(31, 0, 31),   # 5: pink    — critical
    ]

    def __init__(self, cfg: dict):
        try:
            neo_cfg = cfg.get("displays", {}).get("neopixel", {})
            self.on = datetime.strptime(
                neo_cfg.get("on_"), "%H:%M"
            ).time()
            self.off = datetime.strptime(
                neo_cfg.get("off_"), "%H:%M"
            ).time()
            self.timeout = neo_cfg.get("sensor_timeout", 0.5)
            self.brightness = neo_cfg.get("brightness", 63)
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
            logger.error("Error connecting to neo-pixels: %s", err)
            sys.exit(1)

    def update(self, hi: int, si: int, values: tuple[int, int]) -> None:
        """Update the display for a given host and sensor.
        Args:
            hi (int): Host index.
            si (int): Sensor index.
            values (tuple[int,int]): Values to display, e.g., (value, color_code).
        """
        sleep(self.timeout)
        if self._is_active():
            self.strip.setBrightness(self.brightness)
            index = (
                NeoDisplay.COLS * NeoDisplay.ROWS - 1 - hi - si * NeoDisplay.COLS
            )  # Calculate the index based on host and sensor
            # hi = 0, si = 3 -> 31 - 0 - 3 * 8 = 7
            # hi = 3, si = 0 -> 31 - 3 - 0 * 8 = 28
            # hi = 7, si = 3 -> 31 - 7 - 3 * 8 = 0
            self.strip.setPixelColor(index, NeoDisplay.COLOR_OFF)
            self.strip.show()
            sleep(0.25)
            color_idx = values[1]
            color = NeoDisplay.COLORS[color_idx] if 0 <= color_idx < len(NeoDisplay.COLORS) else NeoDisplay.COLOR_OFF
            self.strip.setPixelColor(index, color)
        else:
            self.strip.setBrightness(0)
        self.strip.show()

    def _is_active(self) -> bool:
        """Check if LEDs should be on based on the configured schedule.
        Supports both daytime (on < off) and overnight (on > off) schedules.
        """
        now = datetime.now().time()
        if self.on <= self.off:
            return self.on <= now < self.off
        # Overnight schedule (e.g., on=22:00, off=6:30)
        return now >= self.on or now < self.off
