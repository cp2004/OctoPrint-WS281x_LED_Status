# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

import io
import logging
import multiprocessing
import re
import time

# noinspection PyPackageRequirements
import octoprint.plugin

# noinspection PyPackageRequirements
from octoprint.events import Events

from octoprint_ws281x_led_status import api, constants, settings, util, wizard
from octoprint_ws281x_led_status.runner import EffectRunner

from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions


PI_MODEL = None


class WS281xLedStatusPlugin(
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.ShutdownPlugin,
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.SimpleApiPlugin,
    octoprint.plugin.WizardPlugin,
    octoprint.plugin.ProgressPlugin,
    octoprint.plugin.EventHandlerPlugin,
    octoprint.plugin.RestartNeedingPlugin,
):
    # Submodules
    api = None  # type: api.PluginApi
    wizard = None  # type: wizard.PluginWizard

    current_effect_process = None  # type: multiprocessing.Process
    current_state = "startup"  # type: str
    effect_queue = multiprocessing.Queue()  # type: multiprocessing.Queue

    # Heating detection flags. True/False, when True & heating tracking is configured, then it does stuff
    heating = False  # type: bool
    cooling = False  # type: bool

    current_progress = 0  # type: int

    # Target temperature is stored here, for use with temp tracking.
    target_temperature = {"tool": 0, "bed": 0}  # type: dict
    current_heater_heating = None  # type: str
    tool_to_target = 0  # type: int

    previous_event_q = []  # type: list
    # Add effects to this list, if you want them to run after things like progress, torch, etc.

    lights_on = True  # Lights should be on by default, makes sense.  TODO #65
    torch_on = False  # Torch is off by default, because who would want that?

    torch_timer = None  # Timer for torch function
    return_timer = None  # Timer object when we want to return to idle.

    # Called when injections are complete
    def initialize(self):
        global PI_MODEL
        self.api = api.PluginApi(self)
        self.wizard = wizard.PluginWizard(self, PI_MODEL)

    # Asset plugin
    def get_assets(self):
        return {
            "js": ["js/ws281x_led_status.js"],
            "css": ["css/fontawesome5_stripped.css", "css/ws281x_led_status.css"],
        }

    # Startup plugin
    def on_startup(self, host, port):
        util.start_daemon_thread(
            target=self.run_os_config_check,
            kwargs={"send_ui": False},
            name="WS281x LED Status OS config test",
        )

    def on_after_startup(self):
        self.start_effect_process()

    # Shutdown plugin
    def on_shutdown(self):
        if self.current_effect_process is not None:
            self.effect_queue.put("KILL")
            self.current_effect_process.join()
        self._logger.info("WS281x LED Status runner stopped")

    # Settings plugin
    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self.restart_strip()

    def get_settings_defaults(self):
        return settings.defaults

    def get_settings_version(self):
        return settings.VERSION

    def on_settings_migrate(self, target, current):
        settings.migrate_settings(target, current, self._settings)

    # Template plugin
    def get_template_configs(self):
        return [
            {"type": "settings", "custom_bindings": True},
            {"type": "generic", "custom_bindings": True},
        ]

    def get_template_vars(self):
        global PI_MODEL
        return {
            "standard_names": constants.STANDARD_EFFECT_NICE_NAMES,
            "pi_model": PI_MODEL,
            "strip_types": constants.STRIP_TYPES,
            "timezone": util.get_timezone(),
            "version": self._plugin_version,
        }

    # Wizard plugin
    def is_wizard_required(self):
        for cmd in [
            api.WIZ_ADDUSER,
            api.WIZ_ENABLE_SPI,
            api.WIZ_INCREASE_BUFFER,
            api.WIZ_SET_CORE_FREQ,
            api.WIZ_SET_FREQ_MIN,
        ]:
            if not self.wizard.validate(cmd):
                return True
        return False

    def get_wizard_details(self):
        return self.wizard.on_api_get()

    def get_wizard_version(self):
        return 1

    def on_wizard_finish(self, handled):
        self._logger.info(
            "You will need to restart your Pi for the changes to take effect"
        )

    # Simple API plugin
    def get_api_commands(self):
        return self.api.get_api_commands()

    def on_api_command(self, command, data):
        return self.api.on_api_command(command, data)

    def on_api_get(self, request):
        return self.api.on_api_get(request=request)

    # Websocket communication
    def _send_UI_msg(self, msg_type, payload):
        self._plugin_manager.send_plugin_message(
            "ws281x_led_status", {"type": msg_type, "payload": payload}
        )

    # Effect runner process
    def start_effect_process(self):
        """
        Begin the LED runner process, with the user's settings, and some other config
        Sets internally self.current_effect_process
        Sets the current lights on/off status as well.
        :return: None
        """
        # Sanity check that I don't call this while it is alive
        if self.current_effect_process and not self.current_effect_process.is_alive():
            self.stop_effect_process()
        # Start effect runner here
        self.current_effect_process = multiprocessing.Process(
            target=EffectRunner,
            name="WS281x LED Status Effect Process",
            kwargs={
                "debug": self._settings.get_boolean(["debug_logging"]),
                "queue": self.effect_queue,
                "strip_settings": self._settings.get(["strip"], merged=True),
                "effect_settings": self._settings.get(["effects"], merged=True),
                "active_times_settings": self._settings.get(
                    ["active_times"], merged=True
                ),
                "previous_state": self.current_state,
                "log_path": self._settings.get_plugin_logfile_path(postfix="debug"),
            },
        )
        self.current_effect_process.daemon = True
        self.current_effect_process.start()
        self._logger.info("WS281x LED Status runner started")
        if self.lights_on:
            self.update_effect("on")
        else:
            self.update_effect("off")

    def stop_effect_process(self):
        """
        Stop the runner
        As this can potentially hang the server for a fraction of a second while the final frame of the effect runs,
        it is not called often - only on update of settings & shutdown.
        """
        if self.current_effect_process is not None:
            if self.current_effect_process.is_alive():
                self.effect_queue.put("KILL")
            self.current_effect_process.join()
        self._logger.info("WS281x LED Status runner stopped")

    def restart_strip(self):
        """
        Shortcut to restart the LED runner process.
        :return: None
        """
        self.stop_effect_process()
        self.start_effect_process()

    def run_os_config_check(self, send_ui=True):
        """
        Run a check on all of the OS level configuration required to run the plugin
        Logs output to octoprint.log, and optionally to the websocket
        :param send_ui: (bool) whether to send the results to the UI
        :return: None
        """
        _UI_MSG_TYPE = "os_config_test"
        self._logger.info(
            "Running OS config test ({} mode)".format("UI" if send_ui else "Log")
        )
        tests = {
            "adduser": self.wizard.is_adduser_done,
            "spi_enabled": self.wizard.is_spi_enabled,
            "spi_buffer_increase": self.wizard.is_spi_buffer_increased,
            "set_core_freq": self.wizard.is_core_freq_set,
            "set_core_freq_min": self.wizard.is_core_freq_min_set,
        }
        statuses = {}

        for test_key, test_func in tests.items():
            if send_ui:
                self._send_UI_msg(
                    _UI_MSG_TYPE, {"test": test_key, "status": "in_progress"}
                )
            status = "passed" if test_func() else "failed"
            if send_ui:
                self._send_UI_msg(_UI_MSG_TYPE, {"test": test_key, "status": status})
            statuses[test_key] = status
            if send_ui:
                # Artificially increase the length of time, to make the UI look nice.
                # Without this, there is a confusing amount of popping in/out of status etc.
                time.sleep(0.5)

        log_content = "OS config test complete. Results:"
        for test_key, status in statuses.items():
            log_content = log_content + "\n| - " + test_key + ": " + status

        if send_ui:
            self._send_UI_msg(_UI_MSG_TYPE, {"test": "complete", "status": "complete"})

        self._logger.info(log_content)

    def activate_lights(self):
        self._logger.info("Turning lights on")
        self.lights_on = True
        self.update_effect("on")
        self._send_UI_msg("lights", {"on": True})

    def deactivate_lights(self):
        self._send_UI_msg("lights", {"on": False})
        self.lights_on = False
        self.update_effect("off")
        self._logger.info("Turning light off")

    def activate_torch(self):
        if self.torch_timer and self.torch_timer.is_alive():
            self.torch_timer.cancel()

        toggle = self._settings.get_boolean(["effects", "torch", "toggle"])
        torch_time = self._settings.get_int(["effects", "torch", "timer"])

        if toggle:
            self._logger.debug("Torch toggling on")
            self.torch_on = True
            self.update_effect("torch")
        else:
            self._logger.debug("Torch timer started for {} secs".format(torch_time))
            self.torch_timer = util.start_daemon_timer(
                interval=torch_time,
                target=self.deactivate_torch,
            )
            self.torch_on = True
            self.update_effect("torch")

        self._send_UI_msg("torch", {"on": True})

    def deactivate_torch(self):
        self._logger.debug(
            "Deactivating torch mode, torch on currently: {}".format(self.torch_on)
        )
        if self.torch_on:
            self.torch_on = False
            self.update_effect(self.current_state)

        self._send_UI_msg("torch", {"on": False})

    def update_effect(self, mode_name, value=None, m150=None):
        """
        Change the effect displayed, use effects.EFFECTS for the correct names!
        If progress effect, value must be specified
        :param mode_name: string of mode name
        :param value: percentage of how far through it is. None
        :param m150: If the effect is an M150 effect, the full command should be passed here
        """
        if self.return_timer is not None and self.return_timer.is_alive():
            self.return_timer.cancel()

        if (
            not self._settings.get_boolean(["effects", "torch", "toggle"])
            and mode_name != "torch"
            and self.torch_on
        ):
            self.torch_on = False
        else:
            if mode_name != "torch" and self.torch_on:
                # Catch all other effects while torch is on - except M150
                if mode_name != "M150":
                    if "progress" in mode_name:
                        self.current_state = "{} {}".format(mode_name, value)
                    else:
                        self.current_state = mode_name

        if mode_name in ["on", "off"]:
            self.effect_queue.put(mode_name)
            return
        elif mode_name == "M150":
            if m150:
                self.effect_queue.put(m150)
            else:
                self._logger.warning("No values supplied with M150, ignoring")
            return

        if not self._settings.get(["effects", mode_name, "enabled"]):
            # If the effect is not enabled, we won't run it. Simple...
            return

        if "success" in mode_name:
            return_idle_time = self._settings.get_int(
                ["effects", "success", "return_to_idle"]
            )
            if return_idle_time > 0:
                self.return_timer = util.start_daemon_timer(
                    return_idle_time, self.update_effect, args=("idle",)
                )

        if "progress" in mode_name:
            if value is None:
                self._logger.warning(
                    "No value supplied with progress style effect, ignoring"
                )
                return
            self._logger.debug(
                "Updating progress effect {}, value {}".format(mode_name, value)
            )
            # Do the thing
            self.effect_queue.put("{} {}".format(mode_name, value))
            self.current_state = "{} {}".format(mode_name, value)
        else:
            self._logger.debug("Updating standard effect {}".format(mode_name))
            # Do the thing
            self.effect_queue.put(mode_name)
            if mode_name != "torch":
                self.current_state = mode_name

    def on_event(self, event, payload):
        if event == Events.PRINT_DONE:
            self.cooling = True
        elif event == Events.PRINT_STARTED:
            self.current_progress = 0
        elif event == Events.PRINT_RESUMED:
            self.update_effect("progress_print", self.current_progress)

        if event in constants.SUPPORTED_EVENTS:
            self.update_effect(constants.SUPPORTED_EVENTS[event])
            # add all events to a backlog, so we know what the last one was.
            self.add_to_backlog(event)

    def on_print_progress(self, storage="", path="", progress=1):
        if (progress == 100 and self.current_state == "success") or self.heating:
            return
        if self._settings.get_boolean(["effects", "printing", "enabled"]):
            self.update_effect("printing")
        self.update_effect("progress_print", progress)
        self.current_progress = progress

    def calculate_heatup_progress(self, current, target):
        if target <= 0:
            self._logger.warning(
                "Tried to calculate heating progress but target was zero"
            )
            self._logger.warning(
                "If you come across this please let me know on the issue tracker! - "
                "https://github.com/cp2004/OctoPrint-WS281x_LED_Status"
            )
            return 0

        # Allows for setting a baseline, so heating display doesn't start halfway down the strip.
        current = max(current - self._settings.get_int(["progress_temp_start"]), 0)
        target = max(target - self._settings.get_int(["progress_temp_start"]), 0)

        try:
            value = round((current / target) * 100)
        except ZeroDivisionError:
            value = 0

        return value

    def process_previous_event_q(self):
        """
        Runs the last event again, to put it back in the case of heating or cooling finishing, then clears the backlog.
        :return: None
        """
        if len(self.previous_event_q):
            self.on_event(self.previous_event_q[-1], payload={})
        self.previous_event_q = []

    def add_to_backlog(self, event):
        self.previous_event_q.append(event)

    def process_gcode_q(
        self,
        comm_instance,
        phase,
        cmd,
        cmd_type,
        gcode,
        subcode=None,
        tags=None,
        *args,
        **kwargs
    ):
        if gcode in constants.BLOCKING_TEMP_GCODES:
            bed_or_tool = {"M109": "tool", "M190": "bed"}
            # Everything is tracked, regardless of settings. Makes it easier to track the state, and then just back out
            # of showing the effect in self.update_effect() rather than getting complex here.
            self.heating = True
            self.current_heater_heating = bed_or_tool[gcode]
        else:
            if (
                self.heating
            ):  # State is switching to non-heating, so we should process the backlog.
                self.heating = False
                self.process_previous_event_q()
                if self._printer.is_printing():
                    self.on_print_progress(progress=self.current_progress)

        if gcode == "M150" and self._settings.get_boolean(["intercept_m150"]):
            self.update_effect("M150", m150=cmd)
            return (None,)

    def temperatures_received(
        self, comm_instance, parsed_temperatures, *args, **kwargs
    ):
        try:
            tool_temp_target = parsed_temperatures[
                "T{}".format(
                    self._settings.get_int(["effects", "progress_heatup", "tool_key"])
                )
            ][1]
        except KeyError:
            tool_temp_target = self.target_temperature["tool"]

        if (
            not tool_temp_target
        ):  # When heating, firmware reports more frequently but *without* target
            # It comes through to the handler as 'None', so we must check for this
            tool_temp_target = self.target_temperature["tool"]

        try:
            bed_temp_target = parsed_temperatures["B"][1]
        except KeyError:
            bed_temp_target = self.target_temperature["tool"]

        if not bed_temp_target:
            # Similarly to tool temp, sometimes comes through as NoneType
            bed_temp_target = self.target_temperature["bed"]

        self.target_temperature = {
            "tool": tool_temp_target
            if tool_temp_target > 0
            else self.target_temperature["tool"],
            "bed": bed_temp_target
            if bed_temp_target > 0
            else self.target_temperature["bed"],
        }
        words_to_tool = {  # maps 'progress_cooling_bed_or_tool' to the parsed temp
            "tool": "T{}".format(self.tool_to_target),
            "bed": "B",
        }
        if self.heating:
            try:
                current_temp = parsed_temperatures[
                    words_to_tool[self.current_heater_heating]
                ][0]
            except KeyError:
                self._logger.error(
                    "Heater {} not found, can't show progress. Check configuration".format(
                        self.current_heater_heating
                    )
                )
                self.heating = False
                self.process_previous_event_q()
                return

            self._logger.debug("State: heating, temp recv: {}".format(current_temp))
            if self.target_temperature[self.current_heater_heating] > 0:
                self.update_effect(
                    "progress_heatup",
                    self.calculate_heatup_progress(
                        current_temp,
                        self.target_temperature[self.current_heater_heating],
                    ),
                )

        elif self.cooling:
            if self._printer.is_printing() or self._printer.is_paused():
                # User has likely started a new print - stop cooling effect??
                self.cooling = False
                return

            current = parsed_temperatures[
                words_to_tool[
                    self._settings.get(["effects", "progress_cooling", "bed_or_tool"])
                ]
            ][0]
            self._logger.debug("State: cooling, temp recv: {}".format(current))

            if current < self._settings.get_int(
                ["effects", "progress_cooling", "threshold"]
            ):
                self.cooling = False
                self.process_previous_event_q()  # should hopefully put back the old effect (maybe progress)
                return
            self.update_effect(
                "progress_cooling",
                self.calculate_heatup_progress(
                    current,
                    self.target_temperature[
                        self._settings.get(
                            ["effects", "progress_cooling", "bed_or_tool"]
                        )
                    ],
                ),
            )

        return parsed_temperatures

    def process_at_command(
        self, comm, phase, command, parameters, tags=None, *args, **kwargs
    ):
        if command not in constants.AT_COMMANDS or not self._settings.get(
            ["at_command_reaction"]
        ):
            return

        if command == constants.ON_AT_COMMAND:
            self._logger.debug("Recieved gcode @ command for lights on")
            self.activate_lights()
        elif command == constants.OFF_AT_COMMAND:
            self._logger.debug("Recieved gcode @ command for lights off")
            self.deactivate_lights()
        elif (
            command == constants.TORCH_AT_COMMAND
            or command == constants.TORCH_ON_AT_COMMAND
        ):
            self._logger.debug("Recieved gcode @ command for torch ON")
            self.activate_torch()
        elif command == constants.TORCH_OFF_AT_COMMAND and self._settings.get_boolean(
            ["effects", "torch", "toggle"]
        ):
            self._logger.debug("Recieved gcode @ command for torch OFF")
            self.deactivate_torch()

    # Softwareupdate hook
    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "ws281x_led_status": {
                "displayName": "WS281x LED Status",
                "displayVersion": self._plugin_version,
                # version check: github repository
                "type": "github_release",
                "user": "cp2004",
                "repo": "OctoPrint-WS281x_LED_Status",
                "stable_branch": {
                    "name": "Stable",
                    "branch": "master",
                    "comittish": ["master"],
                },
                "prerelease_branches": [
                    {
                        "name": "Release Candidate",
                        "branch": "pre-release",
                        "comittish": ["pre-release", "master"],
                    }
                ],
                "current": self._plugin_version,
                # update method: pip
                "pip": "https://github.com/cp2004/OctoPrint-WS281x_LED_Status/archive/{target_version}.zip",
            }
        }


