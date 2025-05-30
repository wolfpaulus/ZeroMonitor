""" InkDisplay class for e-ink displays."""
import time
import subprocess
from display import Display
from log import logger
from PIL import Image, ImageDraw, ImageFont
from waveshare import epd2in13_V4

bold = ImageFont.truetype('DejaVuSans-Bold.ttf', 15)
small = ImageFont.truetype('DejaVuSans.ttf', 15)
tiny = ImageFont.truetype('DejaVuSans.ttf', 12)
icons = ImageFont.truetype('fonts/materialdesignicons-webfont.ttf', 18)

class InkDisplay(Display):
    """Display class for e-ink displays."""

    def __init__(self, config: dict):
        """Initialize the e-ink display."""
        logger.info("init and clear the e-ink display")
        self.hosts = config.get("epaper", {}).get("hosts", [])
        self.epd = epd2in13_V4.EPD()
        self.counter = 0
        self.values = [0] * 16
        self.epd.init()
        self.epd.Clear()
        self._redraw()
        time.sleep(1)


    def update(self, x: int, _: int, values: tuple[int,int], delay: float = 0.1, hostname:str = None):
        """Update the pixel at the specified row and column with the given color."""
        if hostname not in self.hosts:
            return # irrelevant host
        y = self.hosts.index(hostname) # get the row index provided y is irrelevant
        self.counter += 1
        self.values[x + y * 4] = values[1]
        if self.counter == 16:
            self.counter = 0
            self.draw.rectangle((65, 22, 249, 121), fill=1)  # clear partial image
            for row in range(4):
                y = 22 + 20 * row
                for col in range(4):
                    x = 65 + 45 * col
                    self.draw.text((x, y), f"{self.values[row + col*4]:4}", font=small, fill=0)

            self.draw.line([(65, 103), (254, 103)], fill=0, width=1)
            self.draw_mixed_font_text((65, 105), self.get_footer())
            self.epd.displayPartial(self.epd.getbuffer(self.image.rotate(180)))


    def _redraw(self) -> None:
        """Redraw the e-ink display."""
        logger.info("Creating a white image, matching the display size...")
        self.image = Image.new('1', (self.epd.height, self.epd.width), 1)
        self.draw = ImageDraw.Draw(self.image)
        self.draw_mixed_font_text((0, 1), self.get_header())
        self.draw.line([(0, 20), (249, 20)], fill=0, width=1)
        self.draw.line([(0, 103), (249, 103)], fill=0, width=1)
        self.epd.displayPartBaseImage(self.epd.getbuffer(self.image.rotate(180)))
        for i in range(len(self.hosts)):
            host = f"{(self.hosts[i])[:10]}"
            y = 22 + 20 * i
            self.draw.text((0, y), host, font=bold, fill=0)
        self.epd.displayPartial(self.epd.getbuffer(self.image.rotate(180)))


    def draw_mixed_font_text(self, xy, text_data, color=0):
        """Draws text with mixed fonts and styles."""
        current_x, current_y = xy
        for item in text_data:
            text, font = item
            self.draw.text((current_x, current_y), text, fill=color, font=font)
            text_width = self.draw.textbbox((current_x, current_y), text, font=font)[2]  # Calculate text width
            current_x = text_width  # Update starting X position

    @staticmethod
    def get_header() -> list[tuple]:
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
            # 󰖩 󰅐 󰄴 󰍶
        ]

    @staticmethod
    def get_footer() -> list[tuple]:
        """Get the footer for the e-ink display."""
        """ todo - get the wifi quality and signal strength """
        return [
            (" " * 2, tiny),
            ("󰅐", icons),
            (f" {time.strftime('%H:%M:%S')}   ", tiny),
            ("󰖩", icons),
            (f" {InkDisplay.get_wifi_quality()}/70  ", tiny)  # iwconfig wlan0 | grep Quality
        ]

    @staticmethod
    def get_wifi_quality()->int:
        command = "iwconfig"
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()

        if error:
            logger.error(f"Error: {error.decode('utf-8')}")
            return 0

        output_str = output.decode("utf-8")
        lines = output_str.splitlines()

        wifi_data = {}
        for line in lines:
            if "Signal level" in line:
                wifi_data["signal_level"] = line.split("Signal level=")[1].split(" ")[0]
            if "Link Quality" in line:
                wifi_data["link_quality"] = line.split("Link Quality=")[1].split(" ")[0]

        return int(wifi_data.get("link_quality", 0))
