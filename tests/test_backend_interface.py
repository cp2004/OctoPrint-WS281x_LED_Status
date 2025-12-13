__author__ = "Jason Antman <jason@jasonantman.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Jason Antman 2025 - released under the terms of the AGPLv3 License"

import unittest
from typing import Any, Dict, Tuple

from octoprint_ws281x_led_status.backend import (
    LEDBackend,
    color_packed_to_rgb,
    color_rgb_to_packed,
    validate_color_value,
    validate_pixel_index,
)


class TestColorConversion(unittest.TestCase):
    """Test color conversion utility functions."""

    def test_color_rgb_to_packed_rgb(self):
        """Test converting RGB values to packed format."""
        # Red
        packed = color_rgb_to_packed(255, 0, 0)
        self.assertEqual(packed, 0x00FF0000)

        # Green
        packed = color_rgb_to_packed(0, 255, 0)
        self.assertEqual(packed, 0x0000FF00)

        # Blue
        packed = color_rgb_to_packed(0, 0, 255)
        self.assertEqual(packed, 0x000000FF)

        # White (all channels)
        packed = color_rgb_to_packed(255, 255, 255)
        self.assertEqual(packed, 0x00FFFFFF)

    def test_color_rgb_to_packed_rgbw(self):
        """Test converting RGBW values to packed format."""
        # White channel only
        packed = color_rgb_to_packed(0, 0, 0, 255)
        self.assertEqual(packed, 0xFF000000)

        # Full RGBW
        packed = color_rgb_to_packed(255, 128, 64, 32)
        self.assertEqual(packed, 0x20FF8040)

    def test_color_packed_to_rgb(self):
        """Test converting packed format to RGB values."""
        # Red
        r, g, b, w = color_packed_to_rgb(0x00FF0000)
        self.assertEqual((r, g, b, w), (255, 0, 0, 0))

        # Green
        r, g, b, w = color_packed_to_rgb(0x0000FF00)
        self.assertEqual((r, g, b, w), (0, 255, 0, 0))

        # Blue
        r, g, b, w = color_packed_to_rgb(0x000000FF)
        self.assertEqual((r, g, b, w), (0, 0, 255, 0))

        # White
        r, g, b, w = color_packed_to_rgb(0x00FFFFFF)
        self.assertEqual((r, g, b, w), (255, 255, 255, 0))

    def test_color_packed_to_rgb_with_white(self):
        """Test converting packed format with white channel to RGB values."""
        # White channel only
        r, g, b, w = color_packed_to_rgb(0xFF000000)
        self.assertEqual((r, g, b, w), (0, 0, 0, 255))

        # Full RGBW
        r, g, b, w = color_packed_to_rgb(0x20FF8040)
        self.assertEqual((r, g, b, w), (255, 128, 64, 32))

    def test_color_round_trip(self):
        """Test that converting RGB->packed->RGB gives same values."""
        original = (128, 64, 192, 32)
        packed = color_rgb_to_packed(*original)
        result = color_packed_to_rgb(packed)
        self.assertEqual(result, original)


class TestValidation(unittest.TestCase):
    """Test validation utility functions."""

    def test_validate_pixel_index_valid(self):
        """Test validating valid pixel indices."""
        # Should not raise
        validate_pixel_index(0, 10)
        validate_pixel_index(5, 10)
        validate_pixel_index(9, 10)

    def test_validate_pixel_index_negative(self):
        """Test validating negative pixel index."""
        with self.assertRaises(IndexError):
            validate_pixel_index(-1, 10)

    def test_validate_pixel_index_too_large(self):
        """Test validating pixel index beyond strip length."""
        with self.assertRaises(IndexError):
            validate_pixel_index(10, 10)
        with self.assertRaises(IndexError):
            validate_pixel_index(100, 10)

    def test_validate_pixel_index_not_int(self):
        """Test validating non-integer pixel index."""
        with self.assertRaises(TypeError):
            validate_pixel_index("5", 10)
        with self.assertRaises(TypeError):
            validate_pixel_index(5.5, 10)

    def test_validate_color_value_valid(self):
        """Test validating valid color values."""
        # Should not raise
        validate_color_value(0)
        validate_color_value(128)
        validate_color_value(255)

    def test_validate_color_value_negative(self):
        """Test validating negative color value."""
        with self.assertRaises(ValueError):
            validate_color_value(-1)

    def test_validate_color_value_too_large(self):
        """Test validating color value > 255."""
        with self.assertRaises(ValueError):
            validate_color_value(256)
        with self.assertRaises(ValueError):
            validate_color_value(1000)

    def test_validate_color_value_not_int(self):
        """Test validating non-integer color value."""
        with self.assertRaises(TypeError):
            validate_color_value("128")
        with self.assertRaises(TypeError):
            validate_color_value(128.5)

    def test_validate_color_value_custom_name(self):
        """Test validation error messages use custom name."""
        with self.assertRaisesRegex(TypeError, "red"):
            validate_color_value("128", "red")
        with self.assertRaisesRegex(ValueError, "green"):
            validate_color_value(-1, "green")


class TestLEDBackendInterface(unittest.TestCase):
    """Test that LEDBackend is a proper abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that LEDBackend cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            LEDBackend({})

    def test_must_implement_all_methods(self):
        """Test that subclasses must implement all abstract methods."""

        class IncompleteBackend(LEDBackend):
            """Backend missing required methods."""

            def __init__(self, config: Dict[str, Any]) -> None:
                pass

        # Should not be able to instantiate without implementing all methods
        with self.assertRaises(TypeError):
            IncompleteBackend({})

    def test_complete_implementation_can_instantiate(self):
        """Test that complete implementation can be instantiated."""

        class CompleteBackend(LEDBackend):
            """Minimal complete backend implementation."""

            def __init__(self, config: Dict[str, Any]) -> None:
                self.config = config

            def begin(self) -> None:
                pass

            def show(self) -> None:
                pass

            def set_brightness(self, value: int) -> None:
                pass

            def get_brightness(self) -> int:
                return 0

            def num_pixels(self) -> int:
                return 0

            def set_pixel_color(self, index: int, color: int) -> None:
                pass

            def set_pixel_color_rgb(
                self, index: int, r: int, g: int, b: int, w: int = 0
            ) -> None:
                pass

            def get_pixel_color(self, index: int) -> int:
                return 0

            def get_pixel_color_rgb(self, index: int) -> Tuple[int, int, int, int]:
                return (0, 0, 0, 0)

            def cleanup(self) -> None:
                pass

        # Should be able to instantiate
        backend = CompleteBackend({"count": 10})
        self.assertIsNotNone(backend)


if __name__ == "__main__":
    unittest.main()
