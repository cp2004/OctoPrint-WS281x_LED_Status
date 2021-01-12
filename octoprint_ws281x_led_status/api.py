# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

import threading

# noinspection PyPackageRequirements
from flask import jsonify

# Define API commands
CMD_LIGHTS_ON = "lights_on"
CMD_LIGHTS_OFF = "lights_off"
CMD_TORCH_ON = "torch_on"
CMD_TORCH_OFF = "torch_off"
CMD_TEST_OS = "test_os_config"
WIZ_ADDUSER = "wiz_adduser"
WIZ_ENABLE_SPI = "wiz_enable_spi"
WIZ_INCREASE_BUFFER = "wiz_increase_buffer"
WIZ_SET_CORE_FREQ = "wiz_set_core_freq"
WIZ_SET_FREQ_MIN = "wiz_set_core_freq_min"


class PluginApi:
    def __init__(self, plugin):
        self.plugin = plugin
        # noinspection PyProtectedMember
        self._settings = plugin._settings

    @staticmethod
    def get_api_commands():
        return {
            CMD_LIGHTS_ON: [],
            CMD_LIGHTS_OFF: [],
            CMD_TORCH_ON: [],
            CMD_TORCH_OFF: [],
            CMD_TEST_OS: [],
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
        elif command.startswith("wiz"):
            # Pass to wizard command handler
            return self.plugin.wizard.on_api_command(
                command, data, self.plugin.PI_MODEL
            )

        return self.on_api_get()

    def on_api_get(self, **kwargs):
        response = {
            "lights_on": self.plugin.get_lights_status(),
            "torch_on": self.plugin.get_torch_status(),
        }
        return jsonify(response)

    def start_os_config_test(self):
        thread = threading.Thread(
            target=self.plugin.run_os_config_check, name="WS281x OS Config Test"
        )
        thread.daemon = True
        thread.start()
        return
