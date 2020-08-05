from __future__ import unicode_literals

import time
import logging
import re

import rpi_ws281x
from rpi_ws281x import PixelStrip

from octoprint_ws281x_led_status.effects import basic, progress
from octoprint_ws281x_led_status.util import hex_to_rgb

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
STRIP_TYPES = {  # Adding any more strips requires a request, then testing
    'WS2811_STRIP_GRB': rpi_ws281x.WS2811_STRIP_GRB,
    'WS2812_STRIP': rpi_ws281x.WS2812_STRIP,
    'WS2811_STRIP_RGB': rpi_ws281x.WS2811_STRIP_RGB,
    'WS2811_STRIP_RBG': rpi_ws281x.WS2811_STRIP_RBG,
    'WS2811_STRIP_GBR': rpi_ws281x.WS2811_STRIP_GBR,
    'WS2811_STRIP_BGR': rpi_ws281x.WS2811_STRIP_BGR,
    'WS2811_STRIP_BRG': rpi_ws281x.WS2811_STRIP_BRG,
}
EFFECTS = {
    'solid': basic.solid_color,
    'wipe': basic.color_wipe,
    'wipe2': basic.color_wipe_2,
    'pulse': basic.simple_pulse,
    'rainbow': basic.rainbow,
    'cycle': basic.rainbow_cycle,
    'bounce': basic.bounce,
    'random': basic.random_single,
    'blink': basic.blink,
    'progress_print': progress.progress,
    'progress_heatup': progress.progress
}
MODES = [
    'startup',
    'idle',
    'disconnected',
    'progress_print',
    'progress_heatup',
    'failed',
    'success',
    'paused',
    'printing'
]
M150_REGEX = r"(^|[^A-Za-z])[Rr](?P<red>\d{1,3})|(^|[^A-Za-z])[GgUu](?P<green>\d{1,3})|(^|[^A-Za-z])[Bb](?P<blue>\d{1,3})|(^|[^A-Za-z])[Pp](?P<brightness>\d{1,3})|(^|[^A-Za-z])[Ww](?P<white>\d{1,3})"


