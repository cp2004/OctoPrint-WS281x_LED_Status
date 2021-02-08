# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

import unittest

from octoprint.util import to_bytes

from . import util


class WS281xUtilTestCase(unittest.TestCase):
    def test_hex_to_rgb(self):
        from octoprint_ws281x_led_status.util import hex_to_rgb

        tests = {
            "#29aab1": (41, 170, 177),
            "#efdcd0": (239, 220, 208),
            "#1ee8a8": (30, 232, 168),
            "#84c513": (132, 197, 19),
            "#7a4f2e": (122, 79, 46),
        }

        for test_case, test_result in tests.items():
            self.assertEqual(hex_to_rgb(test_case), test_result)

    def test_average(self):
        from octoprint_ws281x_led_status.util import average

        tests = {
            (25, 100): 62,
            (46, 81): 63,
            (22, 79): 50,
            (83, 98): 90,
            (28, 85): 56,
        }
        for test_case, test_result in tests.items():
            self.assertEqual(average(test_case[0], test_case[1]), test_result)

    def test_wheel(self):
        from octoprint_ws281x_led_status.util import wheel

        tests = {
            29: (87, 168, 0),
            64: (192, 63, 0),
            108: (186, 0, 69),
            181: (0, 33, 222),
            183: (0, 39, 216),
            244: (0, 222, 33),
            250: (0, 240, 15),
        }

        for test_case, test_result in tests.items():
            self.assertTupleEqual(wheel(test_case), test_result)

    def test_basic_system_command(self):
        expected_stdout = "pi : pi adm tty dialout cdrom sudo audio video plugdev games users input netdev spi i2c gpio"
        self.check_sys_command(
            ["groups", "pi"], expected_stdout, "", (expected_stdout, None)
        )

    def test_failed_password(self):
        self.check_sys_command(
            ["sudo", "adduser", "pi", "gpio"], "", "no password", ("", "password")
        )

    def test_with_password(self):
        self.check_sys_command(
            [
                "sudo",
                "-S",
                "bash",
                "-c",
                "echo 'dtparam=spi=on' >> /boot/config.txt",
            ],
            "",
            "",
            ("", None),
            password="raspberry",
            called_once_with=to_bytes("raspberry\n", "utf-8"),
        )

    def check_sys_command(
        self,
        command,
        expected_stdout,
        expected_stderr,
        expected_return,
        password=None,
        called_once_with=None,
    ):
        from octoprint_ws281x_led_status.util import run_system_command

        mock_popen = util.setup_mock_popen(expected_stdout, expected_stderr)

        test_return = run_system_command(command, password)  # No password supplied

        self.assertEqual(test_return, expected_return)
        if called_once_with:
            mock_popen.communicate.assert_called_once_with(called_once_with)
        else:
            mock_popen.communicate.assert_called_once_with()

    def test_blend_colors(self):
        from octoprint_ws281x_led_status.util import blend_two_colors

        # Test value > 100
        result = blend_two_colors((255, 0, 0), (0, 0, 255), float(101) / 100)
        self.assertTupleEqual((128, 0, 0), result)

        # Test colour > 255
        result = blend_two_colors((187, 245, 2), (345, 255, 255), float(101) / 100)
        self.assertTupleEqual((92, 122, 0), result)

        # Test value = 0
        result = blend_two_colors((187, 245, 2), (156, 0, 255), float(0) / 100)
        self.assertTupleEqual((171, 122, 128), result)

        # Test with nothing special
        result = blend_two_colors((187, 245, 6), (100, 0, 255), float(45) / 100)
        self.assertTupleEqual((69, 55, 71), result)
