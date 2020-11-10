# -*- coding: utf-8 -*-


import unittest

import mock

from octoprint_ws281x_led_status import WS281xLedStatusPlugin

OPEN_SIGNATURE = "io.open"
DT_MODEL = "Raspberry Pi Model F Rev 1.1"


class WS281xTestCase(unittest.TestCase):
    def test_get_proc_dt_model(self):
        from octoprint_ws281x_led_status import get_proc_dt_model

        with mock.patch(OPEN_SIGNATURE, mock.mock_open(), create=True) as m:
            m.return_value.readline.return_value = DT_MODEL
            model = get_proc_dt_model()

        m.assert_called_once_with("/proc/device-tree/model", "rt", encoding="utf-8")
        self.assertEqual(model, DT_MODEL)