class EffectRunner:
    def __init__(self, log_path, debug, queue, all_settings, previous_state):
        self._logger = logging.getLogger("octoprint.plugins.ws281x_led_status.debug")
        self.setup_custom_logger(log_path, debug)
        self.settings = all_settings
        self.max_brightness = all_settings['strip']['led_brightness']
        self.lights_on = True
        self.previous_state = previous_state if previous_state is not None else 'startup'

        if not self.settings['active_start'] or not self.settings['active_stop']:
            self.start_time = None
            self.end_time = None
        else:
            start = self.settings['active_start'].split(":") if self.settings['active_start'] else None
            end = self.settings['active_stop'].split(":") if self.settings['active_stop'] else None
            self.start_time = (int(start[0]) * 60) + int(start[1])
            self.end_time = (int(end[0]) * 60) + int(end[1])
        self.active_times_state = True

        self.queue = queue
        self.strip = self.start_strip()
        if not self.strip:
            self._logger.info("No strip initialised, exiting the effect process.")
            return

        self.main_loop()

    def setup_custom_logger(self, path, debug):
        from octoprint.logging.handlers import CleaningTimedRotatingFileHandler
        # Cleaning handler will remove old logs, defined by 'backupCount'
        # 'D' specifies to roll over each day
        # TODO Need to tune the number of backups kept
        effect_runner_handler = CleaningTimedRotatingFileHandler(path, when="D", backupCount=2)
        effect_runner_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
        effect_runner_handler.setLevel(logging.DEBUG)

        self._logger.addHandler(effect_runner_handler)
        self._logger.setLevel(logging.DEBUG if debug else logging.INFO)
        self._logger.propagate = False

    def main_loop(self):
        try:
            msg = self.previous_state
            while True:
                if not self.queue.empty():
                    msg = self.queue.get()  # The ONLY place the queue should be 'got'
                if msg:
                    parsed = self.parse_q_msg(msg)  # Effects are run from parse_q_msg
                    if parsed == KILL_MSG:
                        return
                    elif parsed:
                        msg = parsed  # So that previous state can return after 'lights on'
                else:
                    self.startup_effect()
        except KeyboardInterrupt:
            self.blank_leds()
            return

    def parse_q_msg(self, msg):
        if not msg:
            self.startup_effect()  # Will probably never happen, but just in case
        if msg == KILL_MSG:
            self.blank_leds()
            self._logger.info("Kill message recieved, Bye!")
            return msg
        elif msg == 'on':
            self.lights_on = True
            self._logger.info("On message recieved, turning on LEDs")
            return self.previous_state
        elif msg == 'off':
            self.lights_on = False
            self._logger.info("Off message recieved, turning off LEDs")
            return self.previous_state
        elif 'progress' in msg:
            msg_split = msg.split()
            self.progress_effect(msg_split[0], float(msg_split[1]))
            if msg != self.previous_state:
                self._logger.debug("Recieved message to update progress: {}".format(msg))
            self.previous_state = msg
        elif 'M150' in msg:
            self.parse_m150(msg)
            self.previous_state = msg
        else:
            self.standard_effect(msg)
            if msg != self.previous_state:
                self._logger.debug("Recieved message to change effect: {}".format(msg))
            self.previous_state = msg

    def parse_m150(self, msg):
        red = green = blue = 0  # Start at 0, means sending 'M150' with no params turns LEDs off
        brightness = self.max_brightness  # No 'P' param? Use set brightness
        matches = re.finditer(M150_REGEX, msg)
        for match in matches:
            if match.group('red'):
                red = min(int(match.group('red')), 255)
            elif match.group('green'):
                green = min(int(match.group('green')), 255)
            elif match.group('blue'):
                blue = min(int(match.group('blue')), 255)
            elif match.group('white'):
                red = green = blue = min(int(match.group('white')), 255)
            elif match.group('brightness'):
                brightness = min(int(match.group('brightness')), 255)

        if self.check_times() and self.lights_on:  # Respect lights on/off
            EFFECTS['solid'](self.strip, self.queue, (red, green, blue), max_brightness=brightness)
        else:
            self.blank_leds()

    def startup_effect(self):
        if self.previous_state != 'startup':
            self._logger.debug("Hello! Running startup effect")
        self.standard_effect('startup')
        self.previous_state = 'startup'

    def progress_effect(self, mode, value):
        if self.check_times() and self.lights_on:
            effect_settings = self.settings[mode]
            EFFECTS[mode](self.strip, self.queue, int(value), hex_to_rgb(effect_settings['color']),
                          hex_to_rgb(effect_settings['base']), self.max_brightness)
        else:
            self.blank_leds()

    def standard_effect(self, mode):
        if self.check_times() and self.lights_on:
            effect_settings = self.settings[mode]
            EFFECTS[effect_settings['effect']](self.strip, self.queue, hex_to_rgb(effect_settings['color']),
                                               effect_settings['delay'], self.max_brightness)
        else:
            self.blank_leds()

    def blank_leds(self):
        """Set LEDs to off, wait 0.1secs to prevent CPU burn"""
        EFFECTS['solid'](self.strip, self.queue, [0, 0, 0], max_brightness=self.max_brightness, wait=False)
        if self.queue.empty():
            time.sleep(0.1)

    def check_times(self):
        """Check if current time is within 'active times' configuration, log if change detected"""
        if not self.start_time or not self.end_time:  # Active times are disabled, LEDs always on
            return True
        current_time = time.ctime(time.time()).split()[3].split(":")
        ct_mins = (int(current_time[0]) * 60) + int(current_time[1])

        if self.start_time <= ct_mins < self.end_time:
            if not self.lights_on:
                self._logger.debug("Active time start reached, but toggle switch is off")
            if not self.active_times_state:
                self._logger.debug("Active time start reached")
                self.active_times_state = True
            return True
        else:
            if self.active_times_state:
                self._logger.debug("Active times end reached")
                self.active_times_state = False
            return False

    def start_strip(self):
        """
        Start PixelStrip object
        :returns rpi_ws281x.PixelStrip
        """
        self._logger.info("Initialising LED strip")
        strip_settings = self.settings['strip']
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
            self._logger.info("Strip object successfully initialised")
            return strip
        except Exception as e:  # Probably wrong settings...
            self._logger.error("Strip failed to initialize, no effects will be run.")
            self._logger.error("Please check your settings.")
            self._logger.error("Here's the exception: {}".format(e))
            return None
