# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

import io
import logging

# noinspection PyPackageRequirements
from flask import jsonify

from octoprint_ws281x_led_status import api
from octoprint_ws281x_led_status.util import run_system_command


class PluginWizard:
    def __init__(self, plugin, pi_model):
        self.plugin = plugin
        self._logger = logging.getLogger("octoprint.plugins.ws281x_led_status.wizard")

        self.pi_model = pi_model

    def on_api_command(self, cmd, data):
        # Wizard specific API
        if not cmd.startswith("wiz"):
            return

        if self.pi_model is None:
            self._logger.error("Tried to run wizard command without Pi model, aborting")
            # TODO return error?
            return

        if not self.validate(cmd):
            self.run_wizard_command(cmd, data)

        return self.on_api_get()

    def on_api_get(self, **kwargs):
        # Wizard specific API
        return {
            "adduser_done": self.validate(api.WIZ_ADDUSER),
            "spi_enabled": self.validate(api.WIZ_ENABLE_SPI),
            "spi_buffer_increase": self.validate(api.WIZ_INCREASE_BUFFER),
            "core_freq_set": self.validate(api.WIZ_SET_CORE_FREQ),
            "core_freq_min_set": self.validate(api.WIZ_SET_FREQ_MIN),
        }

    def validate(self, cmd):
        validators = {
            api.WIZ_ADDUSER: self.is_adduser_done,
            api.WIZ_ENABLE_SPI: self.is_spi_enabled,
            api.WIZ_INCREASE_BUFFER: self.is_spi_buffer_increased,
            api.WIZ_SET_CORE_FREQ: self.is_core_freq_set,
            api.WIZ_SET_FREQ_MIN: self.is_core_freq_min_set,
        }
        return validators[cmd]()

    @staticmethod
    def is_adduser_done():
        groups, error = run_system_command(["groups", "pi"])
        return "gpio" in groups

    @staticmethod
    def is_spi_enabled():
        with io.open("/boot/config.txt") as file:
            for line in file:
                if line.startswith("dtparam=spi=on"):
                    return True
        return False

    @staticmethod
    def is_spi_buffer_increased():
        with io.open("/boot/cmdline.txt") as file:
            for line in file:
                if "spidev.bufsiz=32768" in line:
                    return True
        return False

    def is_core_freq_set(self):
        if self.pi_model == "4":  # Pi 4's default is 500, which is compatible with SPI.
            return True
            # any change to core_freq is ignored on a Pi 4, so let's not bother.
        with io.open("/boot/config.txt") as file:
            for line in file:
                if line.startswith("core_freq=250"):
                    return True
        return False

    def is_core_freq_min_set(self):
        if self.pi_model == "4":
            # Pi 4 has a variable clock speed, which messes up SPI timing
            with io.open("/boot/config.txt") as file:
                for line in file:
                    if line.startswith("core_freq_min=500"):
                        return True
            return False
        else:
            return True

    def run_wizard_command(self, cmd, data):
        command_to_system = {
            # -S for sudo commands means accept password from stdin, see https://www.sudo.ws/man/1.8.13/sudo.man.html#S
            api.WIZ_ADDUSER: ["sudo", "-S", "adduser", "pi", "gpio"],
            api.WIZ_ENABLE_SPI: [
                "sudo",
                "-S",
                "bash",
                "-c",
                "echo 'dtparam=spi=on' >> /boot/config.txt",
            ],
            api.WIZ_SET_CORE_FREQ: [
                "sudo",
                "-S",
                "bash",
                "-c",
                "echo 'core_freq=250' >> /boot/config.txt"
                if self.pi_model != "4"
                else "",
            ],
            api.WIZ_SET_FREQ_MIN: [
                "sudo",
                "-S",
                "bash",
                "-c",
                "echo 'core_freq_min=500' >> /boot/config.txt"
                if self.pi_model == "4"
                else "",
            ],
            api.WIZ_INCREASE_BUFFER: [
                "sudo",
                "-S",
                "sed",
                "-i",
                "$ s/$/ spidev.bufsiz=32768/",
                "/boot/cmdline.txt",
            ],
        }
        sys_command = command_to_system[cmd]
        self._logger.info("Running system command for {}:{}".format(cmd, sys_command))
        stdout, error = run_system_command(sys_command, data.get("password"))
        return jsonify(
            {
                "adduser_done": self.validate(api.WIZ_ADDUSER),
                "spi_enabled": self.validate(api.WIZ_ENABLE_SPI),
                "spi_buffer_increase": self.validate(api.WIZ_INCREASE_BUFFER),
                "core_freq_set": self.validate(api.WIZ_SET_CORE_FREQ),
                "core_freq_min_set": self.validate(api.WIZ_SET_FREQ_MIN),
                "errors": error,
            }
        )
