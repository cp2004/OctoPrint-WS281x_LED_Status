# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

__author__ = "Charlie Powell <cp2004.github@gmail.com"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Charlie Powell 2020-2021 - released under the terms of the AGPLv3 License"

import math

from octoprint_ws281x_led_status.util import blend_two_colors, q_poll_sleep


def progress_bar(
    strip,
    queue,
    value,
    progress_color,
    base_color,
    max_brightness,
    reverse,
    brightness_manager,
):
    brightness_manager.reset_brightness()
    num_pixels = strip.numPixels()
    upper_bar = (value / 100) * num_pixels
    upper_remainder, upper_whole = math.modf(upper_bar)
    pixels_remaining = num_pixels

    for i in range(int(upper_whole)):
        pixel = ((num_pixels - 1) - i) if reverse else i
        strip.setPixelColorRGB(pixel, *progress_color)
        pixels_remaining -= 1

    if upper_remainder > 0.0:
        tween_color = blend_two_colors(progress_color, base_color, upper_remainder)
        pixel = ((num_pixels - int(upper_whole)) - 1) if reverse else int(upper_whole)
        strip.setPixelColorRGB(pixel, *tween_color)
        pixels_remaining -= 1

    for i in range(pixels_remaining):
        pixel = (
            ((pixels_remaining - 1) - i)
            if reverse
            else ((num_pixels - pixels_remaining) + i)
        )
        strip.setPixelColorRGB(pixel, *base_color)

    strip.show()
    if not q_poll_sleep(0.1, queue):
        return


def gradient(
    strip,
    queue,
    value,
    progress_color,
    base_color,
    max_brightness,
    reverse,
    brightness_manager,
):
    brightness_manager.reset_brightness()

    color = blend_two_colors(progress_color, base_color, float(value) / 100)

    for i in range(strip.numPixels()):
        strip.setPixelColorRGB(i, *color)

    strip.show()
    if not q_poll_sleep(0.1, queue):
        return


def single_pixel(
    strip,
    queue,
    value,
    progress_color,
    base_color,
    max_brightness,
    reverse,
    brightness_manager,
):
    brightness_manager.reset_brightness()

    # Calculate which pixel needs to be lit
    pixel_number = int(round(float(value) / 100 * strip.numPixels(), 0))

    for i in range(strip.numPixels()):
        strip.setPixelColorRGB(i, *base_color)

    strip.setPixelColorRGB(pixel_number, *progress_color)

    strip.show()
    if not q_poll_sleep(0.1, queue):
        return
