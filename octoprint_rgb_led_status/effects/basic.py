# Basic effects; such as color wipe, pulse etc.
from __future__ import absolute_import, unicode_literals
import time

def solid_color(strip, queue, color, delay=None):
    # Set pixels to a solid color
    for p in range(strip.numPixels()):
        strip.setPixelColorRGB(p, *color)
    strip.show()


def color_wipe(strip, queue, color, delay):
    for i in range(strip.numPixels()):
        strip.setPixelColorRGB(i, *color)
        strip.show()
        if not queue.empty():
            return
        time.sleep(delay / 1000.0)
    for i in range(strip.numPixels()):
        strip.setPixelColorRGB(i, 0, 0, 0)
        strip.show()
        if not queue.empty():
            return
        time.sleep(delay / 1000.0)
