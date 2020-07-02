# run the effect, handle switching from queue.
# Should be run as a thread
from __future__ import absolute_import, unicode_literals
import time

import rpi_ws281x
from rpi_ws281x import PixelStrip
from effects import basic, progress


STRIP_SETTINGS = [  # LED SETTINGS...
    'led_count',
    'led_pin',
    'led_freq_hz',
    'led_dma',
    'led_invert',
    'led_brightness',
    'led_channel',
    'strip_type'
]

EFFECT_SETTINGS = [
    ''
]

STRIP_TYPES = {  # Add more here once we get going....
    'WS2811_STRIP_GRB': rpi_ws281x.WS2811_STRIP_GRB
}

EFFECTS = {
    'solid': basic.solid_color,
    'wipe': basic.color_wipe
}

MODES = [
    'startup',
    'idle',
    'progress'
]


def effect_runner(logger, queue, settings):
    # start strip, run startup effect until we get something else
    strip_settings = []
    for setting in STRIP_SETTINGS:
        strip_settings.append(settings.get(setting))
    try:
        strip = PixelStrip(*strip_settings)
        strip.begin()
    except Exception as e:  # Just in case
        logger.warning("Strip failed to initialize, no effects will be run.")
        logger.warning("Exception: {}".format(e))

    lights_on = True
    cmd = None
    while True:
        msg = queue.get()
        if msg == 'KILL':
            return
        elif msg == 'OFF':
            lights_on = False
        elif msg == 'ON':
            lights_on = True
        elif msg:
            cmd = msg.split()

        while not queue.empty():
            if cmd[0] == 'progress':
                # Run progress effect or heatup effect
                pass
            else:
                # Run the effect
                while lights_on:
                    EFFECTS[cmd](strip, queue, color, delay)

def parse_settings(settings):
    strip_settings = []
    for setting in STRIP_SETTINGS:
        strip_settings.append(settings.get(setting))

    for setting in EFFECT_SETTINGS:
        split_setting = setting.split("_")

    return strip_settings, effect_settings