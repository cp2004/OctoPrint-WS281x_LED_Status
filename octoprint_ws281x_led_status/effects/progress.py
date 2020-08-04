# Print and heat up progress?
from __future__ import absolute_import, unicode_literals, division
import math
import time

from octoprint_ws281x_led_status.util import blend_two_colors


def progress(strip, queue, value, progress_color, base_color, max_brightness=255):
    strip.setBrightness(max_brightness)
    num_pixels = strip.numPixels()
    upper_bar = (value / 100) * num_pixels
    upper_remainder, upper_whole = math.modf(upper_bar)
    lower_base = ((100 - value) / 100) * num_pixels
    lower_remainder, lower_whole = math.modf(lower_base)
    if int(upper_bar + lower_base) != strip.numPixels():
        log.info("Progress sanity check failed!, (bar)%s +  (base)%s = (total)%s != (strip)%s", upper_bar, lower_base, upper_bar + lower_base, strip.numPixels())
    for i in range(int(upper_whole)):
        strip.setPixelColorRGB(i, *progress_color)
    if upper_remainder:
        tween_color = blend_two_colors(progress_color, base_color, upper_remainder)
        strip.setPixelColorRGB(int(upper_whole), *tween_color)
    for i in range(int(lower_whole)):
        strip.setPixelColorRGB(((num_pixels - 1) - i), *base_color)
    log.info('Show strip')
    strip.show()
    time.sleep(0.1)
