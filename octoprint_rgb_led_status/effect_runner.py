# run the effect, handle switching from queue.
# Should be run as a thread
from __future__ import absolute_import, unicode_literals

import time

import rpi_ws281x
from rpi_ws281x import PixelStrip
from octoprint_rgb_led_status.effects import basic, progress
from octoprint_rgb_led_status.util import hex_to_rgb

KILL_MSG = 'KILL'
STRIP_SETTINGS = [  # ALL LED SETTINGS, for rpi_ws281x.PixelStrip
    'led_count',
    'led_pin',
    'led_freq_hz',
    'led_dma',
    'led_invert',
    'led_brightness',
    'led_channel',
    'strip_type'
]
STRIP_TYPES = {  # Add more here once we get going....
    'WS2811_STRIP_GRB': rpi_ws281x.WS2811_STRIP_GRB
}
EFFECTS = {  # Add more here once we get going....
    'solid': basic.solid_color,
    'wipe': basic.color_wipe,
    'print_progress': progress.print_progress
}
MODES = [  # Add more here once we get going.... (Duplicate of MODES in __init__.py?)
    'startup',
    'idle',
    'progress_print'
]


def effect_runner(logger, queue, all_settings):
    # start strip, run startup effect until we get something else
    strip = start_strip(logger, all_settings['strip'])
    if not strip:
        logger.debug("[RUNNER] Exiting effect runner")
        return

    msg = None
    state = None
    while True:
        if not queue.empty():
            msg = queue.get()  # The ONLY place the queue should be 'got'
        if msg:
            # Run messaged effect
            if msg == KILL_MSG:
                logger.debug("[RUNNER] Received KILL message")
                return
            elif msg == 'shutdown':
                EFFECTS['solid'](strip, queue, [0, 0, 0])
            elif msg.split()[0] in MODES:
                effect_settings = all_settings[msg.split()[0]]  # dict containing 'enabled', 'effect', 'color', 'delay'/'base'
                if 'progress' in msg:
                    value = msg.split()[1]
                    EFFECTS[msg.split()[0]](strip, queue, value, hex_to_rgb(effect_settings['color']),
                                            hex_to_rgb(effect_settings['base']))
                else:
                    EFFECTS[effect_settings['effect']](strip, queue, hex_to_rgb(effect_settings['color']),
                                                       effect_settings['delay'])
        else:
            effect_settings = all_settings['startup']
            # Run startup effect (We haven't got a message yet)
            EFFECTS[effect_settings['effect']](strip, queue, hex_to_rgb(effect_settings['color']),
                                               effect_settings['delay'])
            if not queue.empty():
                time.sleep(0.1)


def start_strip(logger, strip_settings):
    try:
        strip = PixelStrip(
            num=strip_settings['led_count'],
            pin=strip_settings['led_pin'],
            freq_hz=strip_settings['led_freq_hz'],
            dma=strip_settings['led_dma'],
            invert=strip_settings['led_invert'],
            brightness=strip_settings['led_brightness'],
            channel=strip_settings['led_channel'],
            strip_type=STRIP_TYPES[strip_settings['strip_type']]
        )
        strip.begin()
        logger.debug("Strip object initialised")
        return strip
    except Exception as e:  # Probably wrong settings...
        logger.warning("[RUNNER] Strip failed to initialize, no effects will be run.")
        logger.warning("[RUNNER] Exception: {}".format(e))
        return None
