# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

__author__ = "Charlie Powell <cp2004.github@gmail.com"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Charlie Powell 2020-2021 - released under the terms of the AGPLv3 License"

import getpass
import grp
import io
import logging
import os

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

        if not self.validate(cmd)["passed"]:
            return self.run_wizard_command(cmd, data)

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
        try:
            result = validators[cmd]()
        except FileNotFoundError:
            self._logger.warning("Tried to validate {} but files were missing")
            result = {"check": cmd, "passed": False, "reason": "missing"}
        except Exception as e:
            self._logger.error(
                "Something went wrong validating this command, please report to the issue tracker!"
            )
            self._logger.exception(e)
            result = {"check": cmd, "passed": False, "reason": "error"}

        return result

    @staticmethod
    def is_adduser_done():
        if "gpio" not in [grp.getgrgid(g).gr_name for g in os.getgroups()]:
            result = {"check": api.WIZ_ADDUSER, "passed": False, "reason": "failed"}
        else:
            result = {"check": api.WIZ_ADDUSER, "passed": True, "reason": ""}
        return result

    @staticmethod
    def is_spi_enabled():
        result = {"check": api.WIZ_ENABLE_SPI, "passed": False, "reason": "failed"}
        with io.open("/boot/config.txt") as file:
            for line in file:
                if line.startswith("dtparam=spi=on"):
                    result = {"check": api.WIZ_ENABLE_SPI, "passed": True, "reason": ""}
        return result

    @staticmethod
    def is_spi_buffer_increased():
        result = {"check": api.WIZ_INCREASE_BUFFER, "passed": False, "reason": "failed"}
        # Check `/boot/cmdline.txt` first
        with io.open("/boot/cmdline.txt") as file:
            for line in file:
                if "spidev.bufsiz=32768" in line:
                    return {
                        "check": api.WIZ_INCREASE_BUFFER,
                        "passed": True,
                        "reason": "",
                    }
        if not result["passed"]:
            # Check sys modules next - this is higher reliability but needs a reboot for changes
            with io.open(
                "/sys/module/spidev/parameters/bufsiz", encoding="utf-8", mode="rt"
            ) as file:
                if "32768" in file.readline().strip(" \t\r\n\0"):
                    result = {
                        "check": api.WIZ_INCREASE_BUFFER,
                        "passed": True,
                        "reason": "",
                    }

        return result

    def is_core_freq_set(self):
        result = {
            "check": api.WIZ_SET_CORE_FREQ,
            "passed": True if self.pi_model == "4" else False,
            "reason": "" if self.pi_model == "4" else "failed",
        }

        with io.open("/boot/config.txt") as file:
            for line in file:
                if line.startswith("core_freq=250"):
                    if self.pi_model == "4":
                        result = {
                            "check": api.WIZ_SET_CORE_FREQ,
                            "passed": False,
                            "reason": "pi4_250",
                        }
                    else:
                        result = {
                            "check": api.WIZ_SET_CORE_FREQ,
                            "passed": True,
                            "reason": "",
                        }
        return result

    def is_core_freq_min_set(self):
        result = {"check": api.WIZ_SET_CORE_FREQ, "passed": False, "reason": "failed"}

        if self.pi_model == "4":
            # Pi 4 has a variable clock speed, which messes up SPI timing
            with io.open("/boot/config.txt") as file:
                for line in file:
                    if line.startswith("core_freq_min=500"):
                        result = {
                            "check": api.WIZ_SET_CORE_FREQ,
                            "passed": True,
                            "reason": "",
                        }
        else:
            result = {
                "check": api.WIZ_SET_CORE_FREQ,
                "passed": True,
                "reason": "not_required",
            }
        return result

    def run_wizard_command(self, cmd, data):
        command_to_system = {
            # -S for sudo commands means accept password from stdin, see https://www.sudo.ws/man/1.8.13/sudo.man.html#S
            api.WIZ_ADDUSER: ["sudo", "-S", "adduser", getpass.getuser(), "gpio"],
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
        return self.on_api_get().update({"errors": error})
