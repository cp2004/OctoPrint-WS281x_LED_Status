__author__ = "Charlie Powell <cp2004.github@gmail.com"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Charlie Powell 2020-2021 - released under the terms of the AGPLv3 License"

import logging
import math
import time
from queue import Queue

# noinspection PyPackageRequirements
from octoprint.logging.handlers import CleaningTimedRotatingFileHandler

from octoprint_ws281x_led_status import constants
from octoprint_ws281x_led_status.backend import LEDBackend
from octoprint_ws281x_led_status.backend.factory import create_backend
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
        backend_settings,
        effect_settings,
        features_settings,
        previous_state,
        log_path,
        saved_lights_on,
    ):

        self._logger = logging.getLogger("octoprint.plugins.ws281x_led_status.runner")
        self.setup_custom_logger(log_path, debug)
        self._logger.debug("Starting WS281x LED Status Effect runner")

        try:
            # This entire thing is wrapped in a try: except block because otherwise errors here would
            # cause the process to crash but nobody would know about it, it died silently.

            self.segment_manager = None  # type Optional[segments.SegmentManager]

            # Save settings to class
            self.strip_settings = strip_settings
            self.backend_settings = backend_settings
            self.effect_settings = effect_settings
            self.features_settings = features_settings
            self.active_times_settings = features_settings["active_times"]
            self.transition_settings = features_settings["transitions"]
            self.max_brightness = int(
                round((float(backend_settings["config"]["brightness"]) / 100) * 255)
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
            default_segment = {"start": 0, "end": int(self.backend_settings["config"]["count"])}
            if self.features_settings["sacrifice_pixel"]:
                default_segment["start"] = 1

            self.segment_settings.append(default_segment)

            if int(self.backend_settings["config"]["count"]) < 6:
                self._logger.info("Applying < 6 LED flickering bug workaround")
                # rpi_ws281x will think we want 6 LEDs, but we will only use those configured
                # this works around issues where LEDs would show the wrong colour, flicker and more
                # when used with less than 6 LEDs.
                # See #132 for details
                self.backend_settings["config"]["count"] = 6

            # State holders
            self.lights_on = saved_lights_on
            self.previous_state = previous_state
            self.previous_m150 = {}  # type: dict
            self.active_times_state = True
            self.turn_off_timer = None

            self.queue = queue  # type: multiprocessing.Queue
            try:
                self.strip = self.start_strip()  # type: LEDBackend
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
        except Exception as e:
            self._logger.error("Unhandled error starting the effect runner")
            self._logger.exception(e)
            return

        self.main_loop()

    def main_loop(self):
        try:
            # Set back previous state, unless it is `blank`, then start main loop
            if not (
                self.previous_state["type"] == "standard"
                and self.previous_state["effect"] == "blank"
            ):
                self._logger.debug(
                    f"Returning to previous state: {self.previous_state}"
                )
                self.parse_q_msg(self.previous_state)

            self._logger.info("Starting main loop")
            while True:
                msg = self.queue.get()
                self._logger.debug(f"New message: {msg}")
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
        self._logger.debug(f"[TRIGGER] Message received - Type: {msg['type']}, Details: {msg}")

        if msg["type"] == "lights":
            self._logger.info(f"[TRIGGER] Light control: {msg['action']}")
            if msg["action"] == "on":
                self.switch_lights(True)
            if msg["action"] == "off":
                self.switch_lights(False)

        elif msg["type"] == "progress":
            self._logger.info(f"[TRIGGER] Progress effect: {msg['effect']} at {msg['value']}%")
            self.progress_msg(msg["effect"], msg["value"])
            self.previous_state = msg

        elif msg["type"] == "M150":
            self._logger.info(f"[TRIGGER] M150 command: {msg['command']}")
            self.parse_m150(msg["command"])

        elif msg["type"] == "standard":
            self._logger.info(f"[TRIGGER] Standard effect: {msg['effect']}")
            self.standard_effect(msg["effect"])
            self.previous_state = msg

        elif msg["type"] == "custom":
            self._logger.info(f"[TRIGGER] Custom effect: {msg['effect']}, color: {msg['color']}, delay: {msg['delay']}")
            self.custom_effect(msg["effect"], msg["color"], msg["delay"])

    def switch_lights(self, state):
        # state: target state for lights
        # Only run when current state must change, since it will interrupt the currently running effect
        if state == self.lights_on:
            self._logger.debug(f"[STATE] Light switch requested but already in target state: {state}")
            return

        self._logger.info(f"[STATE] Switching lights {'on' if state else 'off'} (was: {'on' if self.lights_on else 'off'})")

        if state:
            self.turn_lights_on()
        else:
            self.turn_lights_off()

    def turn_lights_on(self):
        if not self.active_times_timer.active:
            # Active times are not now, don't do anything
            self._logger.info("[STATE] LED switch on blocked by active times, restoring previous state")
            self.parse_q_msg(self.previous_state)
            return

        if self.turn_off_timer and self.turn_off_timer.is_alive():
            self._logger.debug("[STATE] Cancelling turn-off timer")
            self.turn_off_timer.cancel()

        self.lights_on = True
        self._logger.info(f"[STATE] Lights ON, fade={'enabled' if self.transition_settings['fade']['enabled'] else 'disabled'}")

        if self.transition_settings["fade"]["enabled"]:
            start_daemon_thread(
                target=self.brightness_manager.do_fade_in, name="Fade in"
            )
        self.parse_q_msg(self.previous_state)

    def turn_lights_off(self):
        fade_enabled = self.transition_settings["fade"]["enabled"]
        self._logger.info(f"[STATE] Turning lights OFF, fade={'enabled' if fade_enabled else 'disabled'}")

        if fade_enabled:
            fade_time = float(self.transition_settings["fade"]["time"]) / 1000
            self._logger.debug(f"[STATE] Starting fade out over {fade_time}s")
            # Start fading brightness out
            start_daemon_thread(
                target=self.brightness_manager.do_fade_out, name="Fade out thread"
            )
            # Set timer to turn LEDs off after fade
            self.turn_off_timer = start_daemon_timer(
                interval=fade_time,
                target=self.lights_off,
            )
        else:
            self.lights_off()

    def lights_off(self):
        self._logger.info("[STATE] Lights OFF - blanking LEDs")
        self.standard_effect("blank")
        self.lights_on = False

    def progress_msg(self, progress_effect, value):
        # Detailed logging happens in progress_effect method
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
                f"Parsed new M150: M150 R{red} G{green} B{blue} (brightness: {brightness})"
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
        progress_color = apply_color_correction(
            self.color_correction, *hex_to_rgb(effect_settings["color"])
        )
        base_color = apply_color_correction(
            self.color_correction, *hex_to_rgb(effect_settings["base"])
        )

        if self.lights_on:
            self._logger.info(
                f"[EFFECT] Progress {mode}: value={value}%, effect={effect_settings['effect']}, "
                f"progress_color=RGB{progress_color}, base_color=RGB{base_color}, lights_on=True"
            )
            self.run_effect(
                target=constants.PROGRESS_EFFECTS[effect_settings["effect"]],
                kwargs={
                    "queue": self.effect_queue,
                    "brightness_manager": self.brightness_manager,
                    "value": int(value),
                    "progress_color": progress_color,
                    "base_color": base_color,
                },
                name=mode,
            )
        else:
            self._logger.info(
                f"[EFFECT] Progress {mode} blocked: lights_on=False, blanking LEDs instead"
            )
            self.blank_leds(whole_strip=False)

    def standard_effect(self, mode):
        # Handle "blank" as a special case - it's not in effect_settings
        if mode == "blank":
            self._logger.info(
                f"[EFFECT] Blank mode: blanking LEDs, lights_on={self.lights_on}"
            )
            self.blank_leds(whole_strip=False)
            return

        effect_settings = self.effect_settings[mode]
        torch_override = mode == "torch" and effect_settings.get("override_timer", False)
        will_run = self.lights_on or torch_override

        if will_run:
            color = apply_color_correction(
                self.color_correction, *hex_to_rgb(effect_settings["color"])
            )
            self._logger.info(
                f"[EFFECT] Standard {mode}: effect={effect_settings['effect']}, "
                f"color=RGB{color}, delay={effect_settings['delay']}ms, "
                f"lights_on={self.lights_on}, torch_override={torch_override}"
            )
            self.run_effect(
                target=constants.EFFECTS[effect_settings["effect"]],
                kwargs={
                    "queue": self.effect_queue,
                    "color": color,
                    "delay": effect_settings["delay"],
                    "brightness_manager": self.brightness_manager,
                },
                name=mode,
            )
        else:
            self._logger.info(
                f"[EFFECT] Standard {mode} blocked: lights_on=False, blanking LEDs instead"
            )
            self.blank_leds(whole_strip=False)

    def custom_effect(self, effect, color, delay):
        if self.lights_on:
            corrected_color = apply_color_correction(
                self.color_correction, *hex_to_rgb(color)
            )
            self._logger.info(
                f"[EFFECT] Custom {effect}: color=RGB{corrected_color}, "
                f"delay={delay}ms, lights_on=True"
            )
            self.run_effect(
                target=constants.EFFECTS[effect],
                kwargs={
                    "queue": self.effect_queue,
                    "color": corrected_color,
                    "delay": delay,
                    "brightness_manager": self.brightness_manager,
                },
                name=effect,
            )
        else:
            self._logger.info(
                f"[EFFECT] Custom {effect} blocked: lights_on=False, blanking LEDs instead"
            )
            self.blank_leds(whole_strip=False)

    def run_effect(self, target, kwargs=None, name="WS281x Effect"):
        if kwargs is None:
            kwargs = {}

        if "strip" not in kwargs:
            kwargs["strip"] = self.segment_manager.get_segment(1)

        self.stop_effect()

        self._logger.debug(f"[EFFECT] Starting effect thread: {name}")
        # Targets error handler, which passes off to the effect with effect_args
        self.effect_thread = start_daemon_thread(
            target=error_handled_effect,
            kwargs={"target": target, "logger": self._logger, "effect_args": kwargs},
            name=name,
        )

    def stop_effect(self):
        if self.effect_thread and self.effect_thread.is_alive():
            self._logger.debug(f"[EFFECT] Stopping current effect thread: {self.effect_thread.name}")
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
        Start LED backend and SegmentManager object

        :returns strip: (LEDBackend) The initialised backend object
        """
        # Get backend type from settings
        backend_name = self.backend_settings.get("type", "rpi_ws281x")
        backend_config = self.backend_settings.get("config", {})

        self._logger.info(f"Starting LED strip with backend: '{backend_name}'")
        self._logger.debug(
            f"Backend config: count={backend_config.get('count')}, "
            f"brightness={backend_config.get('brightness', 100)}%"
        )

        try:
            # Create backend using factory
            strip = create_backend(backend_name, backend_config)
            strip.begin()

            self._logger.info(
                f"Successfully initialized '{backend_name}' backend "
                f"with {strip.num_pixels()} LEDs at {strip.get_brightness()} brightness"
            )
        except Exception as e:  # Probably wrong settings or backend unavailable
            self._logger.error(f"Failed to initialize LED backend '{backend_name}': {repr(e)}")
            self._logger.error(
                f"Common causes: wrong GPIO pin, missing dependencies, "
                f"SPI not enabled, or insufficient permissions"
            )
            raise StripFailedError("Error initializing strip") from e

        # Create segments & segment manager
        try:
            self.segment_manager = segments.SegmentManager(strip, self.segment_settings)
            self.segment_manager.create_segments()
            self._logger.debug(f"Created {len(self.segment_settings)} segment(s)")
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
