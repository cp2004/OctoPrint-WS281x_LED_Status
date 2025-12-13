__author__ = "Jason Antman <jason@jasonantman.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Jason Antman 2025 - released under the terms of the AGPLv3 License"

import unittest
from typing import Any, Dict, Tuple
from unittest import mock

from octoprint_ws281x_led_status.backend import LEDBackend
from octoprint_ws281x_led_status.runner.segments import (
    InvalidSegmentError,
    SegmentManager,
    StripSegment,
)


class MockBackend(LEDBackend):
    """Mock backend for testing StripSegment integration."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self._pixels = [0] * config["count"]
        self._brightness = 255

    def begin(self) -> None:
        pass

    def show(self) -> None:
        pass

    def set_brightness(self, value: int) -> None:
        self._brightness = value

    def get_brightness(self) -> int:
        return self._brightness

    def num_pixels(self) -> int:
        return len(self._pixels)

    def set_pixel_color(self, index: int, color: int) -> None:
        self._pixels[index] = color

    def set_pixel_color_rgb(
        self, index: int, r: int, g: int, b: int, w: int = 0
    ) -> None:
        # Pack into 32-bit color
        color = (w << 24) | (r << 16) | (g << 8) | b
        self._pixels[index] = color

    def get_pixel_color(self, index: int) -> int:
        return self._pixels[index]

    def get_pixel_color_rgb(self, index: int) -> Tuple[int, int, int, int]:
        color = self._pixels[index]
        w = (color >> 24) & 0xFF
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        return (r, g, b, w)

    def cleanup(self) -> None:
        self._pixels = [0] * len(self._pixels)


class TestStripSegmentWithBackend(unittest.TestCase):
    """Test StripSegment integration with LED backend."""

    def setUp(self):
        """Create a mock backend for testing."""
        self.backend = MockBackend({"count": 100})

    def test_segment_creation(self):
        """Test creating a segment from a backend."""
        segment = StripSegment(self.backend, start=10, end=20)

        self.assertEqual(segment.numPixels(), 10)
        self.assertEqual(segment.start, 10)

    def test_segment_with_num_parameter(self):
        """Test creating segment with num parameter."""
        segment = StripSegment(self.backend, start=5, num=15)

        self.assertEqual(segment.numPixels(), 15)

    def test_segment_invalid_range(self):
        """Test that invalid segment ranges raise errors."""
        # End before start
        with self.assertRaises(InvalidSegmentError):
            StripSegment(self.backend, start=20, end=10)

        # Zero length
        with self.assertRaises(InvalidSegmentError):
            StripSegment(self.backend, start=10, end=10)

        # Negative num
        with self.assertRaises(InvalidSegmentError):
            StripSegment(self.backend, start=10, num=0)

        # No num or end
        with self.assertRaises(InvalidSegmentError):
            StripSegment(self.backend, start=10)

    def test_segment_setPixelColor(self):
        """Test setting pixel color in a segment."""
        segment = StripSegment(self.backend, start=10, end=20)

        # Set pixel 0 in segment (actual pixel 10 in strip)
        segment.setPixelColor(0, 0x00FF0000)

        # Verify it was set in the backend at correct position
        self.assertEqual(self.backend.get_pixel_color(10), 0x00FF0000)
        self.assertEqual(self.backend.get_pixel_color(9), 0)  # Should not be set

    def test_segment_setPixelColorRGB(self):
        """Test setting pixel color RGB in a segment."""
        segment = StripSegment(self.backend, start=20, end=30)

        # Set pixel 5 in segment (actual pixel 25 in strip)
        segment.setPixelColorRGB(5, 255, 128, 64, 32)

        # Verify it was set correctly
        r, g, b, w = self.backend.get_pixel_color_rgb(25)
        self.assertEqual((r, g, b, w), (255, 128, 64, 32))

    def test_segment_getPixelColor(self):
        """Test getting pixel color from a segment."""
        segment = StripSegment(self.backend, start=30, end=40)

        # Set a color in the backend
        self.backend.set_pixel_color(35, 0x0000FF00)

        # Get it through the segment (pixel 5 in segment = pixel 35 in strip)
        color = segment.getPixelColor(5)
        self.assertEqual(color, 0x0000FF00)

    def test_segment_getPixelColorRGB(self):
        """Test getting pixel color RGB from a segment."""
        segment = StripSegment(self.backend, start=40, end=50)

        # Set a color in the backend
        self.backend.set_pixel_color_rgb(45, 100, 150, 200, 50)

        # Get it through the segment (pixel 5 in segment = pixel 45 in strip)
        r, g, b, w = segment.getPixelColorRGB(5)
        self.assertEqual((r, g, b, w), (100, 150, 200, 50))

    def test_segment_getPixelColorRGBW(self):
        """Test getPixelColorRGBW maps to getPixelColorRGB."""
        segment = StripSegment(self.backend, start=50, end=60)

        self.backend.set_pixel_color_rgb(55, 10, 20, 30, 40)

        # Both methods should return the same value
        rgb = segment.getPixelColorRGB(5)
        rgbw = segment.getPixelColorRGBW(5)
        self.assertEqual(rgb, rgbw)

    def test_segment_show(self):
        """Test that segment.show() calls backend.show()."""
        # Mock the show method before creating segment
        # (segment captures reference in __init__)
        with mock.patch.object(self.backend, "show") as mock_show:
            segment = StripSegment(self.backend, start=0, end=10)
            segment.show()
            mock_show.assert_called_once()

    def test_segment_getBrightness(self):
        """Test that segment.getBrightness() calls backend.get_brightness()."""
        segment = StripSegment(self.backend, start=0, end=10)

        self.backend.set_brightness(150)
        brightness = segment.getBrightness()
        self.assertEqual(brightness, 150)


class TestSegmentManager(unittest.TestCase):
    """Test SegmentManager with LED backend."""

    def setUp(self):
        """Create a mock backend for testing."""
        self.backend = MockBackend({"count": 100})

    def test_create_single_segment(self):
        """Test creating a single segment."""
        settings = [{"start": 0, "end": 100}]
        manager = SegmentManager(self.backend, settings)
        manager.create_segments()

        segments = manager.list_segments()
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["id"], 1)

    def test_create_multiple_segments(self):
        """Test creating multiple segments."""
        settings = [{"start": 0, "end": 50}, {"start": 50, "end": 100}]
        manager = SegmentManager(self.backend, settings)
        manager.create_segments()

        segments = manager.list_segments()
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0]["id"], 1)
        self.assertEqual(segments[1]["id"], 2)

    def test_get_segment_by_id(self):
        """Test retrieving a segment by ID."""
        settings = [{"start": 0, "end": 50}, {"start": 50, "end": 100}]
        manager = SegmentManager(self.backend, settings)
        manager.create_segments()

        segment1 = manager.get_segment(1)
        segment2 = manager.get_segment(2)

        self.assertIsInstance(segment1, StripSegment)
        self.assertIsInstance(segment2, StripSegment)
        self.assertEqual(segment1.numPixels(), 50)
        self.assertEqual(segment2.numPixels(), 50)

    def test_segments_are_independent(self):
        """Test that segments operate independently."""
        settings = [{"start": 0, "end": 50}, {"start": 50, "end": 100}]
        manager = SegmentManager(self.backend, settings)
        manager.create_segments()

        segment1 = manager.get_segment(1)
        segment2 = manager.get_segment(2)

        # Set color in segment 1
        segment1.setPixelColor(10, 0x00FF0000)

        # Set color in segment 2
        segment2.setPixelColor(10, 0x0000FF00)

        # Verify they're set in correct positions
        self.assertEqual(self.backend.get_pixel_color(10), 0x00FF0000)  # Segment 1
        self.assertEqual(self.backend.get_pixel_color(60), 0x0000FF00)  # Segment 2

    def test_segment_with_sacrifice_pixel(self):
        """Test creating segment with sacrifice pixel (starts at 1 instead of 0)."""
        settings = [{"start": 1, "end": 100}]
        manager = SegmentManager(self.backend, settings)
        manager.create_segments()

        segment = manager.get_segment(1)

        # Set pixel 0 in segment (should be pixel 1 in backend)
        segment.setPixelColor(0, 0x00FF0000)

        # Pixel 0 in backend should be untouched
        self.assertEqual(self.backend.get_pixel_color(0), 0)
        # Pixel 1 should be set
        self.assertEqual(self.backend.get_pixel_color(1), 0x00FF0000)


if __name__ == "__main__":
    unittest.main()
