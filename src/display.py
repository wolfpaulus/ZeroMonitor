""" Display management module for LED strip control."""
from abc import ABC, abstractmethod
from time import sleep
from datetime import datetime
from rpi_ws281x import PixelStrip, Color
from log import logger


class Display(ABC):
    """ Abstract base class for display management."""

    @abstractmethod
    def update(self, x:int, y:int, values: tuple[int], delay:float, hostname:str = None)->None:
        """Update the pixel at the specified row and column with the given color."""
        pass


class NeoDisplay(Display):
    """Display class to manage the LED strip and its configuration.
        ROWS = 4 COLS = 8 Each host has one column
        host = h : 0 .. 7 sensor = i : 0 .. 3
        31 30 29 28 27 26 25 24   x = ROWS * COLS - 1 - h - (i * COLS)
        23 22 21 20 19 18 17 16   == (ROWS - i) * COLS - h - 1
        15 14 13 12 11 10 09 08.  E.g. h = 2, i = 3 : (4 - 3)*8 - 2 - 1 = 4
        07 06 05 04 03 02 01 00
    """
    ROWS, COLS = 4, 8
    COLORS = [
        Color(0, 0, 15),
        Color(0, 9, 6),
        Color(0, 15, 0),
        Color(13, 4, 0),
        Color(15, 0, 0),
        Color(9, 0, 6),
        Color(0, 0, 0),
    ]

    def __init__(self, config: dict):
        try:
            self.on = datetime.strptime(config.get("neopixel").get("on_"), "%H:%M").time()
            self.off = datetime.strptime(config.get("neopixel").get("off_"), "%H:%M").time()
            self.brightness = config.get("neopixel").get("brightness", 63)
            self.strip = PixelStrip(num=32,
                                    pin=18,
                                    freq_hz=800_000,
                                    dma=10,
                                    invert=False,
                                    brightness=self.brightness,
                                    channel=0)
            self.strip.begin()
        except Exception as err:
            logger.error(f"Error connecting to neo-pixels: {err}")
            exit(1)


    def update(self, x: int, y: int, values:tuple[int,int], delay: float = 0.1, hostname:str = None) -> None:
        """Update the pixel at the specified row and column with the given color."""
        if self.on <= datetime.now().time() < self.off:
            self.strip.setBrightness(self.brightness)
            index = NeoDisplay.COLS * NeoDisplay.ROWS - x - 1 - (y * NeoDisplay.COLS)
            if delay > 0.1:
                color = -1 if values[0] != -1 else 0
                self.strip.setPixelColor(index, NeoDisplay.COLORS[color])
                self.strip.show()
                sleep(delay)
            self.strip.setPixelColor(index, NeoDisplay.COLORS[values[0]])
        else:
            self.strip.setBrightness(0)
        self.strip.show()


class NeoDisplayMac(Display):
    """Display class to manage the LED strip and its configuration for Mac."""
    ROWS, COLS = 4, 8
    COLORS = "🔵🔵🟢🟧🔴🟪⚪⚫"

    def __init__(self, _: dict):
        self.buffer = ["⚫"] * 32

    def update(self, x: int, y: int, values:tuple[int,int], delay: float = 0.1, hostname:str = None):
        """Update the pixel at the specified row and column with the given color."""
        self.buffer[x + NeoDisplayMac.COLS * y] = NeoDisplayMac.COLORS[values[0]]
        screen = []
        for r in range(NeoDisplayMac.ROWS):
            screen += self.buffer[r * NeoDisplayMac.COLS:(r + 1) * NeoDisplayMac.COLS]
            screen += "\n"
        print("".join(screen))