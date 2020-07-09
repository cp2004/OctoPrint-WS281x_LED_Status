# coding=utf-8
from __future__ import absolute_import, unicode_literals
from multiprocessing import get_context
import re
import io

import octoprint.plugin

from octoprint_rgb_led_status.effect_runner import STRIP_TYPES, STRIP_SETTINGS, EFFECTS, MODES, effect_runner
from octoprint_rgb_led_status.effects import basic, progress
# TODO Add setup wizard
MP_CONTEXT = get_context('fork')
PI_REGEX = r"(?<=Raspberry Pi)(.*)(?=Model)"
_PROC_DT_MODEL_PATH = "/proc/device-tree/model"
BLOCKING_TEMP_GCODES = ["M109","M190"]

STANDARD_EFFECT_NICE_NAMES = {
    'Color Wipe': 'wipe',
    'Solid Color': 'solid'
}


class RgbLedStatusPlugin(octoprint.plugin.StartupPlugin,
                         octoprint.plugin.ShutdownPlugin,
                         octoprint.plugin.SettingsPlugin,
                         octoprint.plugin.TemplatePlugin,
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
    current_effect_thread = None  # thread object
    current_state = None  # Idle, startup, progress etc. Used to put the old effect back on settings change
    effect_queue = MP_CONTEXT.Queue()  # pass name of effects here

    SETTINGS = {}  # Filled in on startup
    PI_MODEL = None

    heating = False
    temp_target = 0
    current_heater_heating = None
    tool_to_target = 0

    # Startup plugin
    def on_after_startup(self):
        self.PI_MODEL = self.determine_pi_version()  # Needed for the wizard...
        self.refresh_settings()
        self.start_effect_process()

    # Shutdown plugin
    def on_shutdown(self):
        self._logger.info("RGB LED Status runner stopped")
        if self.current_effect_thread is not None:
            self.effect_queue.put("KILL")
            self.current_effect_thread.join()

    # Settings plugin
    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self.refresh_settings()
        self.restart_strip()

    def get_settings_defaults(self):
        return dict(
            led_count=24,
            led_pin=10,
            led_freq_hz=800000,
            led_dma=10,
            led_invert=False,
            led_brightness=100,  # Maybe convert to percentage?
            led_channel=0,
            strip_type='WS2811_STRIP_GRB',

            startup_enabled=True,
            startup_effect='Color Wipe',
            startup_color='#00ff00',
            startup_delay='10',

            idle_enabled=True,
            idle_effect='Solid Color',
            idle_color='#0000ff',
            idle_delay='10',

            disconnected_enabled=True,
            disconnected_effect='Solid Color',
            disconnected_color='#ff0000',
            disconnected_delay='10',

            failed_enabled=True,
            failed_effect='Solid Color',
            failed_color='#0f0f00',
            failed_delay='10',

            success_enabled=True,
            success_effect='Solid Color',
            success_color='#00f0f0',
            success_delay='10',

            paused_enabled=True,
            paused_effect='Solid Color',
            paused_color='#0f0f0a',
            paused_delay='10',

            progress_print_enabled=True,
            progress_print_color_base='#000000',
            progress_print_color='#00ff00',

            progress_heatup_enabled=True,
            progress_heatup_color_base='#0000ff',
            progress_heatup_color='#ff0000',
            progress_heatup_tool_enabled=True,
            progress_heatup_bed_enabled=True,
            progress_heatup_tool_key=0
        )

    # Template plugin
    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]

    def get_template_vars(self):
        return {'standard_names': STANDARD_EFFECT_NICE_NAMES, 'effects': EFFECTS, 'strip_types': STRIP_TYPES}

    # Wizard plugin bits

    # My methods
    def determine_pi_version(self):
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

        self.SETTINGS['strip'] = {}
        for setting in STRIP_SETTINGS:
            if setting == 'led_invert':  # Boolean settings
                self.SETTINGS['strip'][setting] = self._settings.get_boolean([setting])
            elif setting == 'strip_type':  # String settings
                self.SETTINGS['strip']['strip_type'] = self._settings.get([setting])
            elif setting == 'led_brightness':  # Percentage
                self.SETTINGS['strip']['led_brightness'] = min(int(round((self._settings.get_int([setting]) / 100) * 255)), 255)
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
                mode_settings['delay'] = self._settings.get_int(['{}_delay'.format(mode)])
            self.SETTINGS[mode] = mode_settings

        self._logger.info("Settings refreshed")

    def restart_strip(self):
        self.stop_effect_process()
        self.start_effect_process()

    def start_effect_process(self):
        # Start effect runner here
        self.current_effect_thread = MP_CONTEXT.Process(
            target=effect_runner,
            name="RGB LED Status Effect Process",
            args=(self._logger, self.effect_queue, self.SETTINGS, self.current_state),
            daemon=True)
        self.current_effect_thread.start()
        self._logger.info("RGB LED Status runner started")

    def stop_effect_process(self):
        """
        Stop the runner
        As this can potentially hang the server for a fraction of a second while the final frame of the effect runs,
        it is not called often - only on update of settings & shutdown.
        """
        self._logger.info("RGB LED Status runner stopped")
        if self.current_effect_thread is not None:
            self.effect_queue.put("KILL")
            self.current_effect_thread.join()

    def update_effect(self, mode_name, value=None):
        """
        Change the effect displayed, using effect.EFFECTS for the correct names!
        If progress effect, value must be specified
        :param mode_name: string of mode name
        :param value: percentage of how far through it is. None
        """
        if not self.SETTINGS[mode_name]['enabled']:  # If the effect is not enabled, we won't run it. Simple
            return

        if 'progress' in mode_name:
            if not value:
                self._logger.warning("No value supplied with progress style effect, ignoring")
                return
            self._logger.debug("Updating progress effect {}, value {}".format(mode_name, value))
            # Do the thing
            self.effect_queue.put('{} {}'.format(mode_name, value))
        else:
            self._logger.debug("Updating standard effect {}".format(mode_name))
            # Do the thing
            self.effect_queue.put(mode_name)
            self.current_state = mode_name

    def on_event(self, event, payload):
        self.on_standard_event_handler(event)

    def on_print_progress(self, storage, path, progress):
        if (progress == 100 and self.current_state == 'success') or self.heating:
            return
        self.on_progress_event_handler('progress_print', progress)
        self._logger.info("Updating print progress to {}".format(progress))

    def on_standard_event_handler(self, event):  # TODO 'event handler' functions are unnecessary!
        try:
            self.update_effect(self.supported_events[event])
        except KeyError:
            pass

    def on_progress_event_handler(self, event, value):
        self.update_effect(event, value)

    def calculate_heatup_progress(self, current, target):
        return round((current / target) * 100)

    def look_for_temperature(self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):
        bed_or_tool = {
            'M109': 'T{}'.format(self.tool_to_target) if self._settings.get_boolean(['progress_heatup_tool_enabled']) else None,
            'M190': 'B' if self._settings.get_boolean(['progress_heatup_bed_enabled']) else None
        }
        if (gcode in BLOCKING_TEMP_GCODES) and bed_or_tool[gcode]:
            self.heating = True
            self.current_heater_heating = bed_or_tool[gcode]
        else:
            self.heating = False

        return

    def temperatures_received(self, comm_instance, parsed_temperatures, *args, **kwargs):
        if self.heating and self.current_heater_heating:
            try:
                current_temp, target_temp = parsed_temperatures[self.current_heater_heating]
            except KeyError:
                self._logger.error("Could not find temperature of tool T{}, not able to show heatup progress.".format(self.current_heater_heating))
                self.heating = False
                return
            if target_temp:  # Sometimes we don't get everything, so to update more frequently we'll store the target
                self.temp_target = target_temp
            if self.temp_target > 0:  # Prevent ZeroDivisionError, or showing progress when target is zero
                self.on_progress_event_handler('progress_heatup', self.calculate_heatup_progress(current_temp, self.temp_target))
        return parsed_temperatures

    # Softwareupdate hook
    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return dict(
            rgb_led_status=dict(
                displayName="Rgb_led_status Plugin",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="cp2004",
                repo="OctoPrint-RGB_LED_Status",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/cp2004/OctoPrint-RGB_LED_Status/archive/{target_version}.zip"
            )
        )


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "RGB LED Status"

# Starting with OctoPrint 1.4.0 OctoPrint will also support to run under Python 3 in addition to the deprecated
# Python 2. New plugins should make sure to run under both versions for now. Uncomment one of the following
# compatibility flags according to what Python versions your plugin supports!
# __plugin_pythoncompat__ = ">=2.7,<3" # only python 2
# __plugin_pythoncompat__ = ">=3,<4" # only python 3
__plugin_pythoncompat__ = ">=2.7,<4" # python 2 and 3


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = RgbLedStatusPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.queued": __plugin_implementation__.look_for_temperature,
        "octoprint.comm.protocol.temperatures.received": __plugin_implementation__.temperatures_received
    }

