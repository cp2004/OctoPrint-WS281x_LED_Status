# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

__author__ = "Charlie Powell <cp2004.github@gmail.com"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Charlie Powell 2020-2021 - released under the terms of the AGPLv3 License"

import logging
import math
import time

# noinspection PyPackageRequirements
from octoprint.logging.handlers import CleaningTimedRotatingFileHandler
from rpi_ws281x import PixelStrip

from octoprint_ws281x_led_status import constants
from octoprint_ws281x_led_status.util import (
    apply_color_correction,
    hex_to_rgb,
    int_0_255,
    milli_sleep,
    start_daemon_thread,
    start_daemon_timer,
)


class EffectRunner:
    def __init__(
        self,
        debug,
        queue,
        strip_settings,
        effect_settings,
        active_times_settings,
        transition_settings,
        previous_state,
        log_path,
    ):

        self._logger = logging.getLogger("octoprint.plugins.ws281x_led_status.runner")
        self.setup_custom_logger(log_path, debug)

        # Save settings to class
        self.strip_settings = strip_settings
        self.effect_settings = effect_settings
        self.active_times_settings = active_times_settings
        self.transition_settings = transition_settings
        self.reverse = strip_settings["reverse"]
        self.max_brightness = int(
            round((float(strip_settings["brightness"]) / 100) * 255)
        )
        start = self.active_times_settings["start"].split(":")
        end = self.active_times_settings["end"].split(":")
        self.start_time = (int(start[0]) * 60) + int(start[1])
        self.end_time = (int(end[0]) * 60) + int(end[1])
        self.color_correction = {
            "red": self.strip_settings["adjustment"]["R"],
            "green": self.strip_settings["adjustment"]["G"],
            "blue": self.strip_settings["adjustment"]["B"],
        }

        # State holders
        self.lights_on = True
        self.previous_state = previous_state
        self.previous_m150 = {}  # type: dict
        self.active_times_state = True
        self.turn_off_timer = None

        self.queue = queue
        try:
            self.strip = self.start_strip()
        except StripFailedError:
            self._logger.info("No strip initialised, exiting the effect process.")
            return

        self.brightness_manager = BrightnessManager(
            self.strip, self.max_brightness, self.transition_settings
        )

        if debug:
            self.log_settings()
        else:
            self._logger.info(
                "Debug logging not enabled, if you are reporting issues please enable it "
                "under 'Features' in the settings page."
            )

        self.main_loop()

    def main_loop(self):
        msg = self.previous_state
        try:
            while True:
                if not self.queue.empty():
                    msg = self.queue.get()  # The ONLY place the queue should be 'got'
                if msg:
                    if msg == constants.KILL_MSG:
                        self.blank_leds()
                        self._logger.info("Kill message recieved, Bye!")
                        # Exit the process
                        return
                    self.parse_q_msg(msg)  # Effects are run from parse_q_msg
                    msg = self.previous_state
        except KeyboardInterrupt:
            self.blank_leds()
            return
        except Exception as e:
            self._logger.error("Unhandled exception in effect runner process")
            self._logger.error(repr(e))
            raise

    def parse_q_msg(self, msg):
        if msg == "on":
            self.turn_lights_on()
            return
        elif msg == "off":
            self.turn_lights_off()
            return
        elif "progress" in msg:
            self.progress_msg(msg)
        elif "M150" in msg:
            self.parse_m150(msg)
            return
        else:
            self.standard_effect(msg)

        self.previous_state = msg

    def turn_lights_on(self):
        if self.turn_off_timer and self.turn_off_timer.is_alive():
            self.turn_off_timer.cancel()

        self.lights_on = True
        if self.transition_settings["fade"]["enabled"]:
            start_daemon_thread(
                target=self.brightness_manager.do_fade_in, name="Fade in thread"
            )
        self._logger.info("On message received, turning on LEDs")

    def turn_lights_off(self):
        if self.transition_settings["fade"]["enabled"]:
            # Start fading brightness out
            start_daemon_thread(
                target=self.brightness_manager.do_fade_out, name="Fade out thread"
            )
            # Set timer to turn LEDs off after fade
            self.turn_off_timer = start_daemon_timer(
                interval=self.transition_settings["fade"]["time"] / 1000,
                target=self.lights_off,
            )
        else:
            self.lights_on = False
        self._logger.info("Off message received, turning off LEDs")

    def lights_off(self):
        self.lights_on = False

    def progress_msg(self, msg):
        msg_split = msg.split()
        self.progress_effect(msg_split[0], float(msg_split[1]))
        if msg != self.previous_state:
            self._logger.debug("Received message to update progress: {}".format(msg))

    def parse_m150(self, msg):
        red = green = blue = 0  # Start at 0 - sending blank M150 turns LEDs off
        brightness = self.max_brightness  # No 'P' param? Use set brightness

        msg = msg.upper()

        if msg != "M150":
            # Found a NEW M150, parse it and remove params
            r = constants.regex_r_param.search(msg)
            if r:
                red = int_0_255(r.group("value"))
            g = constants.regex_g_param.search(msg)
            if g:
                green = int_0_255(g.group("value"))
            b = constants.regex_b_param.search(msg)
            if b:
                blue = int_0_255(b.group("value"))
            p = constants.regex_p_param.search(msg)
            if p:
                brightness = int_0_255(p.group("value"))
            if not r and not g and not b:
                # R/G/B params take priority over white, see #33 for details
                w = constants.regex_w_param.search(msg)
                if w:
                    red = green = blue = int_0_255(w.group("value"))
            # Save parsed to class
            self.previous_m150 = {
                "r": red,
                "b": blue,
                "g": green,
                "brightness": brightness,
            }
            self.previous_state = "M150"

        if self.check_times() and self.lights_on:  # Respect lights on/off
            constants.EFFECTS["Solid Color"](
                self.strip,
                self.queue,
                apply_color_correction(
                    self.color_correction,
                    self.previous_m150["r"],
                    self.previous_m150["g"],
                    self.previous_m150["b"],
                ),
                max_brightness=self.previous_m150["brightness"],
                brightness_manager=self.brightness_manager,
            )
        else:
            self.blank_leds()

    def progress_effect(self, mode, value):
        if self.check_times() and self.lights_on:
            effect_settings = self.effect_settings[mode]
            constants.PROGRESS_EFFECTS["progress"](  # TODO More progress effects
                self.strip,
                self.queue,
                int(value),
                apply_color_correction(
                    self.color_correction, *hex_to_rgb(effect_settings["color"])
                ),
                apply_color_correction(
                    self.color_correction, *hex_to_rgb(effect_settings["base"])
                ),
                self.max_brightness,
                self.reverse,
                brightness_manager=self.brightness_manager,
            )
        else:
            self.blank_leds()

    def standard_effect(self, mode):
        if self.previous_state != mode:
            self._logger.debug("Changing effect to {}".format(mode))
        if self.check_times() and self.lights_on:
            effect_settings = self.effect_settings[mode]
            constants.EFFECTS[effect_settings["effect"]](
                self.strip,
                self.queue,
                apply_color_correction(
                    self.color_correction, *hex_to_rgb(effect_settings["color"])
                ),
                effect_settings["delay"],
                self.max_brightness,
                brightness_manager=self.brightness_manager,
            )
        else:
            self.blank_leds()

    def blank_leds(self):
        """Set LEDs to off, wait 0.1secs to prevent CPU burn"""
        constants.EFFECTS["Solid Color"](
            self.strip,
            self.queue,
            [0, 0, 0],
            max_brightness=self.max_brightness,
            wait=False,
            brightness_manager=self.brightness_manager,
        )
        if self.queue.empty():
            time.sleep(0.1)

    def check_times(self):
        """Check if current time is within 'active times' configuration, log if change detected"""
        if not self.active_times_settings["enabled"]:
            # Active times are disabled, LEDs always on
            return True

        current_time = time.ctime(time.time()).split()[3].split(":")
        ct_mins = (int(current_time[0]) * 60) + int(current_time[1])

        if self.start_time <= ct_mins < self.end_time:
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
        :returns strip: (rpi_ws281x.PixelStrip) The initialised strip object
        """
        self._logger.info("Initialising LED strip")
        try:
            strip = PixelStrip(
                num=int(self.strip_settings["count"]),
                pin=int(self.strip_settings["pin"]),
                freq_hz=int(self.strip_settings["freq_hz"]),
                dma=int(self.strip_settings["dma"]),
                invert=bool(self.strip_settings["invert"]),
                brightness=int(self.strip_settings["brightness"]),
                channel=int(self.strip_settings["channel"]),
                strip_type=constants.STRIP_TYPES[self.strip_settings["type"]],
            )
            strip.begin()
            self._logger.info("Strip successfully initialised")
            return strip
        except Exception as e:  # Probably wrong settings...
            self._logger.error(repr(e))
            self._logger.error("Strip failed to initialize, no effects will be run.")
            raise StripFailedError("Error intitializing strip")

    def setup_custom_logger(self, path, debug):
        # Cleaning handler will remove old logs, defined by 'backupCount'
        # 'D' specifies to roll over each day
        effect_runner_handler = CleaningTimedRotatingFileHandler(
            path, when="D", backupCount=2
        )
        effect_runner_handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
        )
        effect_runner_handler.setLevel(logging.DEBUG)

        self._logger.addHandler(effect_runner_handler)
        self._logger.setLevel(logging.DEBUG if debug else logging.INFO)
        self._logger.propagate = False

    def log_settings(self):
        """
        This has to be here so I can find out what kind of settings people
        are running when they report issues. Only logged in debug mode.
        :return: None
        """
        line = "Current settings:"

        # Start with strip settings
        line = line + "\n | * STRIP SETTINGS *"
        for key, value in self.strip_settings.items():
            line = line + "\n | - " + str(key) + ": " + str(value)

        # effect settings
        line = line + "\n | * EFFECT SETTINGS *"
        for key, value in self.effect_settings.items():
            if key in constants.MODES:
                line = line + "\n | " + str(key)
                for setting_key, setting_value in value.items():
                    line = (
                        line + "\n | - " + str(setting_key) + ": " + str(setting_value)
                    )

        # extras
        line = line + "\n | * ACTIVE TIMES *"
        line = line + "\n | - enabled: " + str(self.active_times_settings["enabled"])
        line = line + "\n | - start: " + str(self.active_times_settings["start"])
        line = line + "\n | - end: " + str(self.active_times_settings["end"])
        self._logger.debug(line)


class BrightnessManager:
    def __init__(self, strip, max_brightness, transition_settings):
        self.strip = strip
        self.max_brightness = max_brightness
        self.transition_settings = transition_settings
        self.current_brightness = 0

        # Perform heavy calculation on startup
        self.fade_steps = self.calculate_fade_in()

        # State flags
        self.fade_active = False

    def get_brightness(self):
        """
        Get current brightness from manager
        """
        return self.current_brightness

    def calculate_fade_in(self):
        """
        Calculate a list of brightness values per ms, based on sine curve
        """
        fade_time = self.transition_settings["fade"]["time"]  # Fade time in ms
        step = (math.pi / 2) / (fade_time / 20)
        # Difference between steps, in radians (per 10ms)

        # Work out brightness value per ms, based on sine curve
        steps = []
        for i in range(0, int(fade_time / 20)):
            steps.append(math.sin(i * step) * self.max_brightness)

        return steps

    def do_fade_in(self):
        """
        Step through fade values to produce fade in effect
        """
        while self.fade_active:
            # Wait for any previous fade to finish
            milli_sleep(10)

        self.fade_active = True
        for step in self.fade_steps:
            self.current_brightness = int(round(step, 0))
            self.strip.setBrightness(self.current_brightness)
            self.strip.show()
            milli_sleep(20)

        self.fade_active = False

    def do_fade_out(self):
        """
        Step through fade values to produce fade out effect
        """
        while self.fade_active:
            # Wait for any previous fade to finish
            milli_sleep(10)

        self.fade_active = True
        for step in reversed(self.fade_steps):
            self.current_brightness = int(round(step, 0))
            self.strip.setBrightness(self.current_brightness)
            self.strip.show()
            milli_sleep(20)

        self.fade_active = False

    def reset_brightness(self):
        if not self.fade_active:
            self.strip.setBrightness(self.max_brightness)


class StripFailedError(Exception):
    pass
