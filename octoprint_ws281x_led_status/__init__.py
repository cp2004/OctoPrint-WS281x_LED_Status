# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

__author__ = "Charlie Powell <cp2004.github@gmail.com"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Charlie Powell 2020-2021 - released under the terms of the AGPLv3 License"

import io
import logging
import multiprocessing
import os
import re
import time

# noinspection PyPackageRequirements
import octoprint.plugin
from octoprint.events import Events, all_events
from octoprint.util.version import is_octoprint_compatible

from octoprint_ws281x_led_status import (
    api,
    constants,
    settings,
    triggers,
    util,
    wizard,
)
from octoprint_ws281x_led_status.constants import (
    AtCommands,
    DeprecatedAtCommands,
)
from octoprint_ws281x_led_status.runner import EffectRunner
from octoprint_ws281x_led_status.util import RestartableTimer

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
    def __init__(self):
        super(WS281xLedStatusPlugin, self).__init__()

        # Submodules
        self.api = api.PluginApi(self)  # type: api.PluginApi
        self.wizard = wizard.PluginWizard(PI_MODEL)  # type: wizard.PluginWizard

        self.current_effect_process = None  # type: multiprocessing.Process
        self.effect_queue = multiprocessing.Queue()  # type: multiprocessing.Queue

        self.custom_triggers = triggers.Trigger(
            self.effect_queue
        )  # type: triggers.Trigger

        # Effect states
        self.previous_state = ""
        self.current_state = {"type": "standard", "effect": "blank"}
        self.next_state = ""

        # Heating detection flags. True/False, when True & heating tracking is configured, then it does stuff
        self.heating = False  # type: bool
        self.cooling = False  # type: bool

        self.current_progress = 0  # type: int

        self.current_heater_heating = None  # type: str
        self.previous_target = {
            "tool": 0,
            "bed": 0,
        }  # Store last non-zero target here, for cooling tracking
        self.tool_to_target = 0  # type: int

        self.previous_event = (
            ""
        )  # type: str # Effect here will be run when progress expires

        self.lights_on = True  # Lights should be on by default, makes sense.
        self.torch_on = False  # Torch is off by default, because who would want that?

        self.torch_timer = RestartableTimer(
            interval=30,  # Default, overwritten on settings save TODO!
            function=self.deactivate_torch,
        )
        self.return_timer = RestartableTimer(
            interval=30,  # Default
            function=self.update_effect,
            args=({"type": "standard", "effect": "idle"},),
        )
        self.idle_timer = RestartableTimer(
            interval=30,
            function=self.idle_timeout,
        )
        self.idle_timed_out = False

    # Called when injections are complete
    def initialize(self):
        if self._settings.get_boolean(["effects", "startup", "enabled"]):
            self.current_state["effect"] = "startup"

        if self._settings.get_boolean(["lights_on"]):
            self.lights_on = True
        else:
            self.lights_on = False

    # Asset plugin
    def get_assets(self):
        css_assets = ["css/ws281x_led_status.css"]
        if is_octoprint_compatible("<1.5.0"):
            # OctoPrint 1.5.0 updated to FA5
            css_assets.append("css/fontawesome5_stripped.css")

        return {
            "js": ["js/ws281x_led_status.js"],
            "css": css_assets,
        }

    # Startup plugin
    def on_startup(self, host, port):
        self.custom_triggers.process_settings(
            self._settings.get(["custom"], merged=True)
        )
        util.start_daemon_thread(
            target=self.run_os_config_check,
            kwargs={"send_ui": False},
            name="WS281x LED Status OS config test",
        )

    def on_after_startup(self):
        self.start_effect_process()

    # Shutdown plugin
    def on_shutdown(self):
        self.stop_effect_process()

    # Settings plugin
    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

        self.custom_triggers.process_settings(
            self._settings.get(["custom"], merged=True)
        )

        self.torch_timer.interval = self._settings.get_int(
            ["effects", "torch", "timer"]
        )
        self.return_timer.interval = self._settings.get_int(
            ["effects", "success", "return_to_idle"]
        )
        self.idle_timer.interval = self._settings.get_int(
            ["effects", "idle", "timeout"]
        )

        self.restart_strip()

    def get_settings_defaults(self):
        return settings.defaults

    def get_settings_version(self):
        return settings.VERSION

    def on_settings_migrate(self, target, current):
        settings.migrate_settings(target, current, self._settings)

    # Template plugin
    def get_template_configs(self):
        return [{"type": "navbar", "styles": ["display: flex"]}]

    def get_template_vars(self):
        global PI_MODEL
        return {
            "standard_names": constants.EFFECTS.keys(),
            "progress_names": constants.PROGRESS_EFFECTS.keys(),
            "pi_model": PI_MODEL,
            "strip_types": constants.STRIP_TYPES,
            "timezone": util.get_timezone(),
            "version": self._plugin_version,
            "is_docker": os.path.exists(os.path.join("/bin", "s6-svscanctl"))
            or os.path.exists(
                os.path.join("/usr", "local", "bin", "docker-entrypoint.sh")
            ),
            "docs_url": constants.DOCS_FULL_LINK,
            "all_events": all_events(),
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
            if not self.wizard.validate(cmd)["passed"]:
                return True
        return False

    def get_wizard_details(self):
        return self.wizard.on_api_get()

    def get_wizard_version(self):
        return 1

    def on_wizard_finish(self, handled):
        self._logger.warning(
            "You will need to restart your Pi for OS changes to take effect"
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

    # Event Handler plugin
    def on_event(self, event, payload):
        if event == Events.PRINT_DONE:
            self.cooling = True
        elif event == Events.PRINT_STARTED:
            self.cooling = False
            self.current_progress = 0
        elif event == Events.PRINT_RESUMED:
            self.update_effect(
                {
                    "type": "progress",
                    "effect": "progress_print",
                    "value": self.current_progress,
                }
            )

        if event in constants.SUPPORTED_EVENTS.keys():
            effect = constants.SUPPORTED_EVENTS[event]
            self.update_effect({"type": "standard", "effect": effect})
            # Record the event's effect so that it can used when progress expires
            self.previous_event = effect

        self.custom_triggers.on_event(event)

    # Progress plugin
    def on_print_progress(self, storage="", path="", progress=1):
        if (
            (
                progress == 100
                and self.current_state["type"] == "standard"
                and self.current_state["effect"] == "success"
            )
            or (
                self.heating
                and self._settings.get_boolean(
                    ["effects", "progress_heatup", "enabled"]
                )
            )
            or (
                self.cooling
                and self._settings.get_boolean(
                    ["effects", "progress_cooling", "enabled"]
                )
            )
        ):
            # Skip 100% if necessary, as success event usually comes before this
            return

        if self._settings.get_boolean(["effects", "printing", "enabled"]):
            self.update_effect({"type": "standard", "effect": "printing"})
        else:
            self.update_effect(
                {"type": "progress", "effect": "progress_print", "value": progress}
            )

        self.current_progress = progress

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
                "debug": self._settings.get_boolean(["features", "debug_logging"]),
                "queue": self.effect_queue,
                "strip_settings": self._settings.get(["strip"], merged=True),
                "effect_settings": self._settings.get(["effects"], merged=True),
                "features_settings": self._settings.get(["features"], merged=True),
                "previous_state": self.current_state,
                "log_path": self._settings.get_plugin_logfile_path(postfix="debug"),
                "saved_lights_on": self.lights_on,
            },
        )
        self.current_effect_process.daemon = True
        self.current_effect_process.start()
        self._logger.info("WS281x LED Status runner started")
        if self.lights_on:
            self.effect_queue.put(constants.ON_MSG)
        else:
            self.effect_queue.put(constants.OFF_MSG)

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

    # OS Config test
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
            "adduser": api.WIZ_ADDUSER,
            "spi_enabled": api.WIZ_ENABLE_SPI,
            "spi_buffer_increase": api.WIZ_INCREASE_BUFFER,
            "set_core_freq": api.WIZ_SET_CORE_FREQ,
            "set_core_freq_min": api.WIZ_SET_FREQ_MIN,
        }
        statuses = {}

        for test_key, command in tests.items():
            if send_ui:
                self._send_UI_msg(
                    _UI_MSG_TYPE, {"test": test_key, "status": "in_progress"}
                )

            status = self.wizard.validate(command)
            if send_ui:
                self._send_UI_msg(_UI_MSG_TYPE, {"test": test_key, "status": status})

            statuses[test_key] = status
            if send_ui:
                # Artificially increase the length of time, to make the UI look nice.
                # Without this, there is a confusing amount of popping in/out of status etc.
                time.sleep(0.3)

        log_content = "OS config test complete. Results:"
        for test_key, status in statuses.items():
            log_content = log_content + "\n| - {}: {}".format(
                test_key, status["passed"]
            )
            if not status["passed"]:
                log_content = log_content + " !! Reason: {}".format(status["reason"])

        if send_ui:
            self._send_UI_msg(_UI_MSG_TYPE, {"test": "complete", "status": "complete"})

        self._logger.info(log_content)

    # Lights and torch on/off handling
    def switch_lights(self, state):
        # Notify the UI
        self._send_UI_msg("lights", {"on": state})
        # Actually do the action
        self.lights_on = state
        self.effect_queue.put(constants.ON_MSG if state else constants.OFF_MSG)
        # Store state across restart
        self._settings.set(["lights_on"], state)
        self._settings.save()
        # Logs
        self._logger.info("Switched lights, on: {}".format(state))

    def activate_torch(self):
        self.torch_timer.stop()

        toggle = self._settings.get_boolean(["effects", "torch", "toggle"])
        torch_time = self._settings.get_int(["effects", "torch", "timer"])

        self.next_state = self.current_state

        if toggle:
            self._logger.debug("Torch toggling on")
        else:
            self._logger.debug("Torch timer started for {} secs".format(torch_time))
            self.torch_timer.start()

        self.update_effect({"type": "standard", "effect": "torch"})
        self.torch_on = True

        self._send_UI_msg("torch", {"on": True})

    def deactivate_torch(self):
        self._logger.debug("Deactivating torch mode")
        if self.torch_on:
            self.torch_on = False
            # Return whatever state we have suppressed
            self.update_effect(self.next_state)

        self._send_UI_msg("torch", {"on": False})

    def update_effect(self, mode):
        """
        Change the effect displayed, use effects.EFFECTS for the correct names!
        If progress effect, value must be specified
        :param mode: (str) effect to be run
        """

        # If torch is on, state is saved until torch is finished
        if (
            self.torch_on
            and mode["type"] in ["standard", "progress"]
            and mode["effect"] != "torch"
        ):
            self.next_state = mode
            return

        # If the mode is an M150 command, then set state. M150 enabled has already been checked.
        elif mode["type"] == "M150":
            self.effect_queue.put(mode)
            self.set_state(mode)

        if mode["type"] in ["standard", "progress"]:
            self._send_standard_effect(mode)

    def _send_standard_effect(self, mode):
        # Check the effect is enabled
        if not self._settings.get(["effects", mode["effect"], "enabled"]):
            return

        # Stop timers, new effects take priority over return to idle or idle timout
        if self.return_timer.is_alive():
            self._logger.debug("Stopping return to idle timer, new effect")
            self.return_timer.stop()
        if self.idle_timer.is_alive():
            self._logger.debug("Stopping idle timeout timer, new effect")
            self.idle_timer.stop()

        # Start idle timeout
        if (
            mode["effect"] == "idle"
            and self._settings.get_int(["effects", "idle", "timeout"]) > 0
        ):
            self.idle_timer.start()

        elif self.idle_timed_out:
            # Timed out previously, turn lights back on for this effect
            self.switch_lights(True)
            self.idle_timed_out = False

        # Start return to idle timer
        if (
            mode["effect"] == "success"
            and self._settings.get_int(["effects", "success", "return_to_idle"]) > 0
        ):
            self.return_timer.start()

        # Finally, start actually updating the effect
        self._logger.debug("Updating effect to {}".format(mode))
        self.effect_queue.put(mode)
        if mode["effect"] != "torch":
            self.set_state(mode)

    def set_state(self, new_state):
        self.previous_state = self.current_state
        self.current_state = new_state

    def calculate_heatup_progress(self, current, target):
        # Allows for setting a baseline, so heating display doesn't start halfway down the strip.
        current = max(current - self._settings.get_int(["progress_temp_start"]), 0)
        target = max(target - self._settings.get_int(["progress_temp_start"]), 0)

        try:
            return round((current / target) * 100)
        except ZeroDivisionError:
            self._logger.warning(
                "Tried to calculate heating progress but target was zero"
            )
            return 0

    def process_previous_event(self):
        """
        Runs the last event again, to put it back in the case of heating or cooling finishing, then clears the backlog.
        :return: None
        """
        if self.previous_event:
            self.update_effect({"type": "standard", "effect": self.previous_event})
        self.previous_event = ""

    def idle_timeout(self):
        self.idle_timed_out = True
        self.switch_lights(False)

    # Hooks
    def process_gcode_q(
        self,
        _comm_instance,
        _phase,
        cmd,
        _cmd_type,
        gcode,
        _subcode=None,
        _tags=None,
        *_args,
        **_kwargs
    ):
        if gcode in constants.BLOCKING_TEMP_GCODES.keys():
            # New M109 or M190, start tracking heating
            self.heating = True
            self.current_heater_heating = constants.BLOCKING_TEMP_GCODES[gcode]

        elif gcode == "M150" and self._settings.get_boolean(
            ["features", "intercept_m150"]
        ):
            # Update effect to M150 and suppress it
            self.update_effect({"type": "M150", "command": cmd})
            return (None,)

        else:
            if self.heating:
                # Currently heating, now stopping - go back to last event
                self.heating = False
                if self._printer.is_printing():
                    # If printing, go back to print progress immediately
                    self.on_print_progress(progress=self.current_progress)
                else:
                    # Otherwise go back to the previous effect
                    self.process_previous_event()

        self.custom_triggers.on_gcode_command(gcode, cmd)

    def temperatures_received(self, _comm, parsed_temps, *_args, **_kwargs):
        if not self.heating and not self.cooling:
            # Don't waste time if we're not doing anything
            return parsed_temps

        def abort():
            self.process_previous_event()
            return parsed_temps

        # Find the tool target temperature from OctoPrint
        tool_target = self._printer.get_current_temperatures()[
            "tool{}".format(
                self._settings.get(["effects", "progress_heatup", "tool_key"])
            )
        ]["target"]

        # Find the bed target temperature from OctoPrint
        bed_target = self._printer.get_current_temperatures()["bed"]["target"]

        if tool_target is not None and tool_target > 0:
            self.previous_target["tool"] = tool_target

        if bed_target is not None and bed_target > 0:
            self.previous_target["bed"] = tool_target

        if self.heating:
            # Find out current temperature from parsed
            if self.current_heater_heating == "tool":
                heater = "T{}".format(
                    self._settings.get(["effects", "progress_heatup", "tool_key"])
                )
                target = tool_target
            else:
                heater = "B"
                target = bed_target

            try:
                current_temp = parsed_temps[heater][0]
            except KeyError:
                # Abort if that tool does not exist - maybe misconfiguration
                self._logger.error(
                    "Heater {} not found, can't show heating progress".format(heater)
                )
                self.heating = False
                return abort()

            # Stop if current is above target
            if current_temp > target:
                self.heating = False
                return abort()

            self.update_effect(
                {
                    "type": "progress",
                    "effect": "progress_heatup",
                    "value": self.calculate_heatup_progress(current_temp, target),
                }
            )

        elif self.cooling:
            if (
                self._settings.get(["effects", "progress_cooling", "bed_or_tool"])
                == "tool"
            ):
                heater = "T{}".format(
                    self._settings.get(["effects", "progress_heatup", "tool_key"])
                )
                target = self.previous_target["tool"]
            else:
                heater = "B"
                target = self.previous_target["bed"]

            try:
                current = parsed_temps[heater][0]
            except KeyError:
                # Abort if that tool does not exist - maybe misconfiguration
                self._logger.error(
                    "Heater {} not found, can't show cooling progress".format(heater)
                )
                self.heating = False
                return abort()

            if current < self._settings.get_int(
                ["effects", "progress_cooling", "threshold"]
            ):
                self.cooling = False
                return abort()

            self.update_effect(
                {
                    "type": "progress",
                    "effect": "progress_cooling",
                    "value": self.calculate_heatup_progress(current, target),
                }
            )

        return parsed_temps

    def process_at_command(
        self, _comm, _phase, cmd, params, _tags=None, *_args, **_kwargs
    ):
        if not self._settings.get(["features", "at_command_reaction"]):
            return

        cmd = cmd.upper()

        if cmd == "WS":
            params = params.upper()

            if params == AtCommands.LIGHTS_ON:
                self.switch_lights(True)
            elif params == AtCommands.LIGHTS_OFF:
                self.switch_lights(False)
            elif params == AtCommands.LIGHTS_TOGGLE:
                self.switch_lights(not self.lights_on)
            elif params in [AtCommands.TORCH, AtCommands.TORCH_ON]:
                self.activate_torch()
            elif params == AtCommands.TORCH_OFF and self._settings.get_boolean(
                ["effects", "torch", "toggle"]
            ):
                self.deactivate_torch()
            elif params[0:6] == AtCommands.CUSTOM:
                self.custom_triggers.on_at_command(params[7:])  # Strip off "CUSTOM"

        elif cmd[0:3] == "WS_":
            if cmd == DeprecatedAtCommands.LIGHTS_ON:
                self.switch_lights(True)
                self.deprecated_at_command(cmd)
            elif cmd == DeprecatedAtCommands.LIGHTS_OFF:
                self.switch_lights(False)
                self.deprecated_at_command(cmd)
            elif cmd in [
                DeprecatedAtCommands.TORCH,
                DeprecatedAtCommands.TORCH_ON,
            ]:
                self.activate_torch()
                self.deprecated_at_command(cmd)
            elif cmd == DeprecatedAtCommands.TORCH_OFF and self._settings.get_boolean(
                ["effects", "torch", "toggle"]
            ):
                self.deactivate_torch()
                self.deprecated_at_command(cmd)

    def deprecated_at_command(self, cmd):
        # These styles of commands are deprecated, and raise a warning
        self._logger.warning(
            "!! Deprecated @ command used, please use the newer alternatives."
            " Support will be removed in a future version"
        )
        self._logger.warning("!! Command used: {}".format(cmd))
        self._logger.warning(
            "!! See https://cp2004.gitbook.io/ws281x-led-status/documentation/host-commands"
            " for more info"
        )

        self._send_UI_msg("at_cmd_deprecation", cmd)

    # Software update hook
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
                    },
                    {
                        "name": "Development",
                        "branch": "devel",
                        "comittish": ["devel", "master"],
                    },
                ],
                "current": self._plugin_version,
                # update method: pip
                "pip": "https://github.com/cp2004/OctoPrint-WS281x_LED_Status/archive/{target_version}.zip",
            }
        }


