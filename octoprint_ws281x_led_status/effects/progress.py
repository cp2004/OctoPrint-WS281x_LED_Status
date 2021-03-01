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
    brightness_manager,
    value,
    progress_color,
    base_color,
    reverse,
    *args,
    **kwargs
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
    strip, queue, value, brightness_manager, progress_color, base_color, *args, **kwargs
):
    brightness_manager.reset_brightness()

    color = blend_two_colors(progress_color, base_color, float(value) / 100)

    for i in range(strip.numPixels()):
        strip.setPixelColorRGB(i, *color)

    strip.show()
    if not q_poll_sleep(0.1, queue):
        return


def single_pixel(
    strip, queue, brightness_manager, value, progress_color, base_color, *args, **kwargs
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


def both_ends(
    strip, queue, brightness_manager, value, progress_color, base_color, *args, **kwargs
):
    brightness_manager.reset_brightness()
    num_pixels = strip.numPixels()
    if num_pixels % 2 != 0:
        num_pixels -= 1

    def progress(min_pixel, max_pixel, val, reverse):
        number_pixels = max_pixel - min_pixel
        print(reverse)
        upper_bar = (val / 100) * number_pixels
        upper_remainder, upper_whole = math.modf(upper_bar)
        pixels_remaining = number_pixels

        for i in range(int(upper_whole)):
            pixel = ((max_pixel - 1) - i) if reverse else i
            strip.setPixelColorRGB(pixel, *progress_color)
            pixels_remaining -= 1
            print("bottom" + str(pixel) if not reverse else "top" + str(pixel))

        if upper_remainder > 0.0:
            tween_color = blend_two_colors(progress_color, base_color, upper_remainder)
            pixel = (
                ((max_pixel - int(upper_whole)) - 1) if reverse else int(upper_whole)
            )
            strip.setPixelColorRGB(pixel, *tween_color)
            pixels_remaining -= 1
            print("bottom" + str(pixel) if not reverse else "top" + str(pixel))

        for i in range(pixels_remaining):
            pixel = (
                ((min_pixel + pixels_remaining - 1) - i)
                if reverse
                else ((number_pixels - pixels_remaining) + i)
            )
            strip.setPixelColorRGB(pixel, *base_color)
            print("bottom" + str(pixel) if not reverse else "top" + str(pixel))

    # Set the progress to either end of the strip

    progress(0, num_pixels // 2, value, False)
    progress(num_pixels // 2, num_pixels, value, True)

    strip.show()
    if not q_poll_sleep(0.1, queue):
        return
