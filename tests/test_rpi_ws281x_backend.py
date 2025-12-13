__author__ = "Jason Antman <jason@jasonantman.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Jason Antman 2025 - released under the terms of the AGPLv3 License"

import unittest
from unittest import mock

from octoprint_ws281x_led_status.backend.rpi_ws281x_backend import RpiWS281xBackend


class TestRpiWS281xBackend(unittest.TestCase):
    """Test rpi_ws281x backend wrapper."""

    def test_init_with_minimal_config(self):
        """Test initialization with minimal configuration."""
        config = {"count": 24}

        backend = RpiWS281xBackend(config)

        self.assertEqual(backend._num_pixels, 24)
        self.assertEqual(backend._pin, 10)  # default
        self.assertEqual(backend._freq_hz, 800000)  # default
        self.assertEqual(backend._dma, 10)  # default
        self.assertFalse(backend._invert)  # default
        self.assertEqual(backend._channel, 0)  # default

    def test_init_with_full_config(self):
        """Test initialization with full configuration."""
        config = {
            "count": 50,
            "pin": 12,
            "freq_hz": 400000,
            "dma": 5,
            "invert": True,
            "brightness": 75,
            "channel": 1,
            "type": "SK6812W_STRIP",
        }

        backend = RpiWS281xBackend(config)

        self.assertEqual(backend._num_pixels, 50)
        self.assertEqual(backend._pin, 12)
        self.assertEqual(backend._freq_hz, 400000)
        self.assertEqual(backend._dma, 5)
        self.assertTrue(backend._invert)
        self.assertEqual(backend._channel, 1)
        # Brightness 75% -> 191 out of 255
        self.assertEqual(backend._brightness, 191)

    def test_init_brightness_conversion(self):
        """Test that brightness is correctly converted from percentage."""
        # 0% -> 0
        backend = RpiWS281xBackend({"count": 10, "brightness": 0})
        self.assertEqual(backend._brightness, 0)

        # 50% -> 127
        backend = RpiWS281xBackend({"count": 10, "brightness": 50})
        self.assertEqual(backend._brightness, 127)

        # 100% -> 255
        backend = RpiWS281xBackend({"count": 10, "brightness": 100})
        self.assertEqual(backend._brightness, 255)

    def test_init_invalid_strip_type(self):
        """Test that invalid strip type raises error."""
        config = {"count": 10, "type": "INVALID_TYPE"}

        with self.assertRaisesRegex(ValueError, "Unknown strip type"):
            RpiWS281xBackend(config)

    def test_init_valid_strip_types(self):
        """Test that all valid strip types are accepted."""
        valid_types = [
            "WS2811_STRIP_GRB",
            "WS2812_STRIP",
            "WS2811_STRIP_RGB",
            "SK6812_STRIP",
            "SK6812W_STRIP",
            "SK6812_STRIP_RGBW",
        ]

        for strip_type in valid_types:
            config = {"count": 10, "type": strip_type}
            backend = RpiWS281xBackend(config)
            self.assertIsNotNone(backend)

    @mock.patch("octoprint_ws281x_led_status.backend.rpi_ws281x_backend.PixelStrip")
    def test_begin_success(self, mock_pixel_strip_class):
        """Test successful hardware initialization."""
        config = {"count": 24, "pin": 10}
        backend = RpiWS281xBackend(config)

        mock_strip = mock.Mock()
        mock_pixel_strip_class.return_value = mock_strip

        backend.begin()

        # Verify PixelStrip was created with correct parameters
        mock_pixel_strip_class.assert_called_once()
        call_kwargs = mock_pixel_strip_class.call_args[1]
        self.assertEqual(call_kwargs["num"], 24)
        self.assertEqual(call_kwargs["pin"], 10)

        # Verify begin() was called on the strip
        mock_strip.begin.assert_called_once()

    @mock.patch("octoprint_ws281x_led_status.backend.rpi_ws281x_backend.PixelStrip")
    def test_begin_failure(self, mock_pixel_strip_class):
        """Test hardware initialization failure."""
        config = {"count": 24}
        backend = RpiWS281xBackend(config)

        mock_pixel_strip_class.side_effect = Exception("Hardware error")

        with self.assertRaisesRegex(RuntimeError, "Failed to initialize"):
            backend.begin()

    @mock.patch("octoprint_ws281x_led_status.backend.rpi_ws281x_backend.PixelStrip")
    def test_show(self, mock_pixel_strip_class):
        """Test show() method."""
        backend = RpiWS281xBackend({"count": 10})
        mock_strip = mock.Mock()
        mock_pixel_strip_class.return_value = mock_strip
        backend.begin()

        backend.show()

        mock_strip.show.assert_called_once()

    @mock.patch("octoprint_ws281x_led_status.backend.rpi_ws281x_backend.PixelStrip")
    def test_set_brightness(self, mock_pixel_strip_class):
        """Test set_brightness() method."""
        backend = RpiWS281xBackend({"count": 10})
        mock_strip = mock.Mock()
        mock_pixel_strip_class.return_value = mock_strip
        backend.begin()

        backend.set_brightness(128)

        mock_strip.setBrightness.assert_called_once_with(128)
        self.assertEqual(backend._brightness, 128)

    @mock.patch("octoprint_ws281x_led_status.backend.rpi_ws281x_backend.PixelStrip")
    def test_get_brightness(self, mock_pixel_strip_class):
        """Test get_brightness() method."""
        backend = RpiWS281xBackend({"count": 10})
        mock_strip = mock.Mock()
        mock_strip.getBrightness.return_value = 200
        mock_pixel_strip_class.return_value = mock_strip
        backend.begin()

        brightness = backend.get_brightness()

        self.assertEqual(brightness, 200)
        mock_strip.getBrightness.assert_called_once()

    @mock.patch("octoprint_ws281x_led_status.backend.rpi_ws281x_backend.PixelStrip")
    def test_num_pixels(self, mock_pixel_strip_class):
        """Test num_pixels() method."""
        backend = RpiWS281xBackend({"count": 42})
        mock_strip = mock.Mock()
        mock_strip.numPixels.return_value = 42
        mock_pixel_strip_class.return_value = mock_strip
        backend.begin()

        num = backend.num_pixels()

        self.assertEqual(num, 42)

    @mock.patch("octoprint_ws281x_led_status.backend.rpi_ws281x_backend.PixelStrip")
    def test_set_pixel_color(self, mock_pixel_strip_class):
        """Test set_pixel_color() with packed color."""
        backend = RpiWS281xBackend({"count": 10})
        mock_strip = mock.Mock()
        mock_pixel_strip_class.return_value = mock_strip
        backend.begin()

        backend.set_pixel_color(5, 0x00FF8040)

        mock_strip.setPixelColor.assert_called_once_with(5, 0x00FF8040)

    @mock.patch("octoprint_ws281x_led_status.backend.rpi_ws281x_backend.PixelStrip")
    def test_set_pixel_color_rgb(self, mock_pixel_strip_class):
        """Test set_pixel_color_rgb() with separate values."""
        backend = RpiWS281xBackend({"count": 10})
        mock_strip = mock.Mock()
        mock_pixel_strip_class.return_value = mock_strip
        backend.begin()

        backend.set_pixel_color_rgb(3, 255, 128, 64, 32)

        mock_strip.setPixelColorRGB.assert_called_once_with(3, 255, 128, 64, 32)

    @mock.patch("octoprint_ws281x_led_status.backend.rpi_ws281x_backend.PixelStrip")
    def test_get_pixel_color(self, mock_pixel_strip_class):
        """Test get_pixel_color() returns packed color."""
        backend = RpiWS281xBackend({"count": 10})
        mock_strip = mock.Mock()
        mock_strip.getPixelColor.return_value = 0x00FF0000
        mock_pixel_strip_class.return_value = mock_strip
        backend.begin()

        color = backend.get_pixel_color(2)

        self.assertEqual(color, 0x00FF0000)
        mock_strip.getPixelColor.assert_called_once_with(2)

    @mock.patch("octoprint_ws281x_led_status.backend.rpi_ws281x_backend.PixelStrip")
    def test_get_pixel_color_rgb(self, mock_pixel_strip_class):
        """Test get_pixel_color_rgb() returns tuple."""
        backend = RpiWS281xBackend({"count": 10})
        mock_strip = mock.Mock()
        mock_strip.getPixelColorRGBW.return_value = (255, 128, 64, 0)
        mock_pixel_strip_class.return_value = mock_strip
        backend.begin()

        color = backend.get_pixel_color_rgb(4)

        self.assertEqual(color, (255, 128, 64, 0))
        mock_strip.getPixelColorRGBW.assert_called_once_with(4)

    @mock.patch("octoprint_ws281x_led_status.backend.rpi_ws281x_backend.PixelStrip")
    def test_cleanup(self, mock_pixel_strip_class):
        """Test cleanup() turns off all LEDs."""
        backend = RpiWS281xBackend({"count": 5})
        mock_strip = mock.Mock()
        mock_strip.numPixels.return_value = 5
        mock_pixel_strip_class.return_value = mock_strip
        backend.begin()

        backend.cleanup()

        # Should set all pixels to 0 (off)
        self.assertEqual(mock_strip.setPixelColor.call_count, 5)
        for i in range(5):
            mock_strip.setPixelColor.assert_any_call(i, 0)

        # Should call show to update the strip
        mock_strip.show.assert_called()


if __name__ == "__main__":
    unittest.main()
