__author__ = "Jason Antman <jason@jasonantman.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Jason Antman 2025 - released under the terms of the AGPLv3 License"

from typing import Any, Dict, Tuple

from rpi_ws281x import PixelStrip

from octoprint_ws281x_led_status import constants
from octoprint_ws281x_led_status.backend import LEDBackend


class RpiWS281xBackend(LEDBackend):
    """
    Backend implementation using the rpi_ws281x library.

    This backend wraps the rpi_ws281x.PixelStrip class to provide LED control
    on Raspberry Pi 3, 4, and older models using PWM or PCM.

    OS Requirements:
        - User must be in 'gpio' group
        - SPI must be enabled in /boot/config.txt
        - SPI buffer size increase recommended (spidev.bufsiz=32768 in /boot/cmdline.txt)
        - Core frequency settings required for Pi 3 (core_freq=250) and Pi 4 (core_freq_min=500)

    IMPORTANT: Wizard test requirements for this backend are defined in:
        octoprint_ws281x_led_status/wizard.py::BACKEND_TEST_REQUIREMENTS["rpi_ws281x"]
    If you modify the OS requirements for this backend, update the wizard tests accordingly.

    Configuration keys:
        count (int): Number of LEDs in the strip
        pin (int): GPIO pin connected to the strip (default: 10)
        freq_hz (int): LED signal frequency in Hz (default: 800000)
        dma (int): DMA channel to use (default: 10)
        invert (bool): Invert the signal (default: False)
        brightness (int): Initial brightness 0-100% (default: 100)
        channel (int): PWM channel (default: 0)
        type (str): Strip type string (e.g., "WS2811_STRIP_GRB")
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the rpi_ws281x backend.

        Args:
            config: Backend configuration dictionary
        """
        self.config = config
        self._strip: PixelStrip = None  # type: ignore
        self._num_pixels: int = int(config["count"])

        # Extract configuration with defaults
        self._pin = int(config.get("pin", 10))
        self._freq_hz = int(config.get("freq_hz", 800000))
        self._dma = int(config.get("dma", 10))
        self._invert = bool(config.get("invert", False))
        self._channel = int(config.get("channel", 0))

        # Brightness is stored as 0-100 percentage in config, convert to 0-255
        brightness_percent = int(config.get("brightness", 100))
        self._brightness = int((brightness_percent / 100.0) * 255)

        # Map strip type string to rpi_ws281x constant
        strip_type_str = config.get("type", "WS2811_STRIP_GRB")
        if strip_type_str not in constants.STRIP_TYPES:
            raise ValueError(
                f"Unknown strip type: {strip_type_str}. "
                f"Valid types: {list(constants.STRIP_TYPES.keys())}"
            )
        self._strip_type = constants.STRIP_TYPES[strip_type_str]

    def begin(self) -> None:
        """
        Initialize the LED hardware.

        Creates the PixelStrip instance and initializes it.

        Raises:
            RuntimeError: If hardware initialization fails
        """
        try:
            self._strip = PixelStrip(
                num=self._num_pixels,
                pin=self._pin,
                freq_hz=self._freq_hz,
                dma=self._dma,
                invert=self._invert,
                brightness=self._brightness,
                channel=self._channel,
                strip_type=self._strip_type,
            )
            self._strip.begin()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize rpi_ws281x strip: {e}") from e

    def show(self) -> None:
        """Update the LED strip with buffered pixel colors."""
        self._strip.show()

    def set_brightness(self, value: int) -> None:
        """
        Set the global brightness level for all LEDs.

        Args:
            value: Brightness value from 0 (off) to 255 (maximum brightness)
        """
        self._brightness = int(value)
        self._strip.setBrightness(self._brightness)

    def get_brightness(self) -> int:
        """
        Get the current global brightness level.

        Returns:
            Current brightness value from 0 to 255
        """
        return self._strip.getBrightness()

    def num_pixels(self) -> int:
        """
        Get the number of pixels in the strip.

        Returns:
            Number of LEDs in the strip
        """
        return self._strip.numPixels()

    def set_pixel_color(self, index: int, color: int) -> None:
        """
        Set a pixel's color using a packed 32-bit integer.

        Args:
            index: Pixel index (0-based)
            color: 32-bit packed color value in 0xWWRRGGBB format
        """
        self._strip.setPixelColor(index, color)

    def set_pixel_color_rgb(self, index: int, r: int, g: int, b: int, w: int = 0) -> None:
        """
        Set a pixel's color using separate R, G, B, W values.

        Args:
            index: Pixel index (0-based)
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)
            w: White value (0-255), defaults to 0
        """
        self._strip.setPixelColorRGB(index, r, g, b, w)

    def get_pixel_color(self, index: int) -> int:
        """
        Get a pixel's color as a packed 32-bit integer.

        Args:
            index: Pixel index (0-based)

        Returns:
            32-bit packed color in 0xWWRRGGBB format
        """
        return self._strip.getPixelColor(index)

    def get_pixel_color_rgb(self, index: int) -> Tuple[int, int, int, int]:
        """
        Get a pixel's color as separate R, G, B, W values.

        Args:
            index: Pixel index (0-based)

        Returns:
            Tuple of (r, g, b, w) where each value is 0-255
        """
        return self._strip.getPixelColorRGBW(index)

    def cleanup(self) -> None:
        """
        Clean up resources and reset the hardware.

        This turns off all LEDs and releases hardware resources.
        """
        if self._strip is not None:
            # Turn off all LEDs
            for i in range(self.num_pixels()):
                self.set_pixel_color(i, 0)
            self.show()
