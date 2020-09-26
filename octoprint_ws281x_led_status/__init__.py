# coding=utf-8
from __future__ import absolute_import, division, unicode_literals

import multiprocessing
import re
import io
import time
import threading

import octoprint.plugin
from flask import jsonify

from octoprint_ws281x_led_status.runner import EffectRunner, STRIP_TYPES, STRIP_SETTINGS, MODES
import octoprint_ws281x_led_status.wizard


PI_REGEX = r"(?<=Raspberry Pi)(.*)(?=Model)"
_PROC_DT_MODEL_PATH = "/proc/device-tree/model"
BLOCKING_TEMP_GCODES = ["M109", "M190"]  # TODO make configurable? No one has complained about it yet...

ON_AT_COMMAND = 'WS_LIGHTSON'
OFF_AT_COMMAND = 'WS_LIGHTSOFF'
TORCH_AT_COMMAND = 'WS_TORCH'
AT_COMMANDS = [ON_AT_COMMAND, OFF_AT_COMMAND, TORCH_AT_COMMAND]

STANDARD_EFFECT_NICE_NAMES = {
    'Solid Color': 'solid',
    'Color Wipe': 'wipe',
    'Color Wipe 2': 'wipe2',
    'Pulse': 'pulse',
    'Bounce': 'bounce',
    'Bounce Solo': 'bounce_solo',
    'Rainbow': 'rainbow',
    'Rainbow Cycle': 'cycle',
    'Random': 'random',
    'Blink': 'blink',
    'Crossover': 'cross',
    'Bouncy Balls': 'balls'
}


