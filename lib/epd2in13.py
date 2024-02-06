"""
Minimalistic MicroPython driver for Waveshare 2.13" V2 Black/Red/White (212x104) e-paper display.

Based on work of
* Mike Causer https://github.com/mcauser/micropython-waveshare-epaper
* Dominik Kapusta https://github.com/ayoy/micropython-waveshare-epd

MIT License
Copyright (c) 2017 Waveshare
Copyright (c) 2018 Mike Causer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import utime
import ustruct

# Display resolution
EPD_WIDTH = 104
EPD_HEIGHT = 212

# Commands
PANEL_SETTING = 0x00
POWER_SETTING = 0x01
POWER_OFF = 0x02
POWER_ON = 0x04
BOOSTER_SOFT_START = 0x06
DATA_START_TRANSMISSION_1 = 0x10
DISPLAY_REFRESH = 0x12
DATA_START_TRANSMISSION_2 = 0x13
VCOM_AND_DATA_INTERVAL_SETTING = 0x50
TCON_RESOLUTION = 0x61
VCM_DC_SETTING_REGISTER = 0x82

# Color or no color
COLORED = 1
UNCOLORED = 0

# Display orientation
ROTATE_0 = 0
ROTATE_90 = 1
ROTATE_180 = 2
ROTATE_270 = 3


class EPD:
    def __init__(self, spi, cs, dc, rst, busy):
        self.rst = rst
        self.rst.init(self.rst.OUT, value=0)

        self.dc = dc
        self.dc.init(self.dc.OUT, value=0)

        self.busy = busy
        self.busy.init(self.busy.IN)

        self.cs = cs
        self.cs.init(self.cs.OUT, value=1)

        self.spi = spi

        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.rotate = ROTATE_0

    def init(self):
        self.reset()
        self.send_command(BOOSTER_SOFT_START, b'\x17\x17\x17')
        self.send_command(POWER_ON)
        self.wait_until_idle()
        self.send_command(PANEL_SETTING, b'\x8F')
        self.send_command(VCOM_AND_DATA_INTERVAL_SETTING, b'\x37')
        self.send_command(TCON_RESOLUTION, ustruct.pack(">BH", EPD_WIDTH, EPD_HEIGHT))
        return 0

    def delay_ms(self, delaytime):
        utime.sleep_ms(delaytime)

    def send_command(self, command, data=None):
        self.dc(False)
        self.cs(False)
        self.spi.write(bytearray([command]))
        self.cs(True)
        if data is not None:
            self.send_data(data)

    def send_data(self, data):
        self.dc(True)
        self.cs(False)
        if isinstance(data, bytes):
            self.spi.write(bytearray(data))
        else:
            self.spi.write(bytearray([data]))
        self.cs(True)

    def wait_until_idle(self):
        while not self.busy():
            self.delay_ms(100)

    def reset(self):
        self.rst(False)  # module reset
        self.delay_ms(200)
        self.rst(True)
        self.delay_ms(200)

    def clear_frame(self, frame_buffer_black, frame_buffer_red=None):
        for i in range(int(self.width * self.height / 8)):
            frame_buffer_black[i] = 0xFF
            if frame_buffer_red is not None:
                frame_buffer_red[i] = 0xFF

    def display_frame(self, frame_buffer_black, frame_buffer_red=None):
        if frame_buffer_black is not None:
            self.send_command(DATA_START_TRANSMISSION_1)
            self.delay_ms(2)
            for i in range(0, self.width * self.height // 8):
                self.send_data(frame_buffer_black[i])
            self.delay_ms(2)
        if frame_buffer_red is not None:
            self.send_command(DATA_START_TRANSMISSION_2)
            self.delay_ms(2)
            for i in range(0, self.width * self.height // 8):
                self.send_data(frame_buffer_red[i])
            self.delay_ms(2)

        self.send_command(DISPLAY_REFRESH)
        self.wait_until_idle()

    # after this, call epd.init() to awaken the module
    def sleep(self):
        self.send_command(VCOM_AND_DATA_INTERVAL_SETTING, b'\x37')
        self.send_command(VCM_DC_SETTING_REGISTER, b'\x00')  # to solve Vcom drop
        self.send_command(POWER_SETTING, b'\x02\x00\x00\x00')
        self.wait_until_idle()
        self.send_command(POWER_OFF)  # power off

    def set_rotate(self, rotate):
        if rotate == ROTATE_0:
            self.rotate = ROTATE_0
            self.width = EPD_WIDTH
            self.height = EPD_HEIGHT
        elif rotate == ROTATE_90:
            self.rotate = ROTATE_90
            self.width = EPD_HEIGHT
            self.height = EPD_WIDTH
        elif rotate == ROTATE_180:
            self.rotate = ROTATE_180
            self.width = EPD_WIDTH
            self.height = EPD_HEIGHT
        elif rotate == ROTATE_270:
            self.rotate = ROTATE_270
            self.width = EPD_HEIGHT
            self.height = EPD_WIDTH

    def set_pixel(self, frame_buffer, x, y, colored):
        if (x < 0 or x >= self.width or y < 0 or y >= self.height):
            return
        if (self.rotate == ROTATE_0):
            self.set_absolute_pixel(frame_buffer, x, y, colored)
        elif (self.rotate == ROTATE_90):
            point_temp = x
            x = EPD_WIDTH - y
            y = point_temp
            self.set_absolute_pixel(frame_buffer, x, y, colored)
        elif (self.rotate == ROTATE_180):
            x = EPD_WIDTH - x
            y = EPD_HEIGHT - y
            self.set_absolute_pixel(frame_buffer, x, y, colored)
        elif (self.rotate == ROTATE_270):
            point_temp = x
            x = y
            y = EPD_HEIGHT - point_temp
            self.set_absolute_pixel(frame_buffer, x, y, colored)

    def set_absolute_pixel(self, frame_buffer, x, y, colored):
        if x < 0 or x >= EPD_WIDTH or y < 0 or y >= EPD_HEIGHT:
            return
        if colored:
            frame_buffer[int((x + y * EPD_WIDTH) / 8)] &= ~(0x80 >> (x % 8))
        else:
            frame_buffer[int((x + y * EPD_WIDTH) / 8)] |= 0x80 >> (x % 8)

    def draw_char_at(self, frame_buffer, x, y, char, font, colored):
        char_offset = (ord(char) - ord(' ')) * font.height * (int(font.width / 8) + (1 if font.width % 8 else 0))
        offset = 0

        for j in range(font.height):
            for i in range(font.width):
                if font.data[char_offset + offset] & (0x80 >> (i % 8)):
                    self.set_pixel(frame_buffer, x + i, y + j, colored)
                if i % 8 == 7:
                    offset += 1
            if font.width % 8 != 0:
                offset += 1

    def display_string_at(self, frame_buffer, x, y, text, font, colored):
        refcolumn = x

        # Send the string character by character on EPD
        for index in range(len(text)):
            # Display one character on EPD
            self.draw_char_at(frame_buffer, refcolumn, y, text[index], font, colored)
            # Decrement the column position by 16
            refcolumn += font.width

    def draw_line(self, frame_buffer, x0, y0, x1, y1, colored):
        # Bresenham algorithm
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while (x0 != x1) and (y0 != y1):
            self.set_pixel(frame_buffer, x0, y0, colored)
            if 2 * err >= dy:
                err += dy
                x0 += sx
            if 2 * err <= dx:
                err += dx
                y0 += sy

    def draw_horizontal_line(self, frame_buffer, x, y, width, colored):
        for i in range(x, x + width):
            self.set_pixel(frame_buffer, i, y, colored)

    def draw_vertical_line(self, frame_buffer, x, y, height, colored):
        for i in range(y, y + height):
            self.set_pixel(frame_buffer, x, i, colored)

    def draw_rectangle(self, frame_buffer, x0, y0, x1, y1, colored):
        min_x = x0 if x1 > x0 else x1
        max_x = x1 if x1 > x0 else x0
        min_y = y0 if y1 > y0 else y1
        max_y = y1 if y1 > y0 else y0
        self.draw_horizontal_line(frame_buffer, min_x, min_y, max_x - min_x + 1, colored)
        self.draw_horizontal_line(frame_buffer, min_x, max_y, max_x - min_x + 1, colored)
        self.draw_vertical_line(frame_buffer, min_x, min_y, max_y - min_y + 1, colored)
        self.draw_vertical_line(frame_buffer, max_x, min_y, max_y - min_y + 1, colored)

    def draw_filled_rectangle(self, frame_buffer, x0, y0, x1, y1, colored):
        min_x = x0 if x1 > x0 else x1
        max_x = x1 if x1 > x0 else x0
        min_y = y0 if y1 > y0 else y1
        max_y = y1 if y1 > y0 else y0
        for i in range(min_x, max_x + 1):
            self.draw_vertical_line(frame_buffer, i, min_y, max_y - min_y + 1, colored)

    def draw_circle(self, frame_buffer, x, y, radius, colored):
        # Bresenham algorithm
        x_pos = -radius
        y_pos = 0
        err = 2 - 2 * radius
        if (x >= self.width or y >= self.height):
            return
        while True:
            self.set_pixel(frame_buffer, x - x_pos, y + y_pos, colored)
            self.set_pixel(frame_buffer, x + x_pos, y + y_pos, colored)
            self.set_pixel(frame_buffer, x + x_pos, y - y_pos, colored)
            self.set_pixel(frame_buffer, x - x_pos, y - y_pos, colored)
            e2 = err
            if e2 <= y_pos:
                y_pos += 1
                err += y_pos * 2 + 1
                if -x_pos == y_pos and e2 <= x_pos:
                    e2 = 0
            if e2 > x_pos:
                x_pos += 1
                err += x_pos * 2 + 1
            if x_pos > 0:
                break

    def draw_filled_circle(self, frame_buffer, x, y, radius, colored):
        # Bresenham algorithm
        x_pos = -radius
        y_pos = 0
        err = 2 - 2 * radius
        if (x >= self.width or y >= self.height):
            return
        while True:
            self.set_pixel(frame_buffer, x - x_pos, y + y_pos, colored)
            self.set_pixel(frame_buffer, x + x_pos, y + y_pos, colored)
            self.set_pixel(frame_buffer, x + x_pos, y - y_pos, colored)
            self.set_pixel(frame_buffer, x - x_pos, y - y_pos, colored)
            self.draw_horizontal_line(frame_buffer, x + x_pos, y + y_pos, 2 * (-x_pos) + 1, colored)
            self.draw_horizontal_line(frame_buffer, x + x_pos, y - y_pos, 2 * (-x_pos) + 1, colored)
            e2 = err
            if (e2 <= y_pos):
                y_pos += 1
                err += y_pos * 2 + 1
                if (-x_pos == y_pos and e2 <= x_pos):
                    e2 = 0
            if (e2 > x_pos):
                x_pos += 1
                err += x_pos * 2 + 1
            if x_pos > 0:
                break
