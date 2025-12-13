__author__ = "Jason Antman <jason@jasonantman.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Jason Antman 2025 - released under the terms of the AGPLv3 License"

"""
Adafruit CircuitPython NeoPixel PWM backend for LED control.

This backend uses the adafruit-circuitpython-neopixel library to control
NeoPixel LEDs via GPIO. This approach works on all Raspberry Pi models
including the Raspberry Pi 5, which uses PIO (Programmable I/O).

Key features:
- Works on all Raspberry Pi models (1-5)
- Supports any GPIO pin (configurable)
- Supports RGB and RGBW pixel orders
- Software-based brightness control

OS Requirements:
- Raspberry Pi 5: Requires PIO (Programmable I/O) support
  - /dev/pio0 device must exist (kernel 6.12+)
  - User must have write access to /dev/pio0 (requires gpio group membership)
  - udev rule required: SUBSYSTEM=="*-pio", GROUP="gpio", MODE="0660" in /etc/udev/rules.d/99-com.rules
  - See: https://github.com/adafruit/Adafruit_Blinka_Raspberry_Pi5_Neopixel
- Raspberry Pi 1-4: No special requirements beyond standard GPIO access
- No SPI configuration needed
- No core frequency settings needed

IMPORTANT: Wizard test requirements for this backend are defined in:
    octoprint_ws281x_led_status/wizard.py::BACKEND_TEST_REQUIREMENTS["adafruit_neopixel_pwm"]
If you modify the OS requirements for this backend, update the wizard tests accordingly.
"""

import os
import tempfile
from typing import Any, Dict, Tuple

from octoprint_ws281x_led_status.backend import LEDBackend

# Try to import Adafruit libraries - they may not be installed
# Note: The lgpio library (used by Adafruit Blinka on Pi 5) creates notification
# files (.lgd-nfy*) in its working directory. We set the LG_WD environment variable
# to ensure these files are created in a writable location (the system temp directory)
# rather than the current working directory (which may be / for services like OctoPrint).
if 'LG_WD' not in os.environ:
    os.environ['LG_WD'] = tempfile.gettempdir()

try:
    import board
    from neopixel import NeoPixel
    import neopixel

    ADAFRUIT_AVAILABLE = True
except ImportError:
    ADAFRUIT_AVAILABLE = False


# Pixel order constants as tuples (R, G, B, [W])
# The neopixel library uses tuples to represent the order of color components
PIXEL_ORDERS = {
    # RGB variations (indices: R=0, G=1, B=2)
    "RGB": (0, 1, 2),
    "RBG": (0, 2, 1),
    "GRB": (1, 0, 2),
    "GBR": (1, 2, 0),
    "BRG": (2, 0, 1),
    "BGR": (2, 1, 0),
    # RGBW variations (indices: R=0, G=1, B=2, W=3)
    "RGBW": (0, 1, 2, 3),
    "RBGW": (0, 2, 1, 3),
    "GRBW": (1, 0, 2, 3),
    "GBRW": (1, 2, 0, 3),
    "BRGW": (2, 0, 1, 3),
    "BGRW": (2, 1, 0, 3),
}


def map_strip_type_to_pixel_order(strip_type: str) -> str:
    """
    Map rpi_ws281x strip type names to pixel order strings.

    Args:
        strip_type: Strip type name (e.g. "WS2811_STRIP_GRB")

    Returns:
        Pixel order string (e.g. "GRB")
    """
    # Remove common prefixes
    order = strip_type.replace("WS2811_STRIP_", "").replace("SK6812_STRIP_", "")
    # Validate it's a known order
    if order not in PIXEL_ORDERS:
        # Default to GRB if unknown
        return "GRB"
    return order