__plugin_name__ = "WS281x LED Status"
__plugin_pythoncompat__ = ">=2.7,<4"  # python 2 and 3
__plugin_version__ = __version__
__plugin_implementation__ = None
__plugin_hooks__ = None


_proc_dt_model = None


# Raspberry Pi detection, borrowed from OctoPrint's Pi support plugin
# https://github.com/OctoPrint/OctoPrint-PiSupport/blob/158c7af065a91429cfba1b48deae183b4df8a301/octoprint_pi_support/__init__.py#L464-L472
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
            "Pi model string detected as `{}`, unable to be parsed".format(
                _proc_dt_model
            )
        )
        raise
    logger.info("Detected running on a Raspberry Pi {}".format(model_no))
    global PI_MODEL
    PI_MODEL = model_no
    return PI_MODEL


def __plugin_check__():
    logger = logging.getLogger("octoprint.plugins.ws281x_led_status")

    def log_abort():
        logger.warning("No Raspberry Pi detected, will not load plugin")

    try:
        proc_dt_model = get_proc_dt_model()
        if proc_dt_model is None:
            log_abort()
            return False
    except Exception as e:
        log_abort()
        logger.warning("Exception suppressed: {}".format(repr(e)))
        return False

    if "raspberry pi" in proc_dt_model.lower():
        return True
    else:
        log_abort()
        return False


def __plugin_load__():
    logger = logging.getLogger("octoprint.plugins.ws281x_led_status")

    # Attempt to parse the Pi version, if so set PI_MODEL global
    try:
        determine_pi_version()
    except Exception as e:
        logger.error("Error detecting Pi model, plugin could not be loaded")
        logger.error("Please report this on WS281x LED Status's issue tracker!")
        logger.error(repr(e))
        return

    global __plugin_implementation__
    __plugin_implementation__ = WS281xLedStatusPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.process_gcode_q,
        "octoprint.comm.protocol.temperatures.received": __plugin_implementation__.temperatures_received,
        "octoprint.comm.protocol.atcommand.sending": __plugin_implementation__.process_at_command,
    }
