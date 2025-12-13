__author__ = "Charlie Powell <cp2004.github@gmail.com"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Charlie Powell 2020-2021 - released under the terms of the AGPLv3 License"

import getpass
import grp
import logging
import os

from octoprint_ws281x_led_status import api
from octoprint_ws281x_led_status.backend.factory import get_registry
from octoprint_ws281x_led_status.util import run_system_command


# Backend-specific test requirements
# Maps backend names to their required validation tests
BACKEND_TEST_REQUIREMENTS = {
    "rpi_ws281x": {
        "required_tests": [
            api.WIZ_ADDUSER,  # User must be in gpio group
            api.WIZ_ENABLE_SPI,  # SPI must be enabled
            api.WIZ_INCREASE_BUFFER,  # SPI buffer size increase recommended
            api.WIZ_SET_CORE_FREQ,  # Core freq settings for Pi 3
            api.WIZ_SET_FREQ_MIN,  # Core freq min for Pi 4
        ],
        "description": "rpi_ws281x backend requires SPI enabled and specific OS configuration",
        "group": "gpio",  # Required group membership
    },
    "adafruit_neopixel_pwm": {
        "required_tests": [
            api.WIZ_CHECK_PIO,  # PIO device must exist and be writable on Pi 5
            api.WIZ_ADD_PIO_UDEV_RULE,  # udev rule needed if PIO device not writable
        ],
        "description": "Adafruit PWM backend requires PIO (Programmable I/O) support on Pi 5",
        "group": "gpio",  # User must be in gpio group for /dev/pio0 access
    },
}


