__author__ = "Charlie Powell <cp2004.github@gmail.com"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Charlie Powell 2020-2021 - released under the terms of the AGPLv3 License"


import unittest
from unittest import mock

OPEN_SIGNATURE = "io.open"
DT_MODEL = "Raspberry Pi 4 Model B Rev 1.1"


def mock_get_proc_dt_model():
    """
    Mocks the Pi model so that we can load the core plugin, bypassing the 'is Pi' checks
    """
    return DT_MODEL


class TestPlugin(unittest.TestCase):
    @mock.patch(
        "octoprint_ws281x_led_status.get_proc_dt_model",
        side_effect=mock_get_proc_dt_model,
    )
    def test_load(self, mock_dt_model):
        """
        Test load of plugin, bypassing checks
        """
        from octoprint_ws281x_led_status import __plugin_load__

        __plugin_load__()

    def test_get_proc_dt_model(self):
        """
        Test reading the right file
        """
        from octoprint_ws281x_led_status import get_proc_dt_model

        with mock.patch(OPEN_SIGNATURE, new=mock.mock_open(read_data=DT_MODEL)):
            model = get_proc_dt_model()

        self.assertEqual(model, DT_MODEL)

    @mock.patch(
        "octoprint_ws281x_led_status.get_proc_dt_model",
        side_effect=mock_get_proc_dt_model,
    )
    def test_get_pi_model(self, mock_dt_model):
        """
        Test parsing the actual Pi model
        """
        from octoprint_ws281x_led_status import determine_pi_version

        self.assertEqual(determine_pi_version(), "4")