__plugin_name__ = "WS281x LED Status"
__plugin_pythoncompat__ = ">=2.7,<4"  # python 2 and 3
__plugin_version__ = __version__

_proc_dt_model = None


# Raspberry Pi detection, borrowed from OctoPrint's Pi support plugin
# https://github.com/OctoPrint/OctoPrint/blob/master/src/octoprint/plugins/pi_support/__init__.py
def get_proc_dt_model():
    global _proc_dt_model

    if _proc_dt_model is None:
        with io.open(constants.PROC_DT_MODEL_PATH, "rt", encoding="utf-8") as f:
            _proc_dt_model = f.readline().strip(" \t\r\n\0")

    return _proc_dt_model


def determine_pi_version():
    """
    Determines Raspberry Pi version for use in the wizard & config test
    :return: (str) Pi Model, if found, else None
    """
    logger = logging.getLogger("octoprint.plugins.ws281x_led_status")
    global _proc_dt_model
    if not _proc_dt_model:
        _proc_dt_model = get_proc_dt_model()

    try:
        model_no = re.search(constants.PI_REGEX, _proc_dt_model).group(1).strip()
    except IndexError:
        logger.error(
            "Pi model string detected as `{}`, unable to be parsed by regex".format(
                _proc_dt_model
            )
        )
        raise
    logger.info("Detected running on a Raspberry Pi {}".format(model_no))
    global PI_MODEL
    PI_MODEL = model_no


def __plugin_check__():
    try:
        proc_dt_model = get_proc_dt_model()
        if proc_dt_model is None:
            return False
    except Exception:
        return False

    return "raspberry pi" in proc_dt_model.lower()


def __plugin_load__():
    # Attempt to parse the Pi version, if so set PI_MODEL
    determine_pi_version()

    global __plugin_implementation__
    __plugin_implementation__ = WS281xLedStatusPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.process_gcode_q,
        "octoprint.comm.protocol.temperatures.received": __plugin_implementation__.temperatures_received,
        "octoprint.comm.protocol.atcommand.sending": __plugin_implementation__.process_at_command,
    }
