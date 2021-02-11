# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

__author__ = "Charlie Powell <cp2004.github@gmail.com"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Charlie Powell 2020-2021 - released under the terms of the AGPLv3 License"

import math
import random
import time

from octoprint_ws281x_led_status.util import q_poll_milli_sleep, wheel

DIRECTIONS = [
    "forward",
    "backward",
]  # Used for effects that go 'out and back' kind of thing


def solid_color(
    strip, queue, color, brightness_manager, wait=True, show=True, *args, **kwargs
):
    brightness_manager.reset_brightness()
    # Set pixels to a solid color
    for p in range(strip.numPixels()):
        strip.setPixelColorRGB(p, *color)
    if show:
        strip.show()

    while wait:
        if not q_poll_milli_sleep(100, queue):
            return


def color_wipe(strip, queue, color, delay, brightness_manager, *args, **kwargs):
    while True:
        brightness_manager.reset_brightness()
        for i in range(strip.numPixels()):
            strip.setPixelColorRGB(i, *color)
            strip.show()
            if not q_poll_milli_sleep(delay, queue):
                return
        for i in range(strip.numPixels()):
            strip.setPixelColorRGB(i, 0, 0, 0)
            strip.show()
            if not q_poll_milli_sleep(delay, queue):
                return


def color_wipe_2(strip, queue, color, delay, brightness_manager, *args, **kwargs):
    while True:
        brightness_manager.reset_brightness()
        for direction in DIRECTIONS:
            for i in (
                range(strip.numPixels())
                if direction == "forward"
                else reversed(range(strip.numPixels()))
            ):
                if direction == "backward":
                    color = (0, 0, 0)
                strip.setPixelColorRGB(i, *color)
                strip.show()
                if not q_poll_milli_sleep(delay, queue):
                    return


def simple_pulse(strip, queue, color, delay, brightness_manager, *args, **kwargs):
    while True:
        max_brightness = brightness_manager.max_brightness
        brightness_manager.set_brightness(1)
        solid_color(
            strip=strip,
            queue=queue,
            color=color,
            brightness_manager=brightness_manager,
            wait=False,
        )

        for direction in DIRECTIONS:
            for b in (
                range(max_brightness)
                if direction == "forward"
                else reversed(range(max_brightness))
            ):
                brightness_manager.set_brightness(b)

                if not q_poll_milli_sleep(delay, queue):
                    return


def rainbow(strip, queue, color, delay, brightness_manager, *args, **kwargs):
    while True:
        for i in range(256):
            solid_color(
                strip=strip,
                queue=queue,
                color=wheel(i),
                delay=delay,
                wait=False,
                brightness_manager=brightness_manager,
            )
            if not q_poll_milli_sleep(delay, queue):
                return


def rainbow_cycle(strip, queue, color, delay, brightness_manager, *args, **kwargs):
    while True:
        brightness_manager.reset_brightness()
        for j in range(256):
            for i in range(strip.numPixels()):
                strip.setPixelColorRGB(
                    i, *wheel((int(i * 256 / strip.numPixels()) + j) & 255)
                )
            strip.show()
            if not q_poll_milli_sleep(delay, queue):
                return


def solo_bounce(strip, queue, color, delay, brightness_manager, *args, **kwargs):
    while True:
        brightness_manager.reset_brightness()
        for direction in DIRECTIONS:
            for i in (
                range(strip.numPixels())
                if direction == "forward"
                else reversed(range(strip.numPixels()))
            ):
                solid_color(
                    strip=strip,
                    queue=queue,
                    color=(0, 0, 0),
                    brightness_manager=brightness_manager,
                    wait=False,
                    show=False,
                )
                strip.setPixelColorRGB(i, *color)
                strip.show()
                if not q_poll_milli_sleep(delay, queue):
                    return


