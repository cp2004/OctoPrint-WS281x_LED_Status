__author__ = "Jason Antman <jason@jasonantman.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Jason Antman 2025 - released under the terms of the AGPLv3 License"

"""
Pytest configuration and fixtures for OctoPrint WS281x LED Status tests.
"""

import sys
from unittest import mock

# Mock Adafruit libraries BEFORE any other imports
# This ensures that when backend modules are imported, the mocks are already in place
mock_board = mock.MagicMock()
mock_neopixel_module = mock.MagicMock()
mock_neopixel_class = mock.MagicMock()
mock_neopixel_module.NeoPixel = mock_neopixel_class

sys.modules["board"] = mock_board
sys.modules["neopixel"] = mock_neopixel_module
