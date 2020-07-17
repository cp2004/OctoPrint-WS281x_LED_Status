# Print and heat up progress?
from __future__ import absolute_import, unicode_literals, division
import time

from octoprint_ws281x_led_status.util import blend_two_colors


def progress(strip, queue, value, progress_color, base_color, max_brightness=255):
    strip.setBrightness(max_brightness)
    num_pixels = strip.numPixels()
    upper_bar = int(round((value / 100) * num_pixels))
    lower_base = int(round(((100 - value) / 100) * num_pixels))
    if upper_bar + lower_base != strip.numPixels():
        print("Progress sanity check failed!, (bar){} +  (base){} = (total){} != (strip){}".format(
            upper_bar, lower_base, upper_bar + lower_base, strip.numPixels()))
    for i in range(upper_bar):
        strip.setPixelColorRGB(i, *progress_color)
    for i in range(lower_base):
        strip.setPixelColorRGB(((num_pixels - 1) - i), *base_color)
    strip.show()
    time.sleep(0.1)
