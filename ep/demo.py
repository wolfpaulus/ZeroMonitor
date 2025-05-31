import logging
import time
from PIL import Image, ImageDraw, ImageFont
from waveshare import epd2in13_V4
from random import randint


# 250x122
def draw_mixed_font_text(draw, xy, text_data, color=0):
    """Draws text with mixed fonts and styles."""
    current_x, current_y = xy
    for item in text_data:
        text, font = item
        draw.text((current_x, current_y), text, fill=color, font=font)
        text_width = draw.textbbox((current_x, current_y), text, font=font)[2]  # Calculate text width
        current_x = text_width  # Update starting X position


logging.basicConfig(level=logging.DEBUG)
logging.info("Loading fonts...")

bold = ImageFont.truetype('fonts/DejaVuSans-Bold.ttf', 15)
small = ImageFont.truetype('fonts/DejaVuSans.ttf', 15)
tiny = ImageFont.truetype('fonts/DejaVuSans.ttf', 12)
icons = ImageFont.truetype('fonts/materialdesignicons-webfont.ttf', 18)


def get_header() -> list[tuple]:
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


def get_footer() -> list[tuple]:
    return [
        (" " * 2, tiny),
        ("󰅐", icons),
        (f" {time.strftime('%H:%M:%S')}   ", tiny),
        ("󰖩", icons),
        (" 70/70  ", tiny)  # iwconfig wlan0 | grep Quality
        # (socket.gethostbyname(socket.gethostname() + ".local"), tiny)
    ]


hosts = ["alpha", "beta", "apollo", "artemis"]
try:
    epd = epd2in13_V4.EPD()
    logging.info("init and Clear")
    epd.init()
    epd.Clear()
    time.sleep(1)

    logging.info("Creating a white image, matching the display size...")
    image = Image.new('1', (epd.height, epd.width), 1)  # 255: clear the frame
    draw = ImageDraw.Draw(image)

    draw_mixed_font_text(draw, (0, 1), get_header())
    draw.line([(0, 20), (249, 20)], fill=0, width=1)
    draw.line([(0,103), (249,103)], fill=0, width=1)

    epd.displayPartBaseImage(epd.getbuffer(image.rotate(180)))
    for i in range(4):
        host = f"{(hosts[i])[:10]}"
        y = 22 + 20 * i
        draw.text((0, y), host, font=bold, fill=0)

    epd.displayPartial(epd.getbuffer(image.rotate(180)))

    for _ in range(15):
        draw.rectangle((65, 22, 249, 121), fill=1)  # clear partial image

        for row in range(4):
            v = [randint(1, 99) for _ in range(4)]
            y = 22 + 20 * row
            for col in range(4):
                x = 65 + 45 * col
                draw.text((x, y), f"{v[col]:4}", font=small, fill=0)

        draw.line([(65, 103), (254, 103)], fill=0, width=1)
        draw_mixed_font_text(draw, (65, 105), get_footer())
        epd.displayPartial(epd.getbuffer(image.rotate(180)))
        time.sleep(5)
    epd.sleep()
except Exception as e:
    logging.error(e)
    epd = epd2in13_V4.EPD()
    epd.sleep()
