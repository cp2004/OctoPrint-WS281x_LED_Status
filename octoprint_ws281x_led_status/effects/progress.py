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
    *args,
    **kwargs
):
    progress_bar_impl(strip, queue, brightness_manager, value, progress_color, base_color, False, False)


def progress_bar_from_both_ends(
    strip,
    queue,
    brightness_manager,
    value,
    progress_color,
    base_color,
    *args,
    **kwargs
):
    progress_bar_impl(strip, queue, brightness_manager, value, progress_color, base_color, False, True)


def progress_bar_from_center(
    strip,
    queue,
    brightness_manager,
    value,
    progress_color,
    base_color,
    *args,
    **kwargs
):
    progress_bar_impl(strip, queue, brightness_manager, value, progress_color, base_color, True, True)


def progress_bar_reversed(
    strip,
    queue,
    brightness_manager,
    value,
    progress_color,
    base_color,
    *args,
    **kwargs
):
    progress_bar_impl(strip, queue, brightness_manager, value, progress_color, base_color, True, False)


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


def progress_bar_impl(
    strip,
    queue,
    brightness_manager,
    value,
    progress_color,
    base_color,
    reverse,
    half_strip,
    *args,
    **kwargs
):
    brightness_manager.reset_brightness()
    num_pixels = strip.numPixels()
    odd_pixel = 0
    if num_pixels % 2 != 0:
        odd_pixel = 1

    def progress(min_pixel, max_pixel, val, reverse_progress):
        number_pixels = max_pixel - min_pixel
        upper_bar = (val / 100) * number_pixels
        upper_remainder, upper_whole = math.modf(upper_bar)
        pixels_remaining = number_pixels

        for i in range(int(upper_whole)):
            pixel = ((max_pixel - 1) - i) if reverse_progress else (min_pixel + i)
            strip.setPixelColorRGB(pixel, *progress_color)
            pixels_remaining -= 1

        if upper_remainder > 0.0:
            tween_color = blend_two_colors(progress_color, base_color, upper_remainder)
            pixel = (
                ((max_pixel - int(upper_whole)) - 1) if reverse_progress else (int(upper_whole) + min_pixel)
            )
            strip.setPixelColorRGB(pixel, *tween_color)
            pixels_remaining -= 1

        for i in range(pixels_remaining):
            pixel = (
                ((min_pixel + pixels_remaining - 1) - i)
                if reverse_progress
                else (min_pixel + (number_pixels - pixels_remaining) + i)
            )
            strip.setPixelColorRGB(pixel, *base_color)

    if half_strip:
        # Set the progress to either end of the strip
        progress(0, math.floor(num_pixels / 2) + odd_pixel, value, reverse)
        progress(math.ceil(num_pixels / 2) - odd_pixel, num_pixels, value, not reverse)
    else:
        # Set the progress for the entire strip
        progress(0, num_pixels, value, reverse)

    strip.show()
    if not q_poll_sleep(0.1, queue):
        return
