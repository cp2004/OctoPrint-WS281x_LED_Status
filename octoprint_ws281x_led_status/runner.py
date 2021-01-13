# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import re
import time

# noinspection PyPackageRequirements
from octoprint.logging.handlers import CleaningTimedRotatingFileHandler
from rpi_ws281x import PixelStrip

from octoprint_ws281x_led_status import constants
from octoprint_ws281x_led_status.util import hex_to_rgb


class EffectRunner:
    def __init__(
        self,
        debug,
        queue,
        strip_settings,
        effect_settings,
        active_times_settings,
        previous_state,
        log_path,
    ):

        self._logger = logging.getLogger("octoprint.plugins.ws281x_led_status.runner")
        self.setup_custom_logger(log_path, debug)

        self.strip_settings = strip_settings
        self.effect_settings = effect_settings
        self.active_times_settings = active_times_settings
        self.reverse = strip_settings["reverse"]
        self.max_brightness = strip_settings["led_brightness"]
        start = self.active_times_settings["start"].split(":")
        end = self.active_times_settings["stop"].split(":")
        self.start_time = (int(start[0]) * 60) + int(start[1])
        self.end_time = (int(end[0]) * 60) + int(end[1])

        self.lights_on = True
        self.previous_state = previous_state
        self.active_times_state = True

        self.queue = queue
        try:
            self.strip = self.start_strip()
        except StripFailedError:
            self._logger.info("No strip initialised, exiting the effect process.")
            return

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
                    parsed = self.parse_q_msg(msg)  # Effects are run from parse_q_msg
                    if parsed == constants.KILL_MSG:
                        self.blank_leds()
                        self._logger.info("Kill message recieved, Bye!")
                        # Exit the process
                        return
                    msg = parsed  # So that previous state can return after 'lights on'
        except KeyboardInterrupt:
            self.blank_leds()
            return
        except Exception as e:
            self._logger.error("Unhandled exception in effect runner process")
            self._logger.error(e)

    def parse_q_msg(self, msg):
        if msg == "on":
            self.turn_lights_off()
            return self.previous_state
        elif msg == "off":
            self.turn_lights_on()
            return self.previous_state
        elif "progress" in msg:
            self.progress_msg(msg)
        elif "M150" in msg:
            self.parse_m150(msg)
        else:
            self.standard_effect(msg)

        self.previous_state = msg

    def turn_lights_on(self):
        self.lights_on = True
        self._logger.info("On message received, turning on LEDs")

    def turn_lights_off(self):
        self.lights_on = False
        self._logger.info("Off message received, turning off LEDs")

    def progress_msg(self, msg):
        msg_split = msg.split()
        self.progress_effect(msg_split[0], float(msg_split[1]))
        if msg != self.previous_state:
            self._logger.debug("Received message to update progress: {}".format(msg))

    def parse_m150(self, msg):
        red = green = blue = 0  # Start at 0 - sending blank M150 turns LEDs off
        brightness = self.max_brightness  # No 'P' param? Use set brightness

        msg = msg.upper()

        matches = re.finditer(constants.M150_REGEX, msg)
        for match in matches:
            if match.group("red"):
                red = min(int(match.group("red")), 255)
            elif match.group("green"):
                green = min(int(match.group("green")), 255)
            elif match.group("blue"):
                blue = min(int(match.group("blue")), 255)
            elif match.group("white"):
                # See issue #33 for details of why this was changed. R/G/B params take priority over white, rather than
                # the other way (w max priority). For compatibility with https://github.com/horfee/OctoPrint-M150control
                if not ("R" in msg or "G" in msg or "U" in msg or "B" in msg):
                    red = green = blue = min(int(match.group("white")), 255)

            elif match.group("brightness"):
                brightness = min(int(match.group("brightness")), 255)

        if self.check_times() and self.lights_on:  # Respect lights on/off
            constants.EFFECTS["solid"](
                self.strip, self.queue, (red, green, blue), max_brightness=brightness
            )
        else:
            self.blank_leds()

    def progress_effect(self, mode, value):
        if self.check_times() and self.lights_on:
            effect_settings = self.effect_settings[mode]
            constants.EFFECTS[mode](
                self.strip,
                self.queue,
                int(value),
                hex_to_rgb(effect_settings["color"]),
                hex_to_rgb(effect_settings["base"]),
                self.max_brightness,
                self.reverse,
            )
        else:
            self.blank_leds()

    def standard_effect(self, mode):
        self._logger.debug("Changing effect to {}".format(mode))
        if self.check_times() and self.lights_on:
            effect_settings = self.effect_settings[mode]
            constants.EFFECTS[effect_settings["effect"]](
                self.strip,
                self.queue,
                hex_to_rgb(effect_settings["color"]),
                effect_settings["delay"],
                self.max_brightness,
            )
        else:
            self.blank_leds()

    def blank_leds(self):
        """Set LEDs to off, wait 0.1secs to prevent CPU burn"""
        constants.EFFECTS["solid"](
            self.strip,
            self.queue,
            [0, 0, 0],
            max_brightness=self.max_brightness,
            wait=False,
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
                num=self.strip_settings["led_count"],
                pin=self.strip_settings["led_pin"],
                freq_hz=self.strip_settings["led_freq_hz"],
                dma=self.strip_settings["led_dma"],
                invert=self.strip_settings["led_invert"],
                brightness=self.strip_settings["led_brightness"],
                channel=self.strip_settings["led_channel"],
                strip_type=constants.STRIP_TYPES[self.strip_settings["strip_type"]],
            )
            strip.begin()
            self._logger.info("Strip successfully initialised")
            return strip
        except Exception as e:  # Probably wrong settings...
            self._logger.error(e)
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
        for key, value in self.strip_settings.items():
            if key in constants.MODES:
                line = line + "\n | " + str(key)
                for setting_key, setting_value in value.items():
                    line = (
                        line + "\n | - " + str(setting_key) + ": " + str(setting_value)
                    )

        # extras
        line = line + "\n | * ACTIVE TIMES *"
        line = line + "\n | - start: " + str(self.active_times_settings["start"])
        line = line + "\n | - end: " + str(self.active_times_settings["active_stop"])
        self._logger.debug(line)


class StripFailedError(Exception):
    pass
