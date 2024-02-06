# Waveshare E-Paper 2.13" V2 display driver for devices running Micropython

This library is based on the work of 
[Mike Causer](https://github.com/mcauser/micropython-waveshare-epaper)
and [Dominik Kapusta](https://github.com/ayoy/micropython-waveshare-epd).

When I was looking for a driver for couple of Waveshare 2.13" V2 red-black displays, 
I could not find anything usable. The example in Mike's repo is only partially working,
and when I stumbled upon great library for 1.54" display, I decided to rework the lib a bit.

## Features

* Drawing lines (horizontal, vertical and between two arbitrary points)
* Drawing rectangles and circles, both regular and filled
* Drawing images from raw data (`list` or `bytes` object)
* Adjusting screen orientation
* Power saving mode (~30uA)

## Usage

### Initializing

The e-paper display uses 6 data lines for communication:

```python
from machine import Pin, SPI
from lib import epd2in13
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
```
On my module there is Reset line, and MISO is obviously not used in the communication.
### Displaying data

Please see `main.py` for an example usage.
In order to use fonts, copy them to `fonts` directory, or if you feel adventurous, 
freeze them in firmware. See [this great blog post](https://kapusta.cc/2018/03/31/epd/) from  Dominik
for more info on how to do it.