class PluginWizard:
    def __init__(self, pi_model):
        self._logger = logging.getLogger("octoprint.plugins.ws281x_led_status.wizard")

        self.pi_model = pi_model

    def on_api_command(self, cmd, data):
        # Wizard specific API
        if not cmd.startswith("wiz"):
            return

        if self.pi_model is None:
            self._logger.error("Tried to run wizard command without Pi model, aborting")
            return

        if not self.validate(cmd)["passed"]:
            return self.run_wizard_command(cmd, data)

        return self.on_api_get()

    def get_config_txt_path(self):
        """
        Get the path to config.txt based on Pi model.

        Returns:
            str: Path to config.txt file
        """
        if self.pi_model == "5":
            return "/boot/firmware/config.txt"
        else:
            return "/boot/config.txt"

    def get_cmdline_txt_path(self):
        """
        Get the path to cmdline.txt based on Pi model.

        Returns:
            str: Path to cmdline.txt file
        """
        if self.pi_model == "5":
            return "/boot/firmware/cmdline.txt"
        else:
            return "/boot/cmdline.txt"

    def get_required_tests_for_backend(self, backend_name):
        """
        Get the list of required OS configuration tests for a specific backend.

        Args:
            backend_name (str): Name of the backend (e.g., "rpi_ws281x", "adafruit_neopixel_pwm")

        Returns:
            list: List of test command names (e.g., [api.WIZ_ADDUSER, api.WIZ_ENABLE_SPI])
        """
        if backend_name not in BACKEND_TEST_REQUIREMENTS:
            self._logger.warning(
                f"Backend '{backend_name}' not in test requirements, defaulting to all tests"
            )
            # Default to rpi_ws281x tests if backend unknown
            return BACKEND_TEST_REQUIREMENTS["rpi_ws281x"]["required_tests"]

        return BACKEND_TEST_REQUIREMENTS[backend_name]["required_tests"]

    def get_backend_recommendation(self):
        """
        Recommend the best LED backend based on detected Pi model.

        Returns:
            dict: Backend recommendation info with keys:
                - pi_model: Detected Pi model (e.g., "5", "4", "3")
                - recommended_backend: Backend name to use
                - reason: Human-readable explanation
                - alternative: Alternative backend (if any)
        """
        self._logger.debug(f"Generating backend recommendation for Raspberry Pi {self.pi_model}")

        registry = get_registry()
        available_backends = registry.list_backends()

        self._logger.debug(f"Available backends: {', '.join(available_backends) if available_backends else 'none'}")

        # Determine recommended backend based on Pi model
        if self.pi_model == "5":
            # Pi 5 requires Adafruit PWM backend
            if "adafruit_neopixel_pwm" in available_backends:
                recommendation = {
                    "pi_model": self.pi_model,
                    "recommended_backend": "adafruit_neopixel_pwm",
                    "reason": "Raspberry Pi 5 is supported by the Adafruit CircuitPython NeoPixel (PWM) backend. "
                    "You can use any GPIO pin (common choices: GPIO 10, 18, or 21). "
                    "The rpi_ws281x backend does not work reliably on Pi 5.",
                    "alternative": None,
                }
                self._logger.info(f"Pi 5 detected: Recommending '{recommendation['recommended_backend']}' backend")
                return recommendation
            else:
                recommendation = {
                    "pi_model": self.pi_model,
                    "recommended_backend": None,
                    "reason": "Raspberry Pi 5 requires the Adafruit CircuitPython NeoPixel (PWM) backend, "
                    "but it is not installed. Please install the required dependencies.",
                    "alternative": None,
                }
                self._logger.warning(
                    "Pi 5 detected but Adafruit PWM backend not available! LED strip will not work."
                )
                return recommendation
        else:
            # Pi 1-4 work best with rpi_ws281x
            if "rpi_ws281x" in available_backends:
                alternative = (
                    "adafruit_neopixel_pwm"
                    if "adafruit_neopixel_pwm" in available_backends
                    else None
                )
                recommendation = {
                    "pi_model": self.pi_model,
                    "recommended_backend": "rpi_ws281x",
                    "reason": f"Raspberry Pi {self.pi_model} works best with the rpi_ws281x (PWM) backend. "
                    "This is the most tested and reliable option for older Pi models.",
                    "alternative": alternative,
                }
                self._logger.info(
                    f"Pi {self.pi_model} detected: Recommending '{recommendation['recommended_backend']}' backend"
                )
                return recommendation
            else:
                # Fallback to Adafruit PWM if rpi_ws281x not available (shouldn't happen)
                if "adafruit_neopixel_pwm" in available_backends:
                    recommendation = {
                        "pi_model": self.pi_model,
                        "recommended_backend": "adafruit_neopixel_pwm",
                        "reason": "The rpi_ws281x backend is not available. "
                        "Using Adafruit CircuitPython NeoPixel (PWM) as alternative.",
                        "alternative": None,
                    }
                    self._logger.warning(
                        f"Pi {self.pi_model}: rpi_ws281x backend not available, "
                        f"falling back to Adafruit PWM backend"
                    )
                    return recommendation
                else:
                    recommendation = {
                        "pi_model": self.pi_model,
                        "recommended_backend": None,
                        "reason": "No compatible LED backends are available. Please check your installation.",
                        "alternative": None,
                    }
                    self._logger.error(
                        f"Pi {self.pi_model}: No compatible LED backends available!"
                    )
                    return recommendation

    def on_api_get(self, **kwargs):
        # Wizard specific API
        backend_recommendation = self.get_backend_recommendation()
        recommended_backend = backend_recommendation.get("recommended_backend")

        # Determine which tests are required for the recommended backend
        if recommended_backend:
            required_tests = self.get_required_tests_for_backend(recommended_backend)
        else:
            # No backend available, show all tests to help diagnose issues
            required_tests = BACKEND_TEST_REQUIREMENTS["rpi_ws281x"]["required_tests"]

        # Only run and return tests that are required for the recommended backend
        result = {"backend_recommendation": backend_recommendation}

        if api.WIZ_ADDUSER in required_tests:
            result["adduser_done"] = self.validate(api.WIZ_ADDUSER)
        if api.WIZ_ENABLE_SPI in required_tests:
            result["spi_enabled"] = self.validate(api.WIZ_ENABLE_SPI)
        if api.WIZ_INCREASE_BUFFER in required_tests:
            result["spi_buffer_increase"] = self.validate(api.WIZ_INCREASE_BUFFER)
        if api.WIZ_SET_CORE_FREQ in required_tests:
            result["core_freq_set"] = self.validate(api.WIZ_SET_CORE_FREQ)
        if api.WIZ_SET_FREQ_MIN in required_tests:
            result["core_freq_min_set"] = self.validate(api.WIZ_SET_FREQ_MIN)
        if api.WIZ_CHECK_PIO in required_tests:
            result["pio_available"] = self.validate(api.WIZ_CHECK_PIO)
        if api.WIZ_ADD_PIO_UDEV_RULE in required_tests:
            result["pio_udev_rule"] = self.validate(api.WIZ_ADD_PIO_UDEV_RULE)

        return result

    def validate(self, cmd):
        validators = {
            api.WIZ_ADDUSER: self.is_adduser_done,
            api.WIZ_ENABLE_SPI: self.is_spi_enabled,
            api.WIZ_INCREASE_BUFFER: self.is_spi_buffer_increased,
            api.WIZ_SET_CORE_FREQ: self.is_core_freq_set,
            api.WIZ_SET_FREQ_MIN: self.is_core_freq_min_set,
            api.WIZ_CHECK_PIO: self.is_pio_available,
            api.WIZ_ADD_PIO_UDEV_RULE: self.is_pio_udev_rule_set,
        }
        try:
            result = validators[cmd]()
        except OSError:
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

    def is_spi_enabled(self):
        """Check if SPI is enabled. Uses Pi-model-specific config file path."""
        result = {"check": api.WIZ_ENABLE_SPI, "passed": False, "reason": "failed"}
        config_path = self.get_config_txt_path()

        try:
            with open(config_path) as file:
                for line in file:
                    if line.startswith("dtparam=spi=on"):
                        result = {"check": api.WIZ_ENABLE_SPI, "passed": True, "reason": ""}
                        return result
        except FileNotFoundError:
            # Config file doesn't exist - check if /dev/spidev0.0 exists as fallback (Pi 5)
            if self.pi_model == "5" and os.path.exists("/dev/spidev0.0"):
                result = {"check": api.WIZ_ENABLE_SPI, "passed": True, "reason": "device_exists"}

        return result

    def is_spi_buffer_increased(self):
        """Check if SPI buffer is increased. Uses Pi-model-specific cmdline.txt path."""
        result = {"check": api.WIZ_INCREASE_BUFFER, "passed": False, "reason": "failed"}
        cmdline_path = self.get_cmdline_txt_path()

        # Check cmdline.txt first
        try:
            with open(cmdline_path) as file:
                for line in file:
                    if "spidev.bufsiz=32768" in line:
                        return {
                            "check": api.WIZ_INCREASE_BUFFER,
                            "passed": True,
                            "reason": "",
                        }
        except FileNotFoundError:
            pass

        if not result["passed"]:
            # Check sys modules next - this is higher reliability but needs a reboot for changes
            # Wrapped in it's own try-catch as it might not exist if SPI is not enabled
            # But we still want it to show as 'fixable', as the file above must have existed
            try:
                with open(
                    "/sys/module/spidev/parameters/bufsiz", encoding="utf-8"
                ) as file:
                    if "32768" in file.readline().strip(" \t\r\n\0"):
                        result = {
                            "check": api.WIZ_INCREASE_BUFFER,
                            "passed": True,
                            "reason": "",
                        }
            except OSError:
                pass

        return result

    def is_core_freq_set(self):
        """Check if core_freq is set. Uses Pi-model-specific config file path."""
        result = {
            "check": api.WIZ_SET_CORE_FREQ,
            "passed": True if self.pi_model in ["4", "5"] else False,
            "reason": "not_required" if self.pi_model in ["4", "5"] else "failed",
        }

        config_path = self.get_config_txt_path()

        try:
            with open(config_path) as file:
                for line in file:
                    if line.startswith("core_freq=250"):
                        if self.pi_model in ["4", "5"]:
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
        except FileNotFoundError:
            pass

        return result

    def is_core_freq_min_set(self):
        """Check if core_freq_min is set. Uses Pi-model-specific config file path."""
        result = {"check": api.WIZ_SET_FREQ_MIN, "passed": False, "reason": "failed"}

        if self.pi_model == "4":
            # Pi 4 has a variable clock speed, which messes up SPI timing
            config_path = self.get_config_txt_path()

            try:
                with open(config_path) as file:
                    for line in file:
                        if line.startswith("core_freq_min=500"):
                            result = {
                                "check": api.WIZ_SET_FREQ_MIN,
                                "passed": True,
                                "reason": "",
                            }
            except FileNotFoundError:
                pass
        else:
            result = {
                "check": api.WIZ_SET_FREQ_MIN,
                "passed": True,
                "reason": "not_required",
            }
        return result

    @staticmethod
    def is_pio_available():
        """
        Check if PIO (Programmable I/O) device exists and is writable.

        PIO support is required for Adafruit NeoPixel on Raspberry Pi 5.
        Returns different failure reasons:
        - "device_missing": /dev/pio0 does not exist (kernel/firmware too old)
        - "not_writable": /dev/pio0 exists but user cannot write to it
        - "": Passed - device exists and is writable

        See: https://github.com/adafruit/Adafruit_Blinka_Raspberry_Pi5_Neopixel
        """
        pio_device = "/dev/pio0"

        # Check if device exists
        if not os.path.exists(pio_device):
            return {
                "check": api.WIZ_CHECK_PIO,
                "passed": False,
                "reason": "device_missing",
            }

        # Check if device is writable by current user
        if not os.access(pio_device, os.W_OK):
            return {
                "check": api.WIZ_CHECK_PIO,
                "passed": False,
                "reason": "not_writable",
            }

        return {"check": api.WIZ_CHECK_PIO, "passed": True, "reason": ""}

    @staticmethod
    def is_pio_udev_rule_set():
        """
        Check if udev rule for PIO device is configured.

        The udev rule should set /dev/pio0 to be writable by the gpio group.
        Expected rule: SUBSYSTEM=="*-pio", GROUP="gpio", MODE="0660"

        This check looks for the rule in /etc/udev/rules.d/99-com.rules

        See: https://github.com/adafruit/Adafruit_Blinka_Raspberry_Pi5_Neopixel
        """
        udev_rules_file = "/etc/udev/rules.d/99-com.rules"
        expected_rule = 'SUBSYSTEM=="*-pio", GROUP="gpio", MODE="0660"'

        # If /dev/pio0 doesn't exist, udev rule isn't relevant yet
        if not os.path.exists("/dev/pio0"):
            return {
                "check": api.WIZ_ADD_PIO_UDEV_RULE,
                "passed": True,
                "reason": "not_required",  # Can't set rule if device doesn't exist
            }

        # If /dev/pio0 is already writable, rule might already be in place or not needed
        if os.access("/dev/pio0", os.W_OK):
            return {
                "check": api.WIZ_ADD_PIO_UDEV_RULE,
                "passed": True,
                "reason": "",  # Device is writable, rule working or not needed
            }

        # Device exists but not writable - check if rule is configured
        try:
            with open(udev_rules_file, encoding="utf-8") as file:
                for line in file:
                    if "*-pio" in line and "gpio" in line:
                        return {
                            "check": api.WIZ_ADD_PIO_UDEV_RULE,
                            "passed": True,
                            "reason": "needs_reboot",  # Rule exists but needs reboot to apply
                        }
        except FileNotFoundError:
            pass  # File doesn't exist, rule not set

        # Rule not found
        return {
            "check": api.WIZ_ADD_PIO_UDEV_RULE,
            "passed": False,
            "reason": "failed",
        }

    def run_wizard_command(self, cmd, data):
        config_txt = self.get_config_txt_path()
        cmdline_txt = self.get_cmdline_txt_path()

        command_to_system = {
            # -S for sudo commands means accept password from stdin, see https://www.sudo.ws/man/1.8.13/sudo.man.html#S
            api.WIZ_ADDUSER: ["sudo", "-S", "adduser", getpass.getuser(), "gpio"],
            api.WIZ_ENABLE_SPI: [
                "sudo",
                "-S",
                "bash",
                "-c",
                f"echo 'dtparam=spi=on' >> {config_txt}",
            ],
            api.WIZ_SET_CORE_FREQ: [
                "sudo",
                "-S",
                "bash",
                "-c",
                f"echo 'core_freq=250' >> {config_txt}"
                if self.pi_model not in ["4", "5"]
                else "",
            ],
            api.WIZ_SET_FREQ_MIN: [
                "sudo",
                "-S",
                "bash",
                "-c",
                f"echo 'core_freq_min=500' >> {config_txt}"
                if self.pi_model == "4"
                else "",
            ],
            api.WIZ_INCREASE_BUFFER: [
                "sudo",
                "-S",
                "sed",
                "-i",
                "$ s/$/ spidev.bufsiz=32768/",
                cmdline_txt,
            ],
            api.WIZ_ADD_PIO_UDEV_RULE: [
                "sudo",
                "-S",
                "bash",
                "-c",
                'echo \'SUBSYSTEM=="*-pio", GROUP="gpio", MODE="0660"\' >> /etc/udev/rules.d/99-com.rules',
            ],
        }
        sys_command = command_to_system[cmd]
        self._logger.info(f"Running system command for {cmd}:{sys_command}")
        stdout, error = run_system_command(sys_command, data.get("password"))
        api_get = self.on_api_get()
        api_get.update({"errors": error})
        return api_get
