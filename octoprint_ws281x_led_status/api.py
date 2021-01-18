# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

__author__ = "Charlie Powell <cp2004.github@gmail.com"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Charlie Powell 2020-2021 - released under the terms of the AGPLv3 License"

# noinspection PyPackageRequirements
from flask import jsonify

from octoprint_ws281x_led_status import util

# Define API commands
CMD_LIGHTS_ON = "lights_on"
CMD_LIGHTS_OFF = "lights_off"
CMD_TORCH_ON = "torch_on"
CMD_TORCH_OFF = "torch_off"
CMD_TEST_OS = "test_os_config"
CMD_TEST_LED = "test_led"
WIZ_ADDUSER = "wiz_adduser"
WIZ_ENABLE_SPI = "wiz_enable_spi"
WIZ_INCREASE_BUFFER = "wiz_increase_buffer"
WIZ_SET_CORE_FREQ = "wiz_set_core_freq"
WIZ_SET_FREQ_MIN = "wiz_set_core_freq_min"


class PluginApi:
    def __init__(self, plugin):
        self.plugin = plugin

    @staticmethod
    def get_api_commands():
        return {
            CMD_LIGHTS_ON: [],
            CMD_LIGHTS_OFF: [],
            CMD_TORCH_ON: [],
            CMD_TORCH_OFF: [],
            CMD_TEST_OS: [],
            CMD_TEST_LED: ["red", "green", "blue"],
            WIZ_ADDUSER: ["password"],
            WIZ_ENABLE_SPI: ["password"],
            WIZ_INCREASE_BUFFER: ["password"],
            WIZ_SET_CORE_FREQ: ["password"],
            WIZ_SET_FREQ_MIN: ["password"],
        }

    def on_api_command(self, command, data):
        if command == CMD_LIGHTS_ON:
            self.plugin.activate_lights()
        elif command == CMD_LIGHTS_OFF:
            self.plugin.deactivate_lights()
        elif command == CMD_TORCH_ON:
            self.plugin.activate_torch()
        elif command == CMD_TORCH_OFF:
            self.plugin.deactivate_torch()
        elif command == CMD_TEST_OS:
            self.start_os_config_test()
        elif command == CMD_TEST_LED:
            self.test_led(data)
        elif command.startswith("wiz"):
            # Pass to wizard command handler
            return self.plugin.wizard.on_api_command(command, data)

        return self.on_api_get()

    def on_api_get(self, **kwargs):
        response = {
            "lights_on": self.plugin.lights_on,
            "torch_on": self.plugin.torch_on,
        }
        return jsonify(response)

    def start_os_config_test(self):
        util.start_daemon_thread(
            target=self.plugin.run_os_config_check,
            name="WS281x LED Status OS Config Test",
        )

    def test_led(self, data):
        # We mock an M150 command here, because it is the easiest way
        # Calling update_effect skips the checking of M150 intercepting or the printer
        self.plugin.update_effect(
            "M150 R{} G{} B{}".format(
                data.get("red"), data.get("green"), data.get("blue")
            )
        )
