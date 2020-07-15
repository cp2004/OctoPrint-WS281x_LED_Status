# coding=utf-8
from __future__ import absolute_import, unicode_literals
from multiprocessing import get_context
import re
import io
import subprocess

import octoprint.plugin

from octoprint_ws281x_led_status.effect_runner import STRIP_TYPES, STRIP_SETTINGS, EFFECTS, MODES, effect_runner
from octoprint_ws281x_led_status.effects import basic, progress
MP_CONTEXT = get_context('fork')
PI_REGEX = r"(?<=Raspberry Pi)(.*)(?=Model)"
_PROC_DT_MODEL_PATH = "/proc/device-tree/model"
BLOCKING_TEMP_GCODES = ["M109", "M190"]

STANDARD_EFFECT_NICE_NAMES = {
    'Solid Color': 'solid',
    'Color Wipe': 'wipe',
    'Color Wipe 2': 'wipe2',
    'Pulse': 'pulse',
    'Bounce': 'bounce',
    'Rainbow': 'rainbow',
    'Rainbow Cycle': 'cycle'
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
    current_state = None  # Idle, startup, progress etc. Used to put the old effect back on settings change/light switch
    effect_queue = MP_CONTEXT.Queue()  # pass name of effects here

    SETTINGS = {}  # Filled in on startup
    PI_MODEL = None  # Filled in on startup

    heating = False   # True when heating is detected, options below are helpers for tracking heatup.
    temp_target = 0
    current_heater_heating = None
    tool_to_target = 0  # Overridden by the plugin settings

    # Asset plugin
    def get_assets(self):
        return dict(
            js=['js/ws281x_led_status.js']
        )

    # Startup plugin
    def on_startup(self, host, port):
        self.PI_MODEL = self.determine_pi_version()

    def on_after_startup(self):
        self.refresh_settings()
        self.start_effect_process()

    # Shutdown plugin
    def on_shutdown(self):
        self._logger.info("RGB LED Status runner stopped")
        if self.current_effect_process is not None:
            self.effect_queue.put("KILL")
            self.current_effect_process.join()

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

            paused_enabled=True,
            paused_effect='Bounce',
            paused_color='#0000ff',
            paused_delay='40',

            progress_print_enabled=True,
            progress_print_color_base='#000000',
            progress_print_color='#00ff00',

            progress_heatup_enabled=True,
            progress_heatup_color_base='#0000ff',
            progress_heatup_color='#ff0000',
            progress_heatup_tool_enabled=True,
            progress_heatup_bed_enabled=True,
            progress_heatup_tool_key=0,

            active_hours_enabled=False,
            active_hours_start="09:00",
            active_hours_stop="21:00"
        )

    # Template plugin
    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]

    def get_template_vars(self):
        return {'standard_names': STANDARD_EFFECT_NICE_NAMES, 'pi_model': self.PI_MODEL, 'strip_types': STRIP_TYPES}

    # Wizard plugin bits
    def is_wizard_required(self):
        for item in self.get_wizard_details().values():
            if not item:
                return True
        return False

    def get_wizard_details(self):
        return dict(
            adduser_done=self.is_adduser_done(),
            spi_enabled=self.is_spi_enabled(),
            spi_buffer_increase=self.is_spi_buffer_increased(),
            core_freq_set=self.is_core_freq_set(),
            core_freq_min_set=self.is_core_freq_min_set()
        )

    def get_wizard_version(self):
        return 1

    def on_wizard_finish(self, handled):
        self._logger.info("You will need to restart your Pi for the changes to take effect")
        # TODO make this a popup? not very useful here

    # Simple API plugin
    def get_api_commands(self):
        return dict(
            adduser=['password'],
            enable_spi=['password'],
            spi_buffer_increase=['password'],
            set_core_freq=['password'],
            set_core_freq_min=['password']
        )

    def on_api_command(self, command, data):
        api_to_command = {
            # -S for sudo commands means accept password from stdin, see https://www.sudo.ws/man/1.8.13/sudo.man.html#S
            'adduser': ['sudo', '-S', 'adduser', 'pi', 'gpio'],
            'enable_spi': ['sudo', '-S', 'bash', '-c', 'echo \'dtparam=spi=on\' >> /boot/config.txt'],
            'set_core_freq': ['sudo', '-S', 'bash', '-c',
                              'echo \'core_freq=500\' >> /boot/config.txt' if self.PI_MODEL == '4' else 'echo \'core_freq=250\' >> /boot/config.txt'],
            'set_core_freq_min': ['sudo', '-S', 'bash', '-c', 'echo \'core_freq_min=500\' >> /boot/config.txt' if self.PI_MODEL == '4' else 'echo \'core_freq_min=250\' >> /boot/config.txt'],
            'spi_buffer_increase': ['sudo', '-S', 'sed', '-i', '$ s/$/ spidev.bufsiz=32768/', '/boot/cmdline.txt']
        }
        api_command_validator = {
            'adduser' : self.is_adduser_done,
            'enable_spi': self.is_spi_enabled,
            'set_core_freq': self.is_core_freq_set,
            'set_core_freq_min': self.is_core_freq_min_set,
            'spi_buffer_increase': self.is_spi_buffer_increased
        }
        if not api_command_validator[command]():
            stdout, error = self.run_system_command(api_to_command[command], data.get('password'))
        else:
            error = None
        return self.api_cmd_response(error)

    def api_cmd_response(self, errors=None):
        from flask import jsonify
        details = self.get_wizard_details()
        details.update(errors=errors)
        return jsonify(details)

    def run_system_command(self, command, password=None):
        if password and password != 'raspberry':
            self._logger.error("Incorrect password")
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        if password:
            stdout, stderr = process.communicate('{}\n'.format(password).encode())
        else:
            stdout, stderr = process.communicate()

        if stderr and 'Sorry' in stderr.decode('utf-8') or 'no password' in stderr.decode('utf-8'):  # .decode for Python 2/3 compatibility, make sure utf-8
            self._logger.error("Running command for {}, but password incorrect".format(command))
            return stdout.decode('utf-8'), 'password'
        else:
            return stdout.decode('utf-8'), None

    def is_adduser_done(self):
        groups, error = self.run_system_command(['groups', 'pi'])
        return 'gpio' in groups

    def is_spi_enabled(self):
        with io.open('/boot/config.txt') as file:
            for line in file:
                if line.startswith('dtparam=spi=on'):
                    return True
        return False

    def is_spi_buffer_increased(self):
        with io.open('/boot/cmdline.txt') as file:
            for line in file:
                if 'spidev.bufsiz=32768' in line:
                    return True
        return False

    def is_core_freq_set(self):
        if self.PI_MODEL == '4':  # Pi 4's default is 500, which is compatible with SPI.
            return True           # any change to core_freq is ignored on a Pi 4, so let's not bother.
        with io.open('/boot/config.txt') as file:
            for line in file:
                if line.startswith('core_freq=250'):
                    return True
        return False

    def is_core_freq_min_set(self):
        if int(self.PI_MODEL) == 4:                    # Pi 4 has a variable clock speed, which messes up SPI timing
            with io.open('/boot/config.txt') as file:  # This is only required on pi 4, not other models.
                for line in file:
                    if line.startswith('core_freq_min=500'):
                        return True
            return False
        else:
            return True

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

        self.SETTINGS['active_start'] = self._settings.get(['active_hours_start']) if self._settings.get(['active_hours_enabled']) else None
        self.SETTINGS['active_stop'] = self._settings.get(['active_hours_stop']) if self._settings.get(['active_hours_enabled']) else None


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
        self.current_effect_process = MP_CONTEXT.Process(
            target=effect_runner,
            name="RGB LED Status Effect Process",
            args=(self._logger, self.effect_queue, self.SETTINGS, self.current_state),
            daemon=True)
        self.current_effect_process.start()
        self._logger.info("RGB LED Status runner started")

    def stop_effect_process(self):
        """
        Stop the runner
        As this can potentially hang the server for a fraction of a second while the final frame of the effect runs,
        it is not called often - only on update of settings & shutdown.
        """
        if self.current_effect_process is not None:
            self.effect_queue.put("KILL")
            self.current_effect_process.join()
        self._logger.info("RGB LED Status runner stopped")

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
        try:
            self.update_effect(self.supported_events[event])
        except KeyError:  # The event isn't supported
            pass

    def on_print_progress(self, storage, path, progress):
        if (progress == 100 and self.current_state == 'success') or self.heating:
            return
        self.update_effect('progress_print', progress)
        self._logger.info("Updating print progress to {}".format(progress))

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
                self.update_effect('progress_heatup', self.calculate_heatup_progress(current_temp, self.temp_target))
        return parsed_temperatures

    # Softwareupdate hook
    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return dict(
            rgb_led_status=dict(
                displayName="RGB LED Status",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="cp2004",
                repo="OctoPrint-RGB_LED_Status",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/cp2004/OctoPrint-WS281x_LED_Status/archive/{target_version}.zip"
            )
        )


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "WS281x LED Status"

# Starting with OctoPrint 1.4.0 OctoPrint will also support to run under Python 3 in addition to the deprecated
# Python 2. New plugins should make sure to run under both versions for now. Uncomment one of the following
# compatibility flags according to what Python versions your plugin supports!
# __plugin_pythoncompat__ = ">=2.7,<3" # only python 2
__plugin_pythoncompat__ = ">=3,<4" # only python 3
# __plugin_pythoncompat__ = ">=2.7,<4" # python 2 and 3


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = WS281xLedStatusPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.queued": __plugin_implementation__.look_for_temperature,
        "octoprint.comm.protocol.temperatures.received": __plugin_implementation__.temperatures_received
    }