class AdafruitNeoPixelPWMBackend(LEDBackend):
    """
    LED backend using Adafruit CircuitPython NeoPixel library (PWM-based).

    This backend is designed for maximum compatibility across all Raspberry Pi
    models including Pi 5. It uses the PWM interface with configurable GPIO pin.

    Configuration parameters:
        pin (int): GPIO pin number (required, e.g. 10, 18, 21)
        count (int): Number of LEDs (required)
        brightness (int): Brightness percentage 0-100 (optional, default 100)
        pixel_order (str): Pixel order like "GRB", "RGB", "RGBW" (optional, default "GRB")
        auto_write (bool): Whether to auto-write on pixel changes (optional, default False)

    Note: The following rpi_ws281x parameters are NOT used by this backend:
        - freq_hz: Determined by hardware
        - dma: Not applicable
        - channel: Not applicable
        - invert: Not supported
        - type: Use pixel_order instead (but will be auto-converted if provided)
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the Adafruit NeoPixel PWM backend.

        Args:
            config: Configuration dictionary with LED settings

        Raises:
            ImportError: If Adafruit libraries are not installed
            ValueError: If configuration is invalid
        """
        if not ADAFRUIT_AVAILABLE:
            raise ImportError(
                "Adafruit CircuitPython NeoPixel library not available. "
                "Install with: pip install adafruit-circuitpython-neopixel"
            )

        self.config = config
        self._pixels = None
        self._num_pixels = int(config["count"])

        # GPIO pin - required
        if "pin" not in config:
            raise ValueError("GPIO pin number is required (config['pin'])")
        self._pin = int(config["pin"])
        
        # Validate pin number (basic sanity check)
        if self._pin < 0 or self._pin > 40:
            raise ValueError(f"Invalid GPIO pin number: {self._pin}. Must be between 0 and 40.")
        
        # Validate GPIO pin number (Raspberry Pi common range)
        if self._pin < 0 or self._pin > 27:
            raise ValueError(
                f"Invalid GPIO pin number: {self._pin}. "
                f"Valid range is 0-27. Common pins: 10, 18, 21"
            )

        # Brightness: convert percentage (0-100) to float (0.0-1.0)
        brightness_percent = int(config.get("brightness", 100))
        self._brightness = max(0.0, min(1.0, brightness_percent / 100.0))

        # Pixel order - try to map from strip type if provided
        pixel_order_str = config.get("pixel_order", None)
        if pixel_order_str is None and "type" in config:
            # Map from strip_type (rpi_ws281x format)
            pixel_order_str = map_strip_type_to_pixel_order(config["type"])
        if pixel_order_str is None:
            pixel_order_str = "GRB"  # Default for most NeoPixels

        # Validate pixel order
        if pixel_order_str not in PIXEL_ORDERS:
            raise ValueError(
                f"Invalid pixel order: {pixel_order_str}. "
                f"Supported: {', '.join(PIXEL_ORDERS.keys())}"
            )

        self._pixel_order = PIXEL_ORDERS[pixel_order_str]
        self._pixel_order_str = pixel_order_str
        self._has_white = pixel_order_str.endswith("W")

        # Auto-write should be False to allow buffering
        self._auto_write = config.get("auto_write", False)

        # Buffer for pixel colors (always stored as (r, g, b, w) 4-tuples for consistency)
        self._buffer = [(0, 0, 0, 0)] * self._num_pixels

    def begin(self) -> None:
        """
        Initialize the LED hardware.

        Creates the NeoPixel object and prepares it for use.

        Raises:
            RuntimeError: If initialization fails
        """
        try:
            # Get the GPIO pin using board.D{pin} notation
            pin_attr = f"D{self._pin}"
            if not hasattr(board, pin_attr):
                raise ValueError(
                    f"GPIO pin {self._pin} not available on this board. "
                    f"Try common pins: 10, 18, or 21"
                )

            pin = getattr(board, pin_attr)

            # Create NeoPixel object
            self._pixels = NeoPixel(
                pin,
                self._num_pixels,
                brightness=self._brightness,
                auto_write=self._auto_write,
                pixel_order=self._pixel_order,
            )

            # Initialize all pixels to off
            self._pixels.fill((0, 0, 0, 0) if self._has_white else (0, 0, 0))
            if not self._auto_write:
                self._pixels.show()

        except Exception as e:
            raise RuntimeError(f"Failed to initialize NeoPixel on GPIO {self._pin}: {e}") from e

    def show(self) -> None:
        """Update the LED strip with buffered pixel colors."""
        if self._pixels is not None:
            self._pixels.show()

    def set_brightness(self, value: int) -> None:
        """
        Set global brightness.

        Args:
            value: Brightness value 0-255

        Note: This affects future pixel updates by scaling color values.
        """
        # Convert 0-255 to 0.0-1.0
        self._brightness = max(0.0, min(1.0, value / 255.0))
        if self._pixels is not None:
            self._pixels.brightness = self._brightness

    def get_brightness(self) -> int:
        """
        Get current brightness.

        Returns:
            Brightness value 0-255
        """
        return int(self._brightness * 255)

    def setBrightness(self, value: int) -> None:
        """
        Compatibility alias for set_brightness() to match rpi_ws281x API.

        The runner code calls this camelCase method directly.
        """
        self.set_brightness(value)

    def num_pixels(self) -> int:
        """
        Get the number of pixels.

        Returns:
            Number of LEDs
        """
        return self._num_pixels

    def numPixels(self) -> int:
        """
        Compatibility alias for num_pixels() to match rpi_ws281x API.

        The effect code calls this camelCase method directly.
        """
        return self.num_pixels()

    def set_pixel_color(self, index: int, color: int) -> None:
        """
        Set pixel color using packed 32-bit integer.

        Args:
            index: Pixel index (0-based)
            color: Color as 32-bit integer (0xWWRRGGBB or 0xRRGGBB)
        """
        # Extract RGBW components from packed integer
        w = (color >> 24) & 0xFF
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF

        self.set_pixel_color_rgb(index, r, g, b, w)

    def set_pixel_color_rgb(
        self, index: int, r: int, g: int, b: int, w: int = 0
    ) -> None:
        """
        Set pixel color using separate RGB(W) values.

        Args:
            index: Pixel index (0-based)
            r: Red value 0-255
            g: Green value 0-255
            b: Blue value 0-255
            w: White value 0-255 (for RGBW strips)
        """
        if self._pixels is None:
            return

        if index < 0 or index >= self._num_pixels:
            return

        # Always store as 4-tuple in buffer for consistency
        self._buffer[index] = (r, g, b, w)

        # Set pixel with appropriate tuple size for hardware
        if self._has_white:
            self._pixels[index] = (r, g, b, w)
        else:
            self._pixels[index] = (r, g, b)

    def setPixelColorRGB(
        self, index: int, r: int, g: int, b: int, w: int = 0
    ) -> None:
        """
        Compatibility alias for set_pixel_color_rgb() to match rpi_ws281x API.

        The effect code calls this camelCase method directly.
        """
        self.set_pixel_color_rgb(index, r, g, b, w)

    def get_pixel_color(self, index: int) -> int:
        """
        Get pixel color as packed 32-bit integer.

        Args:
            index: Pixel index (0-based)

        Returns:
            Color as 32-bit integer (0xWWRRGGBB)
        """
        r, g, b, w = self.get_pixel_color_rgb(index)
        return (w << 24) | (r << 16) | (g << 8) | b

    def get_pixel_color_rgb(self, index: int) -> Tuple[int, int, int, int]:
        """
        Get pixel color as separate RGBW values.

        Args:
            index: Pixel index (0-based)

        Returns:
            Tuple of (r, g, b, w) values
        """
        if index < 0 or index >= self._num_pixels:
            return (0, 0, 0, 0)

        # Buffer always contains 4-tuples
        return self._buffer[index]

    def cleanup(self) -> None:
        """Clean up resources and turn off all LEDs."""
        if self._pixels is not None:
            try:
                self._pixels.fill((0, 0, 0, 0) if self._has_white else (0, 0, 0))
                self._pixels.show()
                self._pixels.deinit()
            except Exception:
                pass  # Ignore cleanup errors
            finally:
                self._pixels = None

    @staticmethod
    def is_available() -> bool:
        """
        Check if the Adafruit NeoPixel PWM backend is available.

        Returns:
            True if backend dependencies are installed
        """
        return ADAFRUIT_AVAILABLE