class WS281xLedStatusPlugin(octoprint.plugin.StartupPlugin,
                            octoprint.plugin.ShutdownPlugin,
                            octoprint.plugin.SettingsPlugin,
                            octoprint.plugin.AssetPlugin,
                            octoprint.plugin.TemplatePlugin,
                            octoprint.plugin.SimpleApiPlugin,
                            octoprint.plugin.WizardPlugin,
                            octoprint.plugin.ProgressPlugin,
                            octoprint.plugin.EventHandlerPlugin,
                            octoprint.plugin.RestartNeedingPlugin):
    supported_events = {
        'Connected': 'idle',
        'Disconnected': 'disconnected',
        'PrintFailed': 'failed',
        'PrintDone': 'success',
        'PrintPaused': 'paused'
    }
    current_effect_process = None  # multiprocessing Process object
    current_state = 'startup'  # Used to put the old effect back on settings change/light switch
    effect_queue = multiprocessing.Queue()  # pass name of effects here

    SETTINGS = {}  # Filled in on startup
    PI_MODEL = None  # Filled in on startup

    # Heating detection flags. True/False, when True & heating tracking is configured, then it does stuff
    heating = False
    cooling = False

    # Target temperature is stored here, for use with temp tracking.
    target_temperature = {"tool": 0, "bed": 0}
    current_heater_heating = None

    previous_event_q = []  # Add effects to this list, if you want them to run after things like progress, torch, etc.

    lights_on = True  # Lights should be on by default, makes sense.
    torch_on = False  # Torch is off by default, because who would want that?

    torch_timer = None  # Timer for torch function
    return_timer = None  # Timer object when we want to return to idle.

    # Asset plugin
    def get_assets(self):
        return dict(
            js=['js/ws281x_led_status.js'],
            css=['css/fontawesome5_stripped.css', 'css/ws281x_led_status.css'],
        )

    # Startup plugin
    def on_startup(self, host, port):
        self.PI_MODEL = self.determine_pi_version()

    def on_after_startup(self):
        self.refresh_settings()
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
        self.refresh_settings()
        self.restart_strip()

    def get_settings_defaults(self):
        return dict(
            debug_logging=False,

            led_count=24,
            led_pin=10,
            led_freq_hz=800000,
            led_dma=10,
            led_invert=False,
            led_brightness=50,
            led_channel=0,
            strip_type='WS2811_STRIP_GRB',

            startup_enabled=True,
            startup_effect='Color Wipe',
            startup_color='#00ff00',
            startup_delay='75',

            idle_enabled=True,
            idle_effect='Color Wipe 2',
            idle_color='#00ccf0',
            idle_delay='75',

            disconnected_enabled=True,
            disconnected_effect='Rainbow Cycle',
            disconnected_color='#000000',
            disconnected_delay='25',

            failed_enabled=True,
            failed_effect='Pulse',
            failed_color='#ff0000',
            failed_delay='10',

            success_enabled=True,
            success_effect='Rainbow',
            success_color='#000000',
            success_delay='25',
            success_return_idle='0',

            paused_enabled=True,
            paused_effect='Bounce',
            paused_color='#0000ff',
            paused_delay='40',

            progress_print_enabled=True,
            progress_print_color_base='#000000',
            progress_print_color='#00ff00',

            printing_enabled=False,
            printing_effect='Solid Color',
            printing_color='#ffffff',
            printing_delay=1,

            progress_heatup_enabled=True,
            progress_heatup_color_base='#0000ff',
            progress_heatup_color='#ff0000',
            progress_heatup_tool_enabled=True,
            progress_heatup_bed_enabled=True,
            progress_heatup_tool_key=0,

            progress_cooling_enabled=True,
            progress_cooling_color_base='#0000ff',
            progress_cooling_color='#ff0000',
            progress_cooling_bed_or_tool='tool',
            progress_cooling_threshold='40',

            torch_enabled=True,
            torch_effect='Solid Color',
            torch_color='#ffffff',
            torch_delay=1,
            torch_timer=15,

            active_hours_enabled=False,
            active_hours_start="09:00",
            active_hours_stop="21:00",

            at_command_reaction=True,
            intercept_m150=True
        )

    # Template plugin
    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]

    def get_template_vars(self):
        return {
            'standard_names': STANDARD_EFFECT_NICE_NAMES,
            'pi_model': self.PI_MODEL,
            'strip_types': STRIP_TYPES,
            'timezone': self.get_timezone()
        }

    @staticmethod
    def get_timezone():
        return time.tzname

    # Wizard plugin bits
    def is_wizard_required(self):
        for item in self.get_wizard_details().values():
            if not item:
                return True
        return False

    def get_wizard_details(self):
        return wizard.get_wizard_info(self.PI_MODEL)

    def get_wizard_version(self):
        return 1

    def on_wizard_finish(self, handled):
        self._logger.info("You will need to restart your Pi for the changes to take effect")
        # TODO make this a popup? not very useful here
        # Requires implementing a plugin message system...

    # Simple API plugin
    def get_api_commands(self):
        return dict(
            toggle_lights=[],
            activate_torch=[],
            adduser=['password'],
            enable_spi=['password'],
            spi_buffer_increase=['password'],
            set_core_freq=['password'],
            set_core_freq_min=['password']
        )

    def on_api_command(self, command, data):
        if command == 'toggle_lights':
            self.toggle_lights()
            return self.on_api_get()
        elif command == 'activate_torch':
            self.activate_torch()
            return self.on_api_get()

        return wizard.run_wizard_command(command, data, self.PI_MODEL)

    def on_api_get(self, request=None):
        return jsonify(
            lights_status=self.get_lights_status(),
            torch_status=self.get_torch_status()
        )

    def toggle_lights(self):
        self.lights_on = False if self.lights_on else True  # Switch from False -> True or True -> False
        self.update_effect('on' if self.lights_on else 'off')
        self._logger.debug("Toggling lights to {}".format('on' if self.lights_on else 'off'))

    def activate_torch(self):
        if self.torch_timer and self.torch_timer.is_alive():
            self.torch_timer.cancel()

        self._logger.debug("Torch Timer started for {} secs".format(self._settings.get_int(['torch_timer'])))
        self.torch_timer = threading.Timer(int(self._settings.get_int(['torch_timer'])), self.deactivate_torch)
        self.torch_timer.daemon = True
        self.torch_timer.start()
        self.torch_on = True
        self.update_effect('torch')

    def deactivate_torch(self):
        self._logger.debug("Deactivating torch mode, torch on currently: {}".format(self.torch_on))
        if self.torch_on:
            self.update_effect(self.current_state)
            self.torch_on = False

    def get_lights_status(self):
        return self.lights_on

    def get_torch_status(self):
        return self.torch_on

    # My methods
    def determine_pi_version(self):
        """
        Determines Raspberry Pi version for use in the wizard (and potentially later to warn of config issues)
        :return: (str) Pi Model, if found, else None
        """
        with io.open(_PROC_DT_MODEL_PATH, 'rt', encoding='utf-8') as f:
            _proc_dt_model = f.readline().strip(" \t\r\n\0")
        if _proc_dt_model:
            model_no = re.search(PI_REGEX, _proc_dt_model).group().strip()
            self._logger.info("Detected running on a Raspberry Pi {}".format(model_no))
            return model_no
        else:
            self._logger.error("Pi not found, why did you install this!!")
            self._logger.error("This plugin is about to break...")

    def refresh_settings(self):
        """
        Update self.SETTINGS dict to custom data structure
        """
        self.tool_to_target = self._settings.get_int(['progress_heatup_tool_key'])
        if not self.tool_to_target:
            self.tool_to_target = 0

        self.SETTINGS['active_start'] = self._settings.get(['active_hours_start']) \
            if self._settings.get(['active_hours_enabled']) else None
        self.SETTINGS['active_stop'] = self._settings.get(['active_hours_stop']) \
            if self._settings.get(['active_hours_enabled']) else None

        self.SETTINGS['strip'] = {}
        for setting in STRIP_SETTINGS:
            if setting == 'led_invert':  # Boolean settings
                self.SETTINGS['strip'][setting] = self._settings.get_boolean([setting])
            elif setting == 'strip_type':  # String settings
                self.SETTINGS['strip']['strip_type'] = self._settings.get([setting])
            elif setting == 'led_brightness':  # Percentage
                self.SETTINGS['strip']['led_brightness'] = min(
                    int(round((self._settings.get_int([setting]) / 100) * 255)), 255)
            else:  # Integer settings
                self.SETTINGS['strip'][setting] = self._settings.get_int([setting])

        for mode in MODES:
            mode_settings = {'enabled': self._settings.get_boolean(['{}_enabled'.format(mode)]),
                             'color': self._settings.get(['{}_color'.format(mode)])}
            if 'progress' in mode:  # Unsure if this works?
                mode_settings['base'] = self._settings.get(['{}_color_base'.format(mode)])
            else:
                effect_nice_name = self._settings.get(['{}_effect'.format(mode)])
                effect_name = STANDARD_EFFECT_NICE_NAMES[effect_nice_name]
                mode_settings['effect'] = effect_name
                mode_settings['delay'] = round(float(self._settings.get(['{}_delay'.format(mode)])), 1)
            self.SETTINGS[mode] = mode_settings

        self._logger.info("Settings refreshed")

    def restart_strip(self):
        """
        Shortcut to restart the LED runner process.
        :return: None
        """
        self.stop_effect_process()
        self.start_effect_process()

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
            args=(
                self._settings.get_plugin_logfile_path(postfix="debug"),
                self._settings.get_boolean(["debug_logging"]),
                self.effect_queue,
                self.SETTINGS,
                self.current_state),
        )
        self.current_effect_process.daemon = True
        self.current_effect_process.start()
        self._logger.info("Ws281x LED Status runner started")
        if self.lights_on:
            self.update_effect('on')
        else:
            self.update_effect('off')

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

    def update_effect(self, mode_name, value=None, m150=None):
        """
        Change the effect displayed, use effects.EFFECTS for the correct names!
        If progress effect, value must be specified
        :param mode_name: string of mode name
        :param value: percentage of how far through it is. None
        """
        if self.return_timer is not None and self.return_timer.is_alive():
            self.return_timer.cancel()

        if mode_name != 'torch' and self.torch_on:
            self.torch_on = False

        if mode_name in ['on', 'off']:
            self.effect_queue.put(mode_name)
            return
        elif mode_name == 'M150':
            if m150:
                self.effect_queue.put(m150)
            else:
                self._logger.warning("No values supplied with M150, ignoring")
            return

        if not self.SETTINGS[mode_name]['enabled']:  # If the effect is not enabled, we won't run it. Simple...
            return

        if 'success' in mode_name:
            return_idle_time = self._settings.get_int(['success_return_idle'])
            if return_idle_time > 0:
                self.return_timer = threading.Timer(return_idle_time, self.return_to_idle)
                self.return_timer.daemon = True
                self.return_timer.start()

        if 'progress' in mode_name:
            if not value:
                self._logger.warning("No value supplied with progress style effect, ignoring")
                return
            self._logger.debug("Updating progress effect {}, value {}".format(mode_name, value))
            # Do the thing
            self.effect_queue.put('{} {}'.format(mode_name, value))
            self.current_state = '{} {}'.format(mode_name, value)
        else:
            self._logger.debug("Updating standard effect {}".format(mode_name))
            # Do the thing
            self.effect_queue.put(mode_name)
            if mode_name != 'torch':
                self.current_state = mode_name

    def return_to_idle(self):
        self.update_effect('idle')

    def on_event(self, event, payload):
        try:
            if event == 'PrintDone':
                self.cooling = True

            if (self.heating and self._settings.get_boolean(["progress_heatup_enabled"])) \
                    or (self.cooling and self._settings.get_boolean(["progress_cooling_enabled"])):
                # We want to hold back effects while we are heating/cooling tracking (unless they are disabled)
                self.add_to_backlog(event)
            else:
                self.update_effect(self.supported_events[event])
        except KeyError:  # The event isn't supported
            pass

    def on_print_progress(self, storage, path, progress):
        if (progress == 100 and self.current_state == 'success') or self.heating:
            return
        if self._settings.get_boolean(['printing_enabled']):
            self.update_effect('printing')
        self.update_effect('progress_print', progress)

    def calculate_heatup_progress(self, current, target):
        if target <= 0:
            self._logger.warning("Tried to calculate heating progress but target was zero")
            self._logger.warning("If you come across this please let me know on the issue tracker! - "
                                 "https://github.com/cp2004/OctoPrint-WS281x_LED_Status")
            return 0
        return round((current / target) * 100)

    def process_previous_event_q(self):
        """
        Runs the last event again, to put it back in the case of heating or cooling finishing, then clears the backlog.
        :return: None
        """
        self.on_event(self.previous_event_q[-1], payload={})
        self.previous_event_q = []

    def add_to_backlog(self, event):
        self.previous_event_q.append(event)

    def process_gcode_q(self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):
        if gcode in BLOCKING_TEMP_GCODES:
            bed_or_tool = {
                'M109': "tool",
                'M190': "bed"
            }
            # Everything is tracked, regardless of settings. Makes it easier to track the state, and then just back out
            # of showing the effect in self.update_effect() rather than getting complex here.
            self.heating = True
            self.current_heater_heating = bed_or_tool[gcode]
        else:
            if self.heating:  # State is switching to non-heating, so we should process the backlog.
                self.heating = False
                self.process_previous_event_q()

        if gcode == 'M150' and self._settings.get_boolean(['intercept_m150']):
            self.update_effect('M150', m150=cmd)
            return None,

    def temperatures_received(self, comm_instance, parsed_temperatures, *args, **kwargs):
        try:
            tool_temp_target = parsed_temperatures['T{}'.format(
                self._settings.get_int(['progress_heatup_tool_key']))][1]
        except KeyError:
            tool_temp_target = self.target_temperature["tool"]

        if not tool_temp_target:  # When heating, firmware reports more frequently but *without* target
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
            "tool": tool_temp_target if tool_temp_target > 0 else self.target_temperature["tool"],
            "bed": bed_temp_target if bed_temp_target > 0 else self.target_temperature["bed"]
        }
        words_to_tool = {  # maps 'progress_cooling_bed_or_tool' to the parsed temp
            "tool": "T{}".format(self.tool_to_target),
            "bed": "B"
        }
        if self.heating:
            try:
                current_temp = parsed_temperatures[words_to_tool[self.current_heater_heating]][0]
            except KeyError:
                self._logger.error(
                    "Heater {} not found, can't show progress. Check configuration".format(self.current_heater_heating))
                self.heating = False
                self.process_previous_event_q()
                return

            self._logger.debug("State: heating, temp recv: {}".format(current_temp))
            if self.target_temperature[self.current_heater_heating] > 0:
                self.update_effect('progress_heatup', self.calculate_heatup_progress(
                    current_temp,
                    self.target_temperature[self.current_heater_heating]
                ))

        elif self.cooling:
            if self._printer.is_printing() or self._printer.is_paused():
                # User has likely started a new print - we can clear the queue, and carry on.
                self.previous_event_q = []
                self.cooling = False
                return

            current = parsed_temperatures[words_to_tool[self._settings.get(['progress_cooling_bed_or_tool'])]][0]
            self._logger.debug("State: cooling, temp recv: {}".format(current))

            if current < self._settings.get_int(['progress_cooling_threshold']):
                self.cooling = False
                self.process_previous_event_q()  # should hopefully put back the old effect (maybe progress)
                return
            self.update_effect('progress_cooling', self.calculate_heatup_progress(
                current,
                self.target_temperature[self._settings.get(['progress_cooling_bed_or_tool'])]
            ))

        return parsed_temperatures

    def process_at_command(self, comm, phase, command, parameters, tags=None, *args, **kwargs):
        if command not in AT_COMMANDS or not self._settings.get(['at_command_reaction']):
            return

        if command == ON_AT_COMMAND:
            self._logger.debug("Recieved gcode @ command for lights on")
            self.lights_on = True
            self.update_effect('on')
        elif command == OFF_AT_COMMAND:
            self._logger.debug("Recieved gcode @ command for lights off")
            self.lights_on = False
            self.update_effect('off')
        elif command == TORCH_AT_COMMAND:
            self._logger.debug("Recieved gcode @ command for torch")
            self.activate_torch()

    # Softwareupdate hook
    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return dict(
            ws281x_led_status=dict(
                displayName="WS281x LED Status",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="cp2004",
                repo="OctoPrint-WS281x_LED_Status",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/cp2004/OctoPrint-WS281x_LED_Status/archive/{target_version}.zip"
            )
        )


__plugin_name__ = "WS281x LED Status"
__plugin_pythoncompat__ = ">=2.7,<4"  # python 2 and 3


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = WS281xLedStatusPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.process_gcode_q,
        "octoprint.comm.protocol.temperatures.received": __plugin_implementation__.temperatures_received,
        "octoprint.comm.protocol.atcommand.sending": __plugin_implementation__.process_at_command
    }
