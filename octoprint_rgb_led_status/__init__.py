# coding=utf-8
from __future__ import absolute_import, unicode_literals
from threading import Thread
import re
import io
import os
try:
    from queue import Queue  # In Python 3 the module has been renamed to queue
except ImportError:
    from Queue import Queue  # Python 2 queue

import octoprint.plugin

from octoprint_rgb_led_status.effect_runner import STRIP_TYPES, STRIP_SETTINGS, EFFECTS, effect_runner
from octoprint_rgb_led_status.effects import basic, progress


MODES = ['startup', 'idle', 'progress_print']  # Possible modes that can happen
PI_REGEX = r"(?<=Raspberry Pi)(.*)(?=Model)"
_PROC_DT_MODEL_PATH = "/proc/device-tree/model"

class RgbLedStatusPlugin(octoprint.plugin.StartupPlugin,
                         octoprint.plugin.ShutdownPlugin,
                         octoprint.plugin.SettingsPlugin,
                         octoprint.plugin.TemplatePlugin,
                         octoprint.plugin.WizardPlugin,
                         octoprint.plugin.ProgressPlugin,
                         octoprint.plugin.EventHandlerPlugin,
                         octoprint.plugin.RestartNeedingPlugin):

    current_effect_thread = None  # thread object
    current_state = None  # Idle, startup, progress etc.
    effect_queue = Queue()  # pass name of effects here

    SETTINGS = {}  # Filled in on startup
    PI_MODEL = None

    # Startup plugin
    def on_after_startup(self):
        self.PI_MODEL = self.determine_pi_version()
        self.refresh_settings()
        self.start_effect_thread()

    # Shutdown plugin
    def on_shutdown(self):
        self.update_effect("shutdown")
        self.stop_effect_thread()

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
            startup_effect='wipe',
            startup_color='#00ff00',
            startup_delay='10',

            idle_enabled=True,
            idle_effect='solid',
            idle_color='#0000ff',
            idle_delay='10',

            progress_enabled=True,
            progress_colour_base='#000000',
            progress_colour_bar='#00ff00'
        )

    # Template plugin
    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]

    def get_template_vars(self):
        return {'effects': EFFECTS, 'strip_types': STRIP_TYPES}

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
        self.SETTINGS['strip'] = {}
        for setting in STRIP_SETTINGS:
            if setting == 'led_invert':  # Boolean settings
                self.SETTINGS['strip'][setting] = self._settings.get_boolean([setting])
            elif setting == 'strip_type':  # String settings
                self.SETTINGS['strip']['strip_type'] = self._settings.get([setting])
            elif setting == 'led_brightness':  # Percentage
                self.SETTINGS['strip']['led_brightness'] = int(round((self._settings.get_int([setting]) / 100) * 255))
            else:  # Integer settings
                self.SETTINGS['strip'][setting] = self._settings.get_int([setting])

        for mode in MODES:
            mode_settings = {'enabled': self._settings.get_boolean(['{}_enabled'.format(mode)]),
                             'effect': self._settings.get(['{}_effect'.format(mode)]),
                             'color': self._settings.get(['{}_color'.format(mode)])}
            if 'progress' in mode:  # Unsure
                mode_settings['base'] = self._settings.get(['{}_base'.format(mode)])
            else:
                mode_settings['delay'] = self._settings.get_int(['{}_delay'.format(mode)])
            self.SETTINGS[mode] = mode_settings

        self._logger.info("Settings refreshed")

    def restart_strip(self):
        self.stop_effect_thread()
        self.start_effect_thread()

    def start_effect_thread(self):
        # Start effect runner here
        self.current_effect_thread = Thread(target=effect_runner, args=(self._logger, self.effect_queue, self.SETTINGS,), name="RGB LED Status runner")
        self.current_effect_thread.start()
        self._logger.info("RGB LED Status runner started")

    def stop_effect_thread(self):
        """
        Stop the runnner
        As this can potentially hang the server for a fraction of a second while the final frame of the effect runs,
        it is not called often - only on update of settings & shutdown.
        """
        self._logger.info("RGB LED Status runner stopped")
        if self.current_effect_thread is not None:
            self.effect_queue.put("KILL")
            self.current_effect_thread.join()

    def update_effect(self, mode_name):
        if progress not in mode_name:
            self.effect_queue.put(mode_name)
        else:
            pass

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
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }

