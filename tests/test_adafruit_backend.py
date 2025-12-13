__author__ = "Jason Antman <jason@jasonantman.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Jason Antman 2025 - released under the terms of the AGPLv3 License"

import unittest
from typing import Any, Dict
from unittest import mock

# Import the backend - mocks are set up in conftest.py
from octoprint_ws281x_led_status.backend.adafruit_neopixel_pwm_backend import (
    AdafruitNeoPixelPWMBackend,
    map_strip_type_to_pixel_order,
    PIXEL_ORDERS,
)


class TestPixelOrderMapping(unittest.TestCase):
    """Test pixel order mapping from strip types."""

    def test_map_ws2811_strip_types(self):
        """Test mapping WS2811 strip types to pixel orders."""
        self.assertEqual(map_strip_type_to_pixel_order("WS2811_STRIP_GRB"), "GRB")
        self.assertEqual(map_strip_type_to_pixel_order("WS2811_STRIP_RGB"), "RGB")
        self.assertEqual(map_strip_type_to_pixel_order("WS2811_STRIP_RBG"), "RBG")

    def test_map_sk6812_strip_types(self):
        """Test mapping SK6812 strip types to pixel orders."""
        self.assertEqual(map_strip_type_to_pixel_order("SK6812_STRIP_RGBW"), "RGBW")
        self.assertEqual(map_strip_type_to_pixel_order("SK6812_STRIP_GRBW"), "GRBW")

    def test_map_unknown_defaults_to_grb(self):
        """Test that unknown strip types default to GRB."""
        self.assertEqual(map_strip_type_to_pixel_order("UNKNOWN_TYPE"), "GRB")
        self.assertEqual(map_strip_type_to_pixel_order(""), "GRB")


class TestAdafruitBackendInit(unittest.TestCase):
    """Test Adafruit PWM backend initialization."""

    def test_init_with_minimal_config(self):
        """Test initialization with minimal configuration."""
        config = {"count": 24, "pin": 10}
        backend = AdafruitNeoPixelPWMBackend(config)

        self.assertEqual(backend.num_pixels(), 24)
        self.assertEqual(backend.get_brightness(), 255)  # Default 100%
        self.assertEqual(backend._pixel_order_str, "GRB")  # Default
        self.assertEqual(backend._pin, 10)

    def test_init_with_full_config(self):
        """Test initialization with full configuration."""
        config = {
            "count": 50,
            "pin": 18,
            "brightness": 75,
            "pixel_order": "RGB",
        }
        backend = AdafruitNeoPixelPWMBackend(config)

        self.assertEqual(backend.num_pixels(), 50)
        self.assertEqual(backend.get_brightness(), 191)  # 75% of 255
        self.assertEqual(backend._pixel_order_str, "RGB")
        self.assertEqual(backend._pin, 18)

    def test_init_maps_strip_type_to_pixel_order(self):
        """Test that strip type is mapped to pixel order if pixel_order not provided."""
        config = {"count": 24, "pin": 10, "type": "WS2811_STRIP_GRB"}
        backend = AdafruitNeoPixelPWMBackend(config)

        self.assertEqual(backend._pixel_order_str, "GRB")

    def test_init_with_rgbw(self):
        """Test initialization with RGBW pixel order."""
        config = {"count": 24, "pin": 10, "pixel_order": "GRBW"}
        backend = AdafruitNeoPixelPWMBackend(config)

        self.assertTrue(backend._has_white)
        self.assertEqual(backend._pixel_order_str, "GRBW")

    def test_init_with_invalid_pixel_order_raises(self):
        """Test that invalid pixel order raises ValueError."""
        config = {"count": 24, "pin": 10, "pixel_order": "INVALID"}

        with self.assertRaises(ValueError) as cm:
            AdafruitNeoPixelPWMBackend(config)

        self.assertIn("Invalid pixel order", str(cm.exception))

    def test_init_without_pin_raises(self):
        """Test that missing pin raises ValueError."""
        config = {"count": 24}

        with self.assertRaises(ValueError) as cm:
            AdafruitNeoPixelPWMBackend(config)

        self.assertIn("GPIO pin number is required", str(cm.exception))

    def test_init_with_invalid_pin_raises(self):
        """Test that invalid GPIO pin raises ValueError."""
        # Pin too low
        with self.assertRaises(ValueError) as cm:
            AdafruitNeoPixelPWMBackend({"count": 24, "pin": -1})
        self.assertIn("Invalid GPIO pin number", str(cm.exception))

        # Pin too high
        with self.assertRaises(ValueError) as cm:
            AdafruitNeoPixelPWMBackend({"count": 24, "pin": 28})
        self.assertIn("Invalid GPIO pin number", str(cm.exception))

    def test_init_with_valid_common_pins(self):
        """Test that common GPIO pins are accepted."""
        for pin in [10, 18, 21]:
            config = {"count": 24, "pin": pin}
            backend = AdafruitNeoPixelPWMBackend(config)
            self.assertEqual(backend._pin, pin)

    def test_brightness_percentage_conversion(self):
        """Test brightness conversion from percentage to float."""
        # 0%
        backend = AdafruitNeoPixelPWMBackend({"count": 24, "pin": 10, "brightness": 0})
        self.assertEqual(backend.get_brightness(), 0)

        # 50%
        backend = AdafruitNeoPixelPWMBackend({"count": 24, "pin": 10, "brightness": 50})
        self.assertEqual(backend.get_brightness(), 127)  # 50% of 255

        # 100%
        backend = AdafruitNeoPixelPWMBackend({"count": 24, "pin": 10, "brightness": 100})
        self.assertEqual(backend.get_brightness(), 255)


class TestAdafruitBackendMethods(unittest.TestCase):
    """Test Adafruit PWM backend methods with mocked NeoPixel."""

    def setUp(self):
        """Create mock backend for each test."""
        self.config = {"count": 10, "pin": 10, "brightness": 100, "pixel_order": "GRB"}
        self.backend = AdafruitNeoPixelPWMBackend(self.config)

        # Mock the pixels object
        self.mock_pixels = mock.MagicMock()
        self.backend._pixels = self.mock_pixels

    def test_set_pixel_color_rgb(self):
        """Test setting pixel color with RGB values."""
        self.backend.set_pixel_color_rgb(5, 255, 128, 64, 0)

        # Should set the pixel on the mock object
        self.mock_pixels.__setitem__.assert_called_once_with(5, (255, 128, 64))

    def test_set_pixel_color_rgbw(self):
        """Test setting pixel color with RGBW values."""
        # Create RGBW backend
        config = {"count": 10, "pin": 10, "pixel_order": "RGBW"}
        backend = AdafruitNeoPixelPWMBackend(config)
        backend._pixels = mock.MagicMock()

        backend.set_pixel_color_rgb(3, 255, 128, 64, 32)

        # Should set all four components
        backend._pixels.__setitem__.assert_called_once_with(3, (255, 128, 64, 32))

    def test_set_pixel_color_packed(self):
        """Test setting pixel color with packed integer."""
        # Color: 0x00FF8040 = R:255, G:128, B:64
        self.backend.set_pixel_color(5, 0x00FF8040)

        self.mock_pixels.__setitem__.assert_called_once_with(5, (255, 128, 64))

    def test_get_pixel_color_rgb(self):
        """Test getting pixel color as RGB tuple."""
        # Set a color in the buffer (always 4-tuple internally)
        self.backend._buffer[5] = (255, 128, 64, 0)

        r, g, b, w = self.backend.get_pixel_color_rgb(5)

        self.assertEqual((r, g, b, w), (255, 128, 64, 0))

    def test_get_pixel_color_packed(self):
        """Test getting pixel color as packed integer."""
        # Set a color in the buffer (always 4-tuple internally)
        self.backend._buffer[5] = (255, 128, 64, 0)

        color = self.backend.get_pixel_color(5)

        # 0x00FF8040
        self.assertEqual(color, 0x00FF8040)

    def test_get_pixel_color_out_of_bounds(self):
        """Test getting pixel color for out of bounds index."""
        r, g, b, w = self.backend.get_pixel_color_rgb(999)

        self.assertEqual((r, g, b, w), (0, 0, 0, 0))

    def test_set_brightness(self):
        """Test setting brightness."""
        self.backend.set_brightness(128)  # 50% of 255

        self.assertEqual(self.backend.get_brightness(), 128)
        self.mock_pixels.brightness = 0.5019607843137255  # 128/255

    def test_get_brightness(self):
        """Test getting brightness."""
        self.backend._brightness = 0.5

        brightness = self.backend.get_brightness()

        self.assertEqual(brightness, 127)  # 50% of 255

    def test_show(self):
        """Test show method calls pixels.show()."""
        self.backend.show()

        self.mock_pixels.show.assert_called_once()

    def test_cleanup(self):
        """Test cleanup turns off LEDs and deinits."""
        self.backend.cleanup()

        # PWM backend uses tuple for fill, not packed integer
        self.mock_pixels.fill.assert_called_once_with((0, 0, 0))
        self.mock_pixels.show.assert_called_once()
        self.mock_pixels.deinit.assert_called_once()


class TestAdafruitBackendBegin(unittest.TestCase):
    """Test Adafruit PWM backend begin() method."""

    @mock.patch("octoprint_ws281x_led_status.backend.adafruit_neopixel_pwm_backend.board")
    @mock.patch("octoprint_ws281x_led_status.backend.adafruit_neopixel_pwm_backend.NeoPixel")
    def test_begin_creates_pixels(self, mock_neopixel, mock_board):
        """Test begin() creates NeoPixel object."""
        # Mock the board.D10 pin
        mock_pin = mock.MagicMock()
        mock_board.D10 = mock_pin

        mock_pixels = mock.MagicMock()
        mock_neopixel.return_value = mock_pixels

        config = {"count": 24, "pin": 10, "brightness": 75, "pixel_order": "GRB"}
        backend = AdafruitNeoPixelPWMBackend(config)
        backend.begin()

        # Verify NeoPixel was created with correct parameters
        mock_neopixel.assert_called_once()
        call_args = mock_neopixel.call_args

        self.assertEqual(call_args[0][0], mock_pin)  # GPIO pin
        self.assertEqual(call_args[0][1], 24)  # num_pixels
        self.assertAlmostEqual(call_args[1]["brightness"], 0.75, places=2)
        self.assertFalse(call_args[1]["auto_write"])

        # Verify pixels were initialized to off
        mock_pixels.fill.assert_called_once_with((0, 0, 0))
        mock_pixels.show.assert_called_once()

    @mock.patch("octoprint_ws281x_led_status.backend.adafruit_neopixel_pwm_backend.board")
    @mock.patch("octoprint_ws281x_led_status.backend.adafruit_neopixel_pwm_backend.NeoPixel")
    def test_begin_with_rgbw(self, mock_neopixel, mock_board):
        """Test begin() with RGBW pixel order."""
        # Mock the board.D10 pin
        mock_pin = mock.MagicMock()
        mock_board.D10 = mock_pin

        mock_pixels = mock.MagicMock()
        mock_neopixel.return_value = mock_pixels

        config = {"count": 24, "pin": 10, "pixel_order": "GRBW"}
        backend = AdafruitNeoPixelPWMBackend(config)
        backend.begin()

        # Verify pixels were initialized with RGBW tuple
        mock_pixels.fill.assert_called_once_with((0, 0, 0, 0))

    @mock.patch("octoprint_ws281x_led_status.backend.adafruit_neopixel_pwm_backend.board")
    @mock.patch("octoprint_ws281x_led_status.backend.adafruit_neopixel_pwm_backend.NeoPixel")
    def test_begin_with_different_pins(self, mock_neopixel, mock_board):
        """Test begin() works with different GPIO pins."""
        for pin_num in [10, 18, 21]:
            # Mock the board.D{pin} attribute
            mock_pin = mock.MagicMock()
            setattr(mock_board, f"D{pin_num}", mock_pin)

            mock_pixels = mock.MagicMock()
            mock_neopixel.return_value = mock_pixels

            config = {"count": 24, "pin": pin_num}
            backend = AdafruitNeoPixelPWMBackend(config)
            backend.begin()

            # Verify the correct pin was used
            call_args = mock_neopixel.call_args
            self.assertEqual(call_args[0][0], mock_pin)

            # Reset mocks for next iteration
            mock_neopixel.reset_mock()


class TestIsAvailable(unittest.TestCase):
    """Test PWM backend availability detection."""

    @mock.patch("octoprint_ws281x_led_status.backend.adafruit_neopixel_pwm_backend.ADAFRUIT_AVAILABLE", True)
    def test_is_available_libraries_installed(self):
        """Test is_available returns True when libraries are installed."""
        result = AdafruitNeoPixelPWMBackend.is_available()
        self.assertTrue(result)

    @mock.patch("octoprint_ws281x_led_status.backend.adafruit_neopixel_pwm_backend.ADAFRUIT_AVAILABLE", False)
    def test_is_available_libraries_not_installed(self):
        """Test is_available returns False when libraries not installed."""
        result = AdafruitNeoPixelPWMBackend.is_available()
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
