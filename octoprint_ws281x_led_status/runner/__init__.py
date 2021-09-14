# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

__author__ = "Charlie Powell <cp2004.github@gmail.com"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Charlie Powell 2020-2021 - released under the terms of the AGPLv3 License"

import logging
import math
import multiprocessing
import threading
import time

try:
    # Py3
    from queue import Queue
    from typing import Optional
except ImportError:
    # Py2
    from Queue import Queue

# noinspection PyPackageRequirements
from octoprint.logging.handlers import CleaningTimedRotatingFileHandler
from rpi_ws281x import PixelStrip

from octoprint_ws281x_led_status import constants
from octoprint_ws281x_led_status.effects import error_handled_effect
from octoprint_ws281x_led_status.runner import segments
from octoprint_ws281x_led_status.runner import timer as active_times
from octoprint_ws281x_led_status.util import (
    apply_color_correction,
    clear_queue,
    hex_to_rgb,
    int_0_255,
    milli_sleep,
    recursively_log,
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
        features_settings,
        previous_state,
        log_path,
        saved_lights_on,
    ):

        self._logger = logging.getLogger("octoprint.plugins.ws281x_led_status.runner")
        self.setup_custom_logger(log_path, debug)
        self._logger.debug("Starting WS281x LED Status Effect runner")

        self.segment_manager = None  # type Optional[segments.SegmentManager]

        # Save settings to class
        self.strip_settings = strip_settings
        self.effect_settings = effect_settings
        self.features_settings = features_settings
        self.active_times_settings = features_settings["active_times"]
        self.transition_settings = features_settings["transitions"]
        self.max_brightness = int(
            round((float(strip_settings["brightness"]) / 100) * 255)
        )
        self.color_correction = {
            "red": self.strip_settings["adjustment"]["R"],
            "green": self.strip_settings["adjustment"]["G"],
            "blue": self.strip_settings["adjustment"]["B"],
            "white_override": self.strip_settings["white_override"],
            "white_brightness": self.strip_settings["white_brightness"],
        }

        # Create segment settings
        # Segments are EXPERIMENTAL and only enabled for certain conditions
        self.segment_settings = []

        # Sacrificial pixel offsets by one
        default_segment = {"start": 0, "end": int(self.strip_settings["count"])}
        if self.features_settings["sacrifice_pixel"]:
            default_segment["start"] = 1

        self.segment_settings.append(default_segment)

        if int(self.strip_settings["count"]) < 6:
            self._logger.info("Applying < 6 LED flickering bug workaround")
            # rpi_ws281x will think we want 6 LEDs, but we will only use those configured
            # this works around issues where LEDs would show the wrong colour, flicker and more
            # when used with less than 6 LEDs.
            # See #132 for details
            self.strip_settings["count"] = 6

        # State holders
        self.lights_on = saved_lights_on
        self.previous_state = previous_state
        self.previous_m150 = {}  # type: dict
        self.active_times_state = True
        self.turn_off_timer = None

        self.queue = queue  # type: multiprocessing.Queue
        try:
            self.strip = self.start_strip()  # type: PixelStrip
        except (StripFailedError, segments.InvalidSegmentError):
            self._logger.error("Exiting the effect process")
            return
        except Exception as e:
            self._logger.exception(e)
            self._logger.error("Exiting the effect process")
            return

        self.effect_queue = Queue()
        self.effect_thread = None  # type: Optional[threading.Thread]

        self.brightness_manager = BrightnessManager(
            self.strip, self.max_brightness, self.transition_settings
        )

        # Create 'Active Times' background timers
        self.active_times_timer = active_times.ActiveTimer(
            self.active_times_settings, self.switch_lights
        )
        self.active_times_timer.start_timer()

        if debug:
            self.log_settings()
        else:
            self._logger.info(
                "Debug logging not enabled, if you are reporting issues please enable it "
                "under 'Features' in the settings page."
            )

        # Set back previous state, unless it is `blank`, then start main loop
        if not (
            self.previous_state["type"] == "standard"
            and self.previous_state["effect"] == "blank"
        ):
            self._logger.debug(
                "Returning to previous state: {}".format(self.previous_state)
            )
            self.parse_q_msg(self.previous_state)

        self._logger.info("Startup Complete!")
        self.main_loop()

    def main_loop(self):
        try:
            while True:
                msg = self.queue.get()
                self._logger.debug("New message: {}".format(msg))
                if msg:
                    if msg == constants.KILL_MSG:
                        self.kill()
                        # Exit the process
                        return
                    self.parse_q_msg(msg)  # Effects are run from parse_q_msg

        except KeyboardInterrupt:
            self.kill()
            return
        except Exception as e:
            self._logger.error("Unhandled exception in effect runner process")
            self._logger.exception(e)
            raise

    def kill(self):
        self._logger.debug("Kill message received, shutting down...")
        self.blank_leds()
        self.stop_effect()
        self.active_times_timer.end_timer()
        self._logger.info("Effect runner shutdown. Bye!")

    def parse_q_msg(self, msg):
        if msg["type"] == "lights":
            if msg["action"] == "on":
                self.switch_lights(True)
            if msg["action"] == "off":
                self.switch_lights(False)

        elif msg["type"] == "progress":
            self.progress_msg(msg["effect"], msg["value"])
            self.previous_state = msg

        elif msg["type"] == "M150":
            self.parse_m150(msg["command"])

        elif msg["type"] == "standard":
            self.standard_effect(msg["effect"])
            self.previous_state = msg

    def switch_lights(self, state):
        # state: target state for lights
        # Only run when current state must change, since it will interrupt the currently running effect
        if state == self.lights_on:
            return

        self._logger.info("Switching lights {}".format("on" if state else "off"))

        if state:
            self.turn_lights_on()
        else:
            self.turn_lights_off()

    def turn_lights_on(self):
        if not self.active_times_timer.active:
            # Active times are not now, don't do anything
            self._logger.debug("LED switch on blocked by active times")
            self.parse_q_msg(self.previous_state)
            return

        if self.turn_off_timer and self.turn_off_timer.is_alive():
            self.turn_off_timer.cancel()

        self.lights_on = True

        if self.transition_settings["fade"]["enabled"]:
            start_daemon_thread(
                target=self.brightness_manager.do_fade_in, name="Fade in"
            )
        self.parse_q_msg(self.previous_state)

    def turn_lights_off(self):
        if self.transition_settings["fade"]["enabled"]:
            # Start fading brightness out
            start_daemon_thread(
                target=self.brightness_manager.do_fade_out, name="Fade out thread"
            )
            # Set timer to turn LEDs off after fade
            self.turn_off_timer = start_daemon_timer(
                interval=float(self.transition_settings["fade"]["time"]) / 1000,
                target=self.lights_off,
            )
        else:
            self.lights_off()

    def lights_off(self):
        self.standard_effect("blank")
        self.lights_on = False

    def progress_msg(self, progress_effect, value):
        self._logger.debug("Changing effect to {}, {}%".format(progress_effect, value))
        self.progress_effect(progress_effect, min(max(int(value), 0), 100))

    def parse_m150(self, msg):
        red = green = blue = white = 0  # Start at 0 - sending blank M150 turns LEDs off
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
                    red = green = blue = white = int_0_255(w.group("value"))
            # Save parsed to class
            self.previous_m150 = {
                "r": red,
                "b": blue,
                "g": green,
                "w": white,
                "brightness": brightness,
            }
            self.previous_state = {
                "type": "M150",
                "command": "M150",  # Chop the parameters, so it is not parsed again
            }
            self._logger.debug(
                "Parsed new M150: M150 R{red} G{green} B{blue} (brightness: {brightness})".format(
                    **locals()
                )
            )

        if self.lights_on:  # Respect lights on/off
            # Set brightness
            self.brightness_manager.set_brightness(self.previous_m150["brightness"])

            # Work out the colour - if specified W, use that if available. Falls back on auto-detection
            if self.color_correction["white_override"] and self.previous_m150["w"]:
                color = (0, 0, 0, int(self.previous_m150["w"]))
            else:
                color = apply_color_correction(
                    self.color_correction,
                    self.previous_m150["r"],
                    self.previous_m150["g"],
                    self.previous_m150["b"],
                )

            # Set the effects
            self.run_effect(
                target=constants.EFFECTS["Solid Color"],
                kwargs={
                    "queue": self.effect_queue,
                    "color": color,
                    "brightness_manager": self.brightness_manager,
                },
                name="Solid Color",
            )
        else:
            self.blank_leds(whole_strip=False)

    def progress_effect(self, mode, value):
        effect_settings = self.effect_settings[mode]
        if self.lights_on:
            self.run_effect(
                target=constants.PROGRESS_EFFECTS[effect_settings["effect"]],
                kwargs={
                    "queue": self.effect_queue,
                    "brightness_manager": self.brightness_manager,
                    "value": int(value),
                    "progress_color": apply_color_correction(
                        self.color_correction, *hex_to_rgb(effect_settings["color"])
                    ),
                    "base_color": apply_color_correction(
                        self.color_correction, *hex_to_rgb(effect_settings["base"])
                    ),
                    "reverse": self.strip_settings["reverse"],
                },
                name=mode,
            )
        else:
            self.blank_leds(whole_strip=False)

    def standard_effect(self, mode):
        # Log if the effect is changing
        self._logger.debug("Changing effect to {}".format(mode))

        if self.lights_on and not mode == "blank":
            effect_settings = self.effect_settings[mode]
            self.run_effect(
                target=constants.EFFECTS[effect_settings["effect"]],
                kwargs={
                    "queue": self.effect_queue,
                    "color": apply_color_correction(
                        self.color_correction, *hex_to_rgb(effect_settings["color"])
                    ),
                    "delay": effect_settings["delay"],
                    "brightness_manager": self.brightness_manager,
                },
                name=mode,
            )
        else:
            self.blank_leds(whole_strip=False)

    def run_effect(self, target, kwargs=None, name="WS281x Effect"):
        if kwargs is None:
            kwargs = {}

        if "strip" not in kwargs:
            kwargs["strip"] = self.segment_manager.get_segment(1)

        self.stop_effect()

        # Targets error handler, which passes off to the effect with effect_args
        self.effect_thread = start_daemon_thread(
            target=error_handled_effect,
            kwargs={"target": target, "logger": self._logger, "effect_args": kwargs},
            name=name,
        )

    def stop_effect(self):
        if self.effect_thread and self.effect_thread.is_alive():
            self.effect_queue.put(constants.KILL_MSG)
            self.effect_thread.join()
            clear_queue(self.effect_queue)

    def blank_leds(self, whole_strip=True):
        """Set LEDs to off, wait 0.1secs to prevent CPU burn"""
        strip = self.strip
        if not whole_strip:
            # Use a segment, not whole strip
            strip = self.segment_manager.get_segment(1)

        self._logger.debug("Blanking LEDs")

        self.run_effect(
            target=constants.EFFECTS["Solid Color"],
            kwargs={
                "strip": strip,
                "queue": self.effect_queue,
                "color": (0, 0, 0),
                "brightness_manager": self.brightness_manager,
                "wait": False,
            },
            name="Solid Color",
        )
        if self.queue.empty():
            time.sleep(0.1)

    def start_strip(self):
        """
        Start PixelStrip and SegmentManager object
        :returns strip: (rpi_ws281x.PixelStrip) The initialised strip object
        """
        self._logger.info("Starting up LED strip")
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
            self._logger.info("Strip startup complete!")
        except Exception as e:  # Probably wrong settings...
            self._logger.error(repr(e))
            self._logger.error("Strip failed to startup")
            raise StripFailedError("Error initializing strip")

        # Create segments & segment manager
        try:
            self.segment_manager = segments.SegmentManager(strip, self.segment_settings)
            self.segment_manager.create_segments()
        except segments.InvalidSegmentError:
            self._logger.error("Segment configuration error. Please report this issue!")
            raise
        return strip

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
        lines = ["Current settings:"]

        lines.extend(
            recursively_log(
                {
                    "STRIP SETTINGS": self.strip_settings,
                    "EFFECT SETTINGS": self.effect_settings,
                    "FEATURES SETTINGS": self.features_settings,
                }
            )
        )

        self._logger.debug("\n".join(lines))


class BrightnessManager:
    def __init__(self, strip, max_brightness, transition_settings):
        self.strip = strip
        self.max_brightness = max_brightness
        self.transition_settings = transition_settings
        self.current_brightness = 0

        # Perform potentially heavy calculation on startup
        self.fade_steps = self.calculate_fade_in()

        # State flags
        self.fade_active = False

    def get_brightness(self):
        """
        Get current brightness from manager
        """
        return self.current_brightness

    def set_brightness(self, value, show=True):
        if not isinstance(value, int):
            value = int(value)

        # If fade active, don't change brightness - would be overwritten quickly
        if not self.fade_active:
            self.current_brightness = value
            self.strip.setBrightness(self.current_brightness)
            if show:
                self.strip.show()

    def reset_brightness(self):
        if not self.fade_active:
            self.strip.setBrightness(self.max_brightness)

    def calculate_fade_in(self):
        """
        Calculate a list of brightness values per ms, based on sine curve
        """
        fade_time = int(self.transition_settings["fade"]["time"])  # Fade time in ms
        step = (math.pi / 2) / (fade_time / 20)
        # Difference between steps, in radians (per 20ms)

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


class StripFailedError(Exception):
    pass
