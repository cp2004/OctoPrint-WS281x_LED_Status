import unittest
from unittest import mock

from octoprint_ws281x_led_status.wizard import PluginWizard

# import mock
#
# from .util import setup_mock_popen
#
# OPEN_SIGNATURE = "io.open"
# CONFIG_TXT = """
# # For more options and information see
# # http://rpf.io/configtxt
# # Some settings may impact device functionality. See link above for details
#
# # uncomment if you get no picture on HDMI for a default "safe" mode
# #hdmi_safe=1
#
# # uncomment this if your display has a black border of unused pixels visible
# # and your display can output without overscan
# #disable_overscan=1
#
# # uncomment the following to adjust overscan. Use positive numbers if console
# # goes off screen, and negative if there is too much border
# #overscan_left=16
# #overscan_right=16
# #overscan_top=16
# #overscan_bottom=16
#
# # uncomment to force a console size. By default it will be display's size minus
# # overscan.
# #framebuffer_width=1280
# #framebuffer_height=720
#
# # uncomment if hdmi display is not detected and composite is being output
# #hdmi_force_hotplug=1
#
# # uncomment to force a specific HDMI mode (this will force VGA)
# #hdmi_group=1
# #hdmi_mode=1
#
# # uncomment to force a HDMI mode rather than DVI. This can make audio work in
# # DMT (computer monitor) modes
# #hdmi_drive=2
#
# # uncomment to increase signal to HDMI, if you have interference, blanking, or
# # no display
# #config_hdmi_boost=4
#
# # uncomment for composite PAL
# #sdtv_mode=2
#
# #uncomment to overclock the arm. 700 MHz is the default.
# #arm_freq=800
#
# # Uncomment some or all of these to enable the optional hardware interfaces
# #dtparam=i2c_arm=on
# #dtparam=i2s=on
# #dtparam=spi=on
#
# # Uncomment this to enable infrared communication.
# #dtoverlay=gpio-ir,gpio_pin=17
# #dtoverlay=gpio-ir-tx,gpio_pin=18
#
# # Additional overlays and parameters are documented /boot/overlays/README
#
# # Enable audio (loads snd_bcm2835)
# dtparam=audio=on
#
# [pi4]
# # Enable DRM VC4 V3D driver on top of the dispmanx display stack
# dtoverlay=vc4-fkms-v3d
# max_framebuffers=2
#
# [all]
# #dtoverlay=vc4-fkms-v3d
# # enable raspicam
# start_x=1
# gpu_mem=128
# """
#
# SPI_ENABLED = "dtparam=spi=on\n"
# SPI_COMMENTED = "#dtparam=spi=on\n"
# CORE_FREQ_250 = "core_freq=250\n"
# CORE_FREQ_MIN_500 = "core_freq_min=500\n"
#
# CMDLINE_TXT = """console=serial0,115200 console=tty1 root=PARTUUID=6c586e13-02 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait"""
# SPI_BUFFER = "spidev.bufsiz=32768"
# SPI_INCORRECT_BUFFER = "spidev.bufsiz=328"
#
#
# class WizardTestCase(unittest.TestCase):
#     def test_adduser_done(self):
#         from octoprint_ws281x_led_status.wizard import is_adduser_done
#
#         mock_popen_valid = setup_mock_popen(
#             expected_stdout="pi : pi adm tty dialout cdrom sudo audio video plugdev games users input netdev spi i2c gpio",
#             expected_stderr="",
#         )
#
#         self.assertTrue(is_adduser_done("4"))
#         mock_popen_valid.communicate.assert_called_once_with()
#
#         mock_popen_invalid = setup_mock_popen(
#             expected_stdout="pi : pi adm tty dialout cdrom sudo audio video plugdev games users input netdev spi i2c",
#             expected_stderr="",
#         )
#
#         self.assertFalse(is_adduser_done("4"))
#         mock_popen_invalid.communicate.assert_called_once_with()
#
#     def test_spi_enabled(self):
#         from octoprint_ws281x_led_status.wizard import is_spi_enabled
#
#         # Test detecting NO SPI STRING
#         with mock.patch(
#             OPEN_SIGNATURE, mock.mock_open(read_data=CONFIG_TXT), create=True
#         ) as m:
#             is_enabled = is_spi_enabled("4")
#
#         m.assert_called_once_with("/boot/config.txt")
#         self.assertFalse(is_enabled)
#
#         # Test detecting WITH SPI STRING
#         with mock.patch(
#             OPEN_SIGNATURE,
#             mock.mock_open(read_data=CONFIG_TXT + SPI_ENABLED),
#             create=True,
#         ) as m:
#             is_enabled = is_spi_enabled("4")
#
#         m.assert_called_once_with("/boot/config.txt")
#         self.assertTrue(is_enabled)
#
#         # Test detecting WITH COMMENTED SPI STRING
#         with mock.patch(
#             OPEN_SIGNATURE,
#             mock.mock_open(read_data=CONFIG_TXT + SPI_COMMENTED),
#             create=True,
#         ) as m:
#             is_enabled = is_spi_enabled("4")
#
#         m.assert_called_once_with("/boot/config.txt")
#         self.assertFalse(is_enabled)
#
#     def test_spi_buffer(self):
#         from octoprint_ws281x_led_status.wizard import is_spi_buffer_increased
#
#         with mock.patch(
#             OPEN_SIGNATURE, mock.mock_open(read_data=CMDLINE_TXT), create=True
#         ) as m:
#             is_increased = is_spi_buffer_increased("4")
#
#         m.assert_called_once_with("/boot/cmdline.txt")
#         self.assertFalse(is_increased)
#
#         with mock.patch(
#             OPEN_SIGNATURE,
#             mock.mock_open(read_data=CMDLINE_TXT + SPI_BUFFER),
#             create=True,
#         ) as m:
#             is_increased = is_spi_buffer_increased("4")
#
#         m.assert_called_once_with("/boot/cmdline.txt")
#         self.assertTrue(is_increased)
#
#         with mock.patch(
#             OPEN_SIGNATURE,
#             mock.mock_open(read_data=CMDLINE_TXT + SPI_INCORRECT_BUFFER),
#             create=True,
#         ) as m:
#             is_increased = is_spi_buffer_increased("4")
#
#         m.assert_called_once_with("/boot/cmdline.txt")
#         self.assertFalse(is_increased)
#
#     def test_core_freq(self):
#         from octoprint_ws281x_led_status.wizard import is_core_freq_set
#
#         # Test Pi 3 without string
#         with mock.patch(
#             OPEN_SIGNATURE,
#             mock.mock_open(read_data=CONFIG_TXT),
#             create=True,
#         ) as m:
#             is_set = is_core_freq_set("3")
#
#         m.assert_called_once_with("/boot/config.txt")
#         self.assertFalse(is_set)
#
#         # Test Pi 3 with string
#         with mock.patch(
#             OPEN_SIGNATURE,
#             mock.mock_open(read_data=CONFIG_TXT + CORE_FREQ_250),
#             create=True,
#         ) as m:
#             is_set = is_core_freq_set("3")
#
#         m.assert_called_once_with("/boot/config.txt")
#         self.assertTrue(is_set)
#
#         # Test Pi 4
#         with mock.patch(
#             OPEN_SIGNATURE,
#             mock.mock_open(read_data=CONFIG_TXT),
#             create=True,
#         ) as m:
#             is_set = is_core_freq_set("4")
#
#         m.assert_not_called()
#         self.assertTrue(is_set)
#
#


class TestWizardBackendRecommendation(unittest.TestCase):
    """Test backend recommendation logic in wizard"""

    @mock.patch("octoprint_ws281x_led_status.wizard.get_registry")
    def test_pi5_recommends_adafruit_when_available(self, mock_get_registry):
        """Pi 5 should recommend Adafruit PWM backend when available"""
        # Mock registry to return both backends
        mock_registry = mock.Mock()
        mock_registry.list_backends.return_value = [
            "rpi_ws281x",
            "adafruit_neopixel_pwm",
        ]
        mock_get_registry.return_value = mock_registry

        wizard = PluginWizard(pi_model="5")
        recommendation = wizard.get_backend_recommendation()

        self.assertEqual(recommendation["pi_model"], "5")
        self.assertEqual(recommendation["recommended_backend"], "adafruit_neopixel_pwm")
        self.assertIsNone(recommendation["alternative"])
        self.assertIn("Raspberry Pi 5", recommendation["reason"])

    @mock.patch("octoprint_ws281x_led_status.wizard.get_registry")
    def test_pi5_warns_when_adafruit_unavailable(self, mock_get_registry):
        """Pi 5 should warn when Adafruit backend is not available"""
        # Mock registry to return only rpi_ws281x
        mock_registry = mock.Mock()
        mock_registry.list_backends.return_value = ["rpi_ws281x"]
        mock_get_registry.return_value = mock_registry

        wizard = PluginWizard(pi_model="5")
        recommendation = wizard.get_backend_recommendation()

        self.assertEqual(recommendation["pi_model"], "5")
        self.assertIsNone(recommendation["recommended_backend"])
        self.assertIn("not installed", recommendation["reason"])

    @mock.patch("octoprint_ws281x_led_status.wizard.get_registry")
    def test_pi4_recommends_rpi_ws281x(self, mock_get_registry):
        """Pi 4 should recommend rpi_ws281x backend"""
        # Mock registry to return both backends
        mock_registry = mock.Mock()
        mock_registry.list_backends.return_value = [
            "rpi_ws281x",
            "adafruit_neopixel_pwm",
        ]
        mock_get_registry.return_value = mock_registry

        wizard = PluginWizard(pi_model="4")
        recommendation = wizard.get_backend_recommendation()

        self.assertEqual(recommendation["pi_model"], "4")
        self.assertEqual(recommendation["recommended_backend"], "rpi_ws281x")
        self.assertEqual(recommendation["alternative"], "adafruit_neopixel_pwm")
        self.assertIn("works best with", recommendation["reason"])

    @mock.patch("octoprint_ws281x_led_status.wizard.get_registry")
    def test_pi3_recommends_rpi_ws281x(self, mock_get_registry):
        """Pi 3 should recommend rpi_ws281x backend"""
        # Mock registry to return only rpi_ws281x
        mock_registry = mock.Mock()
        mock_registry.list_backends.return_value = ["rpi_ws281x"]
        mock_get_registry.return_value = mock_registry

        wizard = PluginWizard(pi_model="3")
        recommendation = wizard.get_backend_recommendation()

        self.assertEqual(recommendation["pi_model"], "3")
        self.assertEqual(recommendation["recommended_backend"], "rpi_ws281x")
        self.assertIsNone(recommendation["alternative"])

    @mock.patch("octoprint_ws281x_led_status.wizard.get_registry")
    def test_pi4_fallback_to_adafruit(self, mock_get_registry):
        """Pi 4 should fallback to Adafruit PWM if rpi_ws281x unavailable"""
        # Mock registry to return only Adafruit PWM backend
        mock_registry = mock.Mock()
        mock_registry.list_backends.return_value = ["adafruit_neopixel_pwm"]
        mock_get_registry.return_value = mock_registry

        wizard = PluginWizard(pi_model="4")
        recommendation = wizard.get_backend_recommendation()

        self.assertEqual(recommendation["pi_model"], "4")
        self.assertEqual(recommendation["recommended_backend"], "adafruit_neopixel_pwm")
        self.assertIn("not available", recommendation["reason"])

    @mock.patch("octoprint_ws281x_led_status.wizard.get_registry")
    def test_no_backends_available(self, mock_get_registry):
        """Should handle case where no backends are available"""
        # Mock registry to return no backends
        mock_registry = mock.Mock()
        mock_registry.list_backends.return_value = []
        mock_get_registry.return_value = mock_registry

        wizard = PluginWizard(pi_model="4")
        recommendation = wizard.get_backend_recommendation()

        self.assertEqual(recommendation["pi_model"], "4")
        self.assertIsNone(recommendation["recommended_backend"])
        self.assertIn("No compatible", recommendation["reason"])


class TestWizardBackendAwareTests(unittest.TestCase):
    """Test backend-aware OS configuration tests"""

    def test_get_required_tests_for_rpi_ws281x(self):
        """rpi_ws281x backend should require all OS config tests"""
        from octoprint_ws281x_led_status import api

        wizard = PluginWizard(pi_model="4")
        required_tests = wizard.get_required_tests_for_backend("rpi_ws281x")

        # Should require all tests
        self.assertIn(api.WIZ_ADDUSER, required_tests)
        self.assertIn(api.WIZ_ENABLE_SPI, required_tests)
        self.assertIn(api.WIZ_INCREASE_BUFFER, required_tests)
        self.assertIn(api.WIZ_SET_CORE_FREQ, required_tests)
        self.assertIn(api.WIZ_SET_FREQ_MIN, required_tests)

    def test_get_required_tests_for_adafruit_pwm(self):
        """Adafruit PWM backend should require PIO tests"""
        from octoprint_ws281x_led_status import api

        wizard = PluginWizard(pi_model="5")
        required_tests = wizard.get_required_tests_for_backend("adafruit_neopixel_pwm")

        # Should require PIO tests
        self.assertIn(api.WIZ_CHECK_PIO, required_tests)
        self.assertIn(api.WIZ_ADD_PIO_UDEV_RULE, required_tests)
        self.assertEqual(len(required_tests), 2)

    def test_get_required_tests_unknown_backend(self):
        """Unknown backend should default to rpi_ws281x tests"""
        from octoprint_ws281x_led_status import api

        wizard = PluginWizard(pi_model="4")
        required_tests = wizard.get_required_tests_for_backend("unknown_backend")

        # Should default to rpi_ws281x tests
        self.assertIn(api.WIZ_ADDUSER, required_tests)
        self.assertIn(api.WIZ_ENABLE_SPI, required_tests)

    @mock.patch("octoprint_ws281x_led_status.wizard.get_registry")
    @mock.patch.object(PluginWizard, "validate")
    def test_on_api_get_pi5_pwm_pio_tests(self, mock_validate, mock_get_registry):
        """Pi 5 with PWM backend should run PIO tests"""
        from octoprint_ws281x_led_status import api

        # Mock registry to recommend Adafruit PWM backend
        mock_registry = mock.Mock()
        mock_registry.list_backends.return_value = ["adafruit_neopixel_pwm"]
        mock_get_registry.return_value = mock_registry

        # Mock validate to return passed=True
        mock_validate.return_value = {"check": "test", "passed": True, "reason": ""}

        wizard = PluginWizard(pi_model="5")
        result = wizard.on_api_get()

        # Should run PIO tests
        self.assertEqual(mock_validate.call_count, 2)
        mock_validate.assert_any_call(api.WIZ_CHECK_PIO)
        mock_validate.assert_any_call(api.WIZ_ADD_PIO_UDEV_RULE)

        # Should return backend recommendation
        self.assertIn("backend_recommendation", result)
        self.assertEqual(result["backend_recommendation"]["pi_model"], "5")
        self.assertEqual(
            result["backend_recommendation"]["recommended_backend"],
            "adafruit_neopixel_pwm",
        )

        # Should include PIO test results
        self.assertIn("pio_available", result)
        self.assertIn("pio_udev_rule", result)

        # Should not include SPI test results
        self.assertNotIn("adduser_done", result)
        self.assertNotIn("spi_enabled", result)
        self.assertNotIn("spi_buffer_increase", result)

    @mock.patch("octoprint_ws281x_led_status.wizard.get_registry")
    @mock.patch.object(PluginWizard, "validate")
    def test_on_api_get_pi4_rpi_ws281x_all_tests(
        self, mock_validate, mock_get_registry
    ):
        """Pi 4 with rpi_ws281x backend should run all OS config tests"""
        from octoprint_ws281x_led_status import api

        # Mock registry to recommend rpi_ws281x backend
        mock_registry = mock.Mock()
        mock_registry.list_backends.return_value = ["rpi_ws281x"]
        mock_get_registry.return_value = mock_registry

        # Mock validate to return passed=True
        mock_validate.return_value = {"check": "test", "passed": True, "reason": ""}

        wizard = PluginWizard(pi_model="4")
        result = wizard.on_api_get()

        # Should run all tests
        self.assertEqual(mock_validate.call_count, 5)
        mock_validate.assert_any_call(api.WIZ_ADDUSER)
        mock_validate.assert_any_call(api.WIZ_ENABLE_SPI)
        mock_validate.assert_any_call(api.WIZ_INCREASE_BUFFER)
        mock_validate.assert_any_call(api.WIZ_SET_CORE_FREQ)
        mock_validate.assert_any_call(api.WIZ_SET_FREQ_MIN)

        # Should include all test results
        self.assertIn("adduser_done", result)
        self.assertIn("spi_enabled", result)
        self.assertIn("spi_buffer_increase", result)
        self.assertIn("core_freq_set", result)
        self.assertIn("core_freq_min_set", result)


class TestWizardPiModelPaths(unittest.TestCase):
    """Test Pi-model-specific file paths"""

    def test_get_config_txt_path_pi5(self):
        """Pi 5 should use /boot/firmware/config.txt"""
        wizard = PluginWizard(pi_model="5")
        path = wizard.get_config_txt_path()
        self.assertEqual(path, "/boot/firmware/config.txt")

    def test_get_config_txt_path_pi4(self):
        """Pi 4 should use /boot/config.txt"""
        wizard = PluginWizard(pi_model="4")
        path = wizard.get_config_txt_path()
        self.assertEqual(path, "/boot/config.txt")

    def test_get_config_txt_path_pi3(self):
        """Pi 3 should use /boot/config.txt"""
        wizard = PluginWizard(pi_model="3")
        path = wizard.get_config_txt_path()
        self.assertEqual(path, "/boot/config.txt")

    def test_get_cmdline_txt_path_pi5(self):
        """Pi 5 should use /boot/firmware/cmdline.txt"""
        wizard = PluginWizard(pi_model="5")
        path = wizard.get_cmdline_txt_path()
        self.assertEqual(path, "/boot/firmware/cmdline.txt")

    def test_get_cmdline_txt_path_pi4(self):
        """Pi 4 should use /boot/cmdline.txt"""
        wizard = PluginWizard(pi_model="4")
        path = wizard.get_cmdline_txt_path()
        self.assertEqual(path, "/boot/cmdline.txt")

    def test_is_core_freq_set_pi5_not_required(self):
        """Pi 5 should not require core_freq setting"""
        wizard = PluginWizard(pi_model="5")
        result = wizard.is_core_freq_set()

        self.assertTrue(result["passed"])
        self.assertEqual(result["reason"], "not_required")

    @mock.patch("builtins.open", mock.mock_open(read_data="# test config\n"))
    def test_is_spi_enabled_uses_pi5_path(self):
        """is_spi_enabled should use Pi-specific config path"""
        wizard = PluginWizard(pi_model="5")

        with mock.patch("builtins.open", mock.mock_open(read_data="# test\n")) as m:
            wizard.is_spi_enabled()
            m.assert_called_with("/boot/firmware/config.txt")

    @mock.patch("os.path.exists")
    @mock.patch("builtins.open", side_effect=FileNotFoundError)
    def test_is_spi_enabled_pi5_fallback_to_device(self, mock_open, mock_exists):
        """Pi 5 should check for /dev/spidev0.0 if config file missing"""
        mock_exists.return_value = True

        wizard = PluginWizard(pi_model="5")
        result = wizard.is_spi_enabled()

        self.assertTrue(result["passed"])
        self.assertEqual(result["reason"], "device_exists")
        mock_exists.assert_called_with("/dev/spidev0.0")


