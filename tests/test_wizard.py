# -*- coding: utf-8 -*-
# import unittest
#
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
#     def test_core_freq_min(self):
#         from octoprint_ws281x_led_status.wizard import is_core_freq_min_set
#
#         # Test Pi 4 without string
#         with mock.patch(
#             OPEN_SIGNATURE,
#             mock.mock_open(read_data=CONFIG_TXT),
#             create=True,
#         ) as m:
#             is_set = is_core_freq_min_set("4")
#
#         m.assert_called_once_with("/boot/config.txt")
#         self.assertFalse(is_set)
#
#         # Test Pi 4 with string
#         with mock.patch(
#             OPEN_SIGNATURE,
#             mock.mock_open(read_data=CONFIG_TXT + CORE_FREQ_MIN_500),
#             create=True,
#         ) as m:
#             is_set = is_core_freq_min_set("4")
#
#         m.assert_called_once_with("/boot/config.txt")
#         self.assertTrue(is_set)
#
#         # Test Pi 3
#         with mock.patch(
#             OPEN_SIGNATURE,
#             mock.mock_open(read_data=CONFIG_TXT),
#             create=True,
#         ) as m:
#             is_set = is_core_freq_min_set("3")
#
#         m.assert_not_called()
#         self.assertTrue(is_set)
#
