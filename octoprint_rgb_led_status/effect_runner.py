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
    'progress_print': progress.progress,
    'progress_heatup': progress.progress
}  # TODO Add more effects!
MODES = [  # Add more here once we get going....
    'startup',
    'idle',
    'disconnected',
    'progress_print',
    'progress_heatup',
    'failed',
    'success',
    'paused'
]


def effect_runner(logger, queue, all_settings, previous_state):
    def on_exit(led_strip):
        EFFECTS['solid'](strip, queue, [0, 0, 0])
        return

    print("[RUNNER] Hello!")
    # start strip, run startup effect until we get something else
    strip = start_strip(logger, all_settings['strip'])
    if not strip:
        print("[RUNNER] Exiting effect runner")
        return

    msg = previous_state
    try:
        while True:
            if not queue.empty():
                msg = queue.get()  # The ONLY place the queue should be 'got'
            if msg:
                msg_split = msg.split()
                # Run messaged effect
                if msg == KILL_MSG:
                    print("[RUNNER] Received KILL message")
                    on_exit(strip)
                    return
                elif msg_split[0] in MODES:
                    effect_settings = all_settings[msg_split[0]]  # dict containing 'enabled', 'effect', 'color', 'delay'/'base'
                    if 'progress' in msg:
                        value = msg_split[1]
                        EFFECTS[msg_split[0]](strip, queue, int(value), hex_to_rgb(effect_settings['color']),
                                              hex_to_rgb(effect_settings['base']))
                    else:
                        EFFECTS[effect_settings['effect']](strip, queue, hex_to_rgb(effect_settings['color']),
                                                           effect_settings['delay'])
                else:
                    time.sleep(0.1)
            else:
                effect_settings = all_settings['startup']
                if effect_settings['enabled']:
                    # Run startup effect (We haven't got a message yet)
                    EFFECTS[effect_settings['effect']](strip, queue, hex_to_rgb(effect_settings['color']),
                                                       effect_settings['delay'])
                if not queue.empty():
                    time.sleep(0.1)
    except KeyboardInterrupt:
        on_exit(strip)
        return


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
        print("Strip object initialised")
        return strip
    except Exception as e:  # Probably wrong settings...
        print("[RUNNER] Strip failed to initialize, no effects will be run.")
        print("[RUNNER] Exception: {}".format(e))
        return None


class FakeStrip:
    def __init__(self, num, pin, freq_hz, dma, invert, brightness, channel, strip_type):
        self.pixels = num
        self.pin = pin
        self.freq_hz = freq_hz
        self.dma = dma
        self.invert = invert
        self.brightness = brightness
        self.channel = channel
        self.strip_type = strip_type

    def numPixels(self):
        return self.pixels

    def begin(self):
        pass

    def show(self):
        pass

    def setPixelColorRGB(self, num, red, green, blue, white=0):
        pass

    def _cleanup(self):
        print("Cleaning up FakeStrip")
        pass