class TestWizardPIOValidation(unittest.TestCase):
    """Test PIO device validation for Adafruit backend on Pi 5"""

    @mock.patch("os.path.exists")
    @mock.patch("os.access")
    def test_is_pio_available_device_exists_and_writable(
        self, mock_access, mock_exists
    ):
        """PIO device exists and is writable - should pass"""
        from octoprint_ws281x_led_status import api

        mock_exists.return_value = True
        mock_access.return_value = True

        result = PluginWizard.is_pio_available()

        self.assertEqual(result["check"], api.WIZ_CHECK_PIO)
        self.assertTrue(result["passed"])
        self.assertEqual(result["reason"], "")
        mock_exists.assert_called_once_with("/dev/pio0")
        mock_access.assert_called_once_with("/dev/pio0", mock.ANY)

    @mock.patch("os.path.exists")
    def test_is_pio_available_device_missing(self, mock_exists):
        """PIO device does not exist - should fail with device_missing"""
        from octoprint_ws281x_led_status import api

        mock_exists.return_value = False

        result = PluginWizard.is_pio_available()

        self.assertEqual(result["check"], api.WIZ_CHECK_PIO)
        self.assertFalse(result["passed"])
        self.assertEqual(result["reason"], "device_missing")
        mock_exists.assert_called_once_with("/dev/pio0")

    @mock.patch("os.path.exists")
    @mock.patch("os.access")
    def test_is_pio_available_device_not_writable(self, mock_access, mock_exists):
        """PIO device exists but not writable - should fail with not_writable"""
        from octoprint_ws281x_led_status import api

        mock_exists.return_value = True
        mock_access.return_value = False

        result = PluginWizard.is_pio_available()

        self.assertEqual(result["check"], api.WIZ_CHECK_PIO)
        self.assertFalse(result["passed"])
        self.assertEqual(result["reason"], "not_writable")
        mock_exists.assert_called_once_with("/dev/pio0")
        mock_access.assert_called_once_with("/dev/pio0", mock.ANY)

    @mock.patch("os.path.exists")
    def test_is_pio_udev_rule_set_device_missing(self, mock_exists):
        """If /dev/pio0 doesn't exist, udev rule check is not required"""
        from octoprint_ws281x_led_status import api

        mock_exists.return_value = False

        result = PluginWizard.is_pio_udev_rule_set()

        self.assertEqual(result["check"], api.WIZ_ADD_PIO_UDEV_RULE)
        self.assertTrue(result["passed"])
        self.assertEqual(result["reason"], "not_required")
        mock_exists.assert_called_once_with("/dev/pio0")

    @mock.patch("os.access")
    @mock.patch("os.path.exists")
    def test_is_pio_udev_rule_set_device_writable(self, mock_exists, mock_access):
        """If /dev/pio0 is writable, udev rule check passes"""
        from octoprint_ws281x_led_status import api

        mock_exists.return_value = True
        mock_access.return_value = True

        result = PluginWizard.is_pio_udev_rule_set()

        self.assertEqual(result["check"], api.WIZ_ADD_PIO_UDEV_RULE)
        self.assertTrue(result["passed"])
        self.assertEqual(result["reason"], "")
        mock_exists.assert_called_once_with("/dev/pio0")
        mock_access.assert_called_once_with("/dev/pio0", mock.ANY)

    @mock.patch("builtins.open", mock.mock_open(read_data='SUBSYSTEM=="*-pio", GROUP="gpio", MODE="0660"\n'))
    @mock.patch("os.access")
    @mock.patch("os.path.exists")
    def test_is_pio_udev_rule_set_rule_exists_needs_reboot(
        self, mock_exists, mock_access
    ):
        """If rule file exists but device not writable, needs reboot"""
        from octoprint_ws281x_led_status import api

        mock_exists.return_value = True
        mock_access.return_value = False

        result = PluginWizard.is_pio_udev_rule_set()

        self.assertEqual(result["check"], api.WIZ_ADD_PIO_UDEV_RULE)
        self.assertTrue(result["passed"])
        self.assertEqual(result["reason"], "needs_reboot")

    @mock.patch("builtins.open", mock.mock_open(read_data="# No PIO rule here\n"))
    @mock.patch("os.access")
    @mock.patch("os.path.exists")
    def test_is_pio_udev_rule_set_rule_not_found(self, mock_exists, mock_access):
        """If device exists but not writable and no rule, should fail"""
        from octoprint_ws281x_led_status import api

        mock_exists.return_value = True
        mock_access.return_value = False

        result = PluginWizard.is_pio_udev_rule_set()

        self.assertEqual(result["check"], api.WIZ_ADD_PIO_UDEV_RULE)
        self.assertFalse(result["passed"])
        self.assertEqual(result["reason"], "failed")

    @mock.patch("builtins.open", side_effect=FileNotFoundError)
    @mock.patch("os.access")
    @mock.patch("os.path.exists")
    def test_is_pio_udev_rule_set_file_missing(self, mock_exists, mock_access, mock_open):
        """If udev rules file doesn't exist, rule is not set"""
        from octoprint_ws281x_led_status import api

        mock_exists.return_value = True
        mock_access.return_value = False

        result = PluginWizard.is_pio_udev_rule_set()

        self.assertEqual(result["check"], api.WIZ_ADD_PIO_UDEV_RULE)
        self.assertFalse(result["passed"])
        self.assertEqual(result["reason"], "failed")
