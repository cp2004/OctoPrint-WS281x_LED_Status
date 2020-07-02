# coding=utf-8
from __future__ import absolute_import, unicode_literals

from threading import Thread
from queue import Queue

from rpi_ws281x import PixelStrip  # May not be needed
import octoprint.plugin

from effect_runner import STRIP_TYPES, effect_runner
from effects import basic, progress


class RgbLedStatusPlugin(octoprint.plugin.SettingsPlugin,
                         octoprint.plugin.TemplatePlugin,
                         octoprint.plugin.WizardPlugin,
                         octoprint.plugin.ProgressPlugin,
                         octoprint.plugin.EventHandlerPlugin,
                         octoprint.RestartNeedingPlugin):

    current_effect_thread = None  # thread object
    current_state = None
    effect_queue = Queue()  # pass name of effects

    MODES = {  # Empty untill filled by
        'startup': None,
        'idle': None,
        'progress': None
    }

    def __init__(self):
        

    def init_effect_thread(self, settings):
        # Start effect runner here
        pass

    def stop_effect_thread(self, settings):
        """
        Stop the runnner
        As this can potentially hang the server for a fraction of the second it is not called often.
        """
        if self.current_effect_thread is not None:
            self.effect_queue.put("KILL")
            self.current_effect_thread.join()

    def update_effect(self, effect_name)

    # SettingsPlugin mixin
    def get_settings_defaults(self):
        return dict(
            led_count=24,
            led_pin=10,
            led_freq_hz=800000,
            led_dma=10,
            led_invert=False,
            led_brightness=255,  # Maybe convert to percentage?
            led_channel=0,
            strip_type='WS2811_STRIP_GRB',

            startup_effect='wipe',
            startup_color='#00ff00',
            startup_delay='10',

            idle_effect='solid',
            idle_color='#0000ff',
            idle_delay='10',

            progress_enabled=True,
            progress_colour_base='#000000'
            progress_colour_bar='#00ff00'
        )

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
__plugin_name__ = "Rgb_led_status Plugin"

# Starting with OctoPrint 1.4.0 OctoPrint will also support to run under Python 3 in addition to the deprecated
# Python 2. New plugins should make sure to run under both versions for now. Uncomment one of the following
# compatibility flags according to what Python versions your plugin supports!
#__plugin_pythoncompat__ = ">=2.7,<3" # only python 2
#__plugin_pythoncompat__ = ">=3,<4" # only python 3
__plugin_pythoncompat__ = ">=2.7,<4" # python 2 and 3


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = RgbLedStatusPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }

