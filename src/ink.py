"""
InkDisplay class for e-ink displays.
https://www.waveshare.com/wiki/2.13inch_e-Paper_HAT+
Author: Wolf Paulus <wolf@paulus.com>
"""

import subprocess
from time import sleep, strftime
from datetime import datetime
from typing import Any

from PIL.ImageFont import FreeTypeFont
from PIL import Image, ImageDraw, ImageFont

from display import Display
from waveshare.epd2in13_V4 import EPD
from log import logger

try:
    logger.info("Loading fonts...")
    bold = ImageFont.truetype("fonts/DejaVuSans-Bold.ttf", 15)
    small = ImageFont.truetype("fonts/DejaVuSans.ttf", 15)
    tiny = ImageFont.truetype("fonts/DejaVuSans.ttf", 12)
    icons = ImageFont.truetype("fonts/materialdesignicons-webfont.ttf", 18)
except OSError as e:
    logger.error("Error loading fonts: %s", e)


class InkDisplay(Display):
    """Display class for e-ink displays."""

    def __init__(self, cfg: dict):
        """Initialize the e-ink display."""
        logger.info("init and clear the e-ink display")
        self.active = False
        self.cfg = cfg
        self.all_hosts = cfg.get("hosts", [])
        self.hosts = [host.get("hostname") for host in self.all_hosts[:4]]  # display is limited to 4 hosts
        self.timeout = cfg.get("displays", {}).get("epaper").get("sensor_timeout", 0.5)
        self.on = datetime.strptime(cfg.get("displays", {}).get("epaper").get("on_"), "%H:%M").time()
        self.off = datetime.strptime(cfg.get("displays", {}).get("epaper").get("off_"), "%H:%M").time()
        self.epd = EPD()
        self.image = None
        self.draw = None
        self.counter = 0
        self.values: list[Any] = [0] * len(self.hosts) * 4  # 4 sensors per host
        self.init()

    def init(self) -> None:
        """Initialize the e-ink display and prepare for partial updates."""
        if not self.active:
            self.epd.init()
            self.epd.Clear()
            logger.info("Creating a white image, matching the display size...")
            self.image = Image.new("1", (self.epd.height, self.epd.width), 1)
            self.draw = ImageDraw.Draw(self.image)
            self.draw_mixed_font_text((0, 1), self.get_header())
            self.draw.line([(0, 20), (249, 20)], fill=0, width=1)
            self.draw.line([(0, 103), (249, 103)], fill=0, width=1)
            self.epd.displayPartBaseImage(self.epd.getbuffer(self.image.rotate(180)))
            for i, host in enumerate(self.hosts):
                y = 22 + 20 * i
                self.draw.text((0, y), host[:10], font=bold, fill=0)
            self.epd.displayPartial(self.epd.getbuffer(self.image.rotate(180)))
            self.active = True
            sleep(1)

    def sleep(self) -> None:
        """Turn off the e-ink display."""
        if self.active:
            # turn off the display
            self.epd.init()
            self.epd.Clear(0xFF)
            self.epd.sleep()
            self.active = False

    def update(self, hi: int, si: int, values: tuple[int, int]):
        """Update the display buffer at the specified row and column with the given value.
        if hi == si == 0, the display will be  redrawn.
        At that time, the footer with time and WiFi quality will be redrawn as well.
        Args:
            hi (int): Host index. 0 .. 7
            si (int): Sensor index. 0 .. 3
            values (tuple[int, int]): Values to display, e.g., (value, color_code).
        """
        sleep(self.timeout)
        if self.on <= datetime.now().time() < self.off:
            if not self.active:  # if the display is not active, redraw it
                self.init()
        else:
            if self.active:
                self.sleep()  # turn off the display
            return  # no need to update the buffer if the display is off

        if hi == si == 0 and any(self.values):  # find live hosts and update the display

            live_hosts = []
            for i, host in enumerate(self.hosts):
                if any(self.values[i * 4:i * 4 + 4]):
                    live_hosts.append(host.get("hostname"))
            live_hosts = live_hosts[:4]  # limit to 4 hosts for display

            if live_hosts != self.hosts:  # update the display with live hosts
                logger.info("Updating display with live hosts: %s", live_hosts)
                self.hosts = live_hosts
                self.active = False  # reset active state to reinitialize the display
                self.init()  # reinitialize the display with live hosts
            else:
                self.draw.rectangle((65, 22, 249, 121), fill=1)  # clear partial image

            for row in range(len(self.hosts)):
                y = 22 + 20 * row
                for col in range(4):
                    x = 65 + 45 * col
                    self.draw.text(
                        (x, y),
                        f"{self.values[col + row * 4]:4}",
                        font=small,
                        fill=0,
                    )
                self.draw.line([(65, 103), (254, 103)], fill=0, width=1)
                self.draw_mixed_font_text((65, 105), self.get_footer())
                self.epd.displayPartial(self.epd.getbuffer(self.image.rotate(180)))

        # put the values into the buffer
        self.values[si + hi * 4] = values[0] if values[0] >= 0 else ""

    def draw_mixed_font_text(self, xy: tuple[int, int], text_data: list[tuple[str, FreeTypeFont]], color=0):
        """Draws text with mixed fonts and styles."""
        current_x, current_y = xy
        for text, font in text_data:
            self.draw.text((current_x, current_y), text, fill=color, font=font)
            text_width = self.draw.textbbox((current_x, current_y), text, font=font)[2]  # Calculate text width
            current_x = text_width  # Update starting X position

    @staticmethod
    def get_header() -> list[tuple[str, FreeTypeFont]]:
        """Get the header for the e-ink display."""
        spaces = " " * 2
        return [
            ("󱂇", icons),  # computer
            (spaces * 6, small),
            ("󰢻", icons),  # processes
            ("%" + spaces, small),
            ("󰔏", icons),  # temp
            ("°C" + spaces, small),
            ("󰍛", icons),  # mem
            ("%" + spaces, small),
            ("󰆼", icons),  # disk space
            ("%", small),
        ]

    @staticmethod
    def get_footer() -> list[tuple[str, FreeTypeFont]]:
        """Get the footer for the e-ink display."""
        return [
            (" " * 2, tiny),
            ("󰅐", icons),
            (f" {strftime('%H:%M:%S')}   ", tiny),
            ("󰖩", icons),
            (
                f" {InkDisplay.get_wifi_quality()}",
                tiny,
            ),  # iwconfig wlan0 | grep Quality
        ]

    @staticmethod
    def get_wifi_quality() -> str:
        """Get the WiFi quality using iwconfig."""
        wifi_data = "-/-"
        try:
            command = "/usr/sbin/iwconfig wlan0"
            process = subprocess.Popen(
                command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            output, error = process.communicate()
            if not error:
                for line in output.decode("utf-8").splitlines():
                    if "Link Quality" in line:
                        wifi_data = line.split("Link Quality=")[
                            1].split(" ")[0]
            else:
                logger.error("Error: %s", error.decode('utf-8'))
        except (OSError, subprocess.SubprocessError) as err:
            logger.error("Failed to get WiFi quality: %s", err)
        return wifi_data
