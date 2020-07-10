# Basic effects; such as color wipe, pulse etc.
from __future__ import absolute_import, unicode_literals
from octoprint_rgb_led_status.util import milli_sleep, wheel


DIRECTIONS = ['forward', 'backward']  # Used for effects that go 'out and back' kind of thing


def solid_color(strip, queue, color, delay=None, max_brightness=255, set_brightness=True):
    # Set pixels to a solid color
    if set_brightness:
        strip.setBrightness(max_brightness)
    for p in range(strip.numPixels()):
        strip.setPixelColorRGB(p, *color)
    strip.show()


def color_wipe(strip, queue, color, delay, max_brightness=255):
    strip.setBrightness(max_brightness)
    for i in range(strip.numPixels()):
        strip.setPixelColorRGB(i, *color)
        strip.show()
        if not queue.empty():
            return
        milli_sleep(delay)
    for i in range(strip.numPixels()):
        strip.setPixelColorRGB(i, 0, 0, 0)
        strip.show()
        if not queue.empty():
            return
        milli_sleep(delay)


def color_wipe_2(strip, queue, color, delay, max_brightness=255):
    strip.setBrightness(max_brightness)
    for direction in DIRECTIONS:
        for i in range(strip.numPixels()) if direction == 'forward' else reversed(range(strip.numPixels())):
            if direction == 'backward':
                color = (0, 0, 0)
            strip.setPixelColorRGB(i, *color)
            strip.show()
            if not queue.empty():
                return
            milli_sleep(delay)


def simple_pulse(strip, queue, color, delay, max_brightness=255):
    strip.setBrightness(1)
    solid_color(strip, queue, color, delay, max_brightness, set_brightness=False)
    for direction in DIRECTIONS:
        for b in range(max_brightness) if direction == 'forward' else reversed(range(max_brightness)):
            strip.setBrightness(b)
            strip.show()
            if not queue.empty():
                return
            milli_sleep(delay)


def rainbow(strip, queue, color, delay, max_brightness=255):
    strip.setBrightness(max_brightness)
    for i in range(256):
        solid_color(strip, queue, wheel(i), delay, max_brightness, False)
        if not queue.empty():
            return
        milli_sleep(delay)


def rainbow_cycle(strip, queue, color, delay, max_brightness=255):
    strip.setBrightness(max_brightness)
    for j in range(256):
        for i in range(strip.numPixels()):
            strip.setPixelColorRGB(i, *wheel(
                (int(i * 256 / strip.numPixels()) + j) & 255))
        strip.show()
        if not queue.empty():
            return
        milli_sleep(delay)


def bounce(strip, queue, color, delay, max_brightness=255):
    for direction in DIRECTIONS:
        for i in range(strip.numPixels() - 2) if direction == 'forward' else reversed(range(strip.numPixels() - 2)):
            active_pixels = [i, i + 1, i + 2]
            for active in active_pixels:
                strip.setPixelColorRGB(max(active, 0), *color)
            for blank in range(strip.numPixels()):
                if blank not in active_pixels:
                    strip.setPixelColorRGB(blank, 0, 0, 0)
            strip.show()
            if not queue.empty():
                return
            milli_sleep(delay)

