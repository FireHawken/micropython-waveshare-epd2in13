from machine import Pin, SPI
from lib import epd2in13
from fonts import font8, font12

# SPI on ESP32 (Hardware SPI #2)
sck = Pin(18)
miso = Pin(19)  # NOT USED
mosi = Pin(23)
# Display config
dc = Pin(2)
cs = Pin(4)
rst = Pin(19)  # NOT USED
busy = Pin(5)
spi = SPI(2, baudrate=2000000, polarity=0, phase=0, bits=8, firstbit=0, sck=sck, miso=miso, mosi=mosi)
epd = epd2in13.EPD(spi, cs, dc, rst, busy)
epd.init()
# Let's use display in landscape orientation
epd.set_rotate(epd2in13.ROTATE_90)

# initialize the frame buffer
fb_size = int(epd.width * epd.height / 8)
frame_black = bytearray(fb_size)
frame_red = bytearray(fb_size)

epd.clear_frame(frame_black, frame_red)

epd.display_string_at(frame_black, 20, 10, "Sensor1 status:", font12, epd2in13.COLORED)
epd.display_string_at(frame_red, 130, 10, "ERROR", font12, epd2in13.COLORED)
epd.display_string_at(frame_black, 20, 40, "Sensor2 status: OK", font12, epd2in13.COLORED)
epd.display_string_at(frame_black, 20, 70, "Sensor3 status:", font12, epd2in13.COLORED)
epd.display_string_at(frame_red, 130, 70, "Offline", font12, epd2in13.COLORED)
epd.draw_rectangle(frame_black, 128, 66, 180, 85, epd2in13.COLORED)
epd.draw_filled_circle(frame_red, 180, 15, 10, epd2in13.COLORED)
epd.draw_circle(frame_black, 180, 45, 10, epd2in13.COLORED)

epd.draw_filled_rectangle(frame_black, 0, 0, 10, 10, epd2in13.COLORED)
epd.draw_filled_rectangle(frame_black, epd.width - 10, 0, epd.width, 10, epd2in13.COLORED)
epd.draw_filled_rectangle(frame_red, 0, epd.height - 10, 10, epd.height, epd2in13.COLORED)
epd.draw_filled_rectangle(frame_red, epd.width - 10, epd.height - 10, epd.width, epd.height, epd2in13.COLORED)

epd.draw_horizontal_line(frame_red, 5, 90, epd.width - 5, epd2in13.COLORED)
epd.draw_horizontal_line(frame_red, 5, 91, epd.width - 5, epd2in13.COLORED)
epd.display_string_at(frame_black, 30, 94, "last update: 12:05 11.08.2023", font8, epd2in13.COLORED)
epd.display_frame(frame_black, frame_red)