def bounce(strip, queue, color, delay, brightness_manager, *args, **kwargs):
    while True:
        brightness_manager.reset_brightness()
        red, green, blue, white = color
        size = 3
        for direction in DIRECTIONS:
            for i in (
                range(0, (strip.numPixels() - size - 2))
                if direction == "forward"
                else range((strip.numPixels() - size - 2), 0, -1)
            ):
                solid_color(
                    strip=strip,
                    queue=queue,
                    color=(0, 0, 0),
                    brightness_manager=brightness_manager,
                    wait=False,
                    show=False,
                )
                strip.setPixelColorRGB(
                    i,
                    *(
                        int(math.floor(red / 10)),
                        int(math.floor(green / 10)),
                        int(math.floor(blue / 10)),
                        int(math.floor(white / 10)),
                    )
                )
                for j in range(1, (size + 1)):
                    strip.setPixelColorRGB(i + j, *(red, green, blue))
                strip.setPixelColorRGB(
                    i + size + 1,
                    *(
                        int(math.floor(red / 10)),
                        int(math.floor(green / 10)),
                        int(math.floor(blue / 10)),
                        int(math.floor(white / 10)),
                    )
                )
                strip.show()
                if not q_poll_milli_sleep(delay, queue):
                    return


def random_single(strip, queue, color, delay, brightness_manager, *args, **kwargs):
    while True:
        brightness_manager.reset_brightness()
        for p in range(strip.numPixels()):
            strip.setPixelColorRGB(p, *wheel(random.randint(0, 255)))
        strip.show()
        while True:
            strip.setPixelColorRGB(
                random.randint(0, strip.numPixels()), *wheel(random.randint(0, 255))
            )
            strip.show()
            if not q_poll_milli_sleep(delay, queue):
                return


def blink(strip, queue, color, delay, brightness_manager, *args, **kwargs):
    while True:
        for direction in DIRECTIONS:
            solid_color(
                strip=strip,
                queue=queue,
                color=color if direction == "forward" else (0, 0, 0),
                brightness_manager=brightness_manager,
                wait=False,
            )
            for _ms in range(int(delay / 2)):
                if not q_poll_milli_sleep(2, queue):
                    # We do it this way so we can check the q more often, as for blink
                    # delay may be high. Otherwise the effect may end up blocking the
                    # server, when settings are saved, or it shuts down.
                    return


def crossover(strip, queue, color, delay, brightness_manager, *args, **kwargs):
    while True:
        brightness_manager.reset_brightness()
        num_pixels = strip.numPixels()
        if num_pixels % 2 != 1:
            # We need an odd number of pixels
            num_pixels -= 1

        for i in range(num_pixels):
            solid_color(
                strip=strip,
                queue=queue,
                color=(0, 0, 0),
                brightness_manager=brightness_manager,
                wait=False,
                show=False,
            )
            strip.setPixelColorRGB(i, *color)
            strip.setPixelColorRGB(num_pixels - 1 - i, *color)
            strip.show()
            if not q_poll_milli_sleep(delay, queue):
                return


# Credit to https://www.tweaking4all.com/hardware/arduino/adruino-led-strip-effects/#LEDStripEffectBouncingBalls
# Translated from c++ to Python by me
def bouncy_balls(strip, queue, color, delay, brightness_manager, *args, **kwargs):
    brightness_manager.reset_brightness()
    ball_count = 2
    gravity = -9.81
    start_height = 1

    height = []
    impact_velocity_start = math.sqrt(-2 * gravity * start_height)
    impact_velocity = []
    time_since_last_bounce = []
    position = []
    clock_time_since_last_bounce = []
    dampening = []

    for i in range(ball_count):
        clock_time_since_last_bounce.append(time.time() * 1000)
        time_since_last_bounce.append(0)
        height.append(start_height)
        position.append(0)
        impact_velocity.append(impact_velocity_start)
        dampening.append(0.9 - (i / math.pow(ball_count, 2)))

    while True:
        for i in range(ball_count):
            time_since_last_bounce[i] = (
                time.time() * 1000 - clock_time_since_last_bounce[i]
            )
            height[i] = (
                0.5 * gravity * math.pow(time_since_last_bounce[i] / 1000, 2)
                + impact_velocity[i] * time_since_last_bounce[i] / 1000
            )

            if height[i] < 0:
                height[i] = 0
                impact_velocity[i] = dampening[i] * impact_velocity[i]
                clock_time_since_last_bounce[i] = time.time() * 1000

                if impact_velocity[i] < 0.01:
                    impact_velocity[i] = impact_velocity_start

            position[i] = int(round(height[i] * (strip.numPixels() - 1) / start_height))

        for p in range(strip.numPixels()):
            # Set to blank
            strip.setPixelColorRGB(p, 0, 0, 0)

        for i in range(ball_count):
            # Light pixels that should be lit
            strip.setPixelColorRGB(position[i], *color)

        strip.show()
        if not q_poll_milli_sleep(delay, queue):
            return
