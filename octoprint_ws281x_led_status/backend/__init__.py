__author__ = "Jason Antman <jason@jasonantman.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Jason Antman 2025 - released under the terms of the AGPLv3 License"

from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple


class LEDBackend(ABC):
    """
    Abstract base class for LED strip backends.

    This interface defines the contract that all LED strip control backends
    must implement. It provides a hardware-agnostic API for controlling
    WS281x-compatible LED strips.

    Backends are responsible for:
    - Initializing the LED hardware
    - Managing pixel colors and brightness
    - Updating the physical LEDs with buffered changes
    - Cleaning up resources on shutdown
    """

    @abstractmethod
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the backend with configuration.

        Args:
            config (dict): Backend-specific configuration dictionary.
                Must include at minimum:
                - count (int): Number of LEDs in the strip
                Additional keys depend on the specific backend implementation.
        """
        pass

    @abstractmethod
    def begin(self) -> None:
        """
        Initialize the LED hardware.

        This method should be called once after construction to set up
        the hardware and prepare it for use. It may raise exceptions if
        hardware initialization fails.

        Raises:
            RuntimeError: If hardware initialization fails
        """
        pass

    @abstractmethod
    def show(self) -> None:
        """
        Update the LED strip with buffered pixel colors.

        This method sends the current pixel buffer to the physical LEDs,
        making any color changes visible. It should be called after setting
        pixel colors to apply the changes.
        """
        pass

    @abstractmethod
    def set_brightness(self, value: int) -> None:
        """
        Set the global brightness level for all LEDs.

        Args:
            value (int): Brightness value from 0 (off) to 255 (maximum brightness)
        """
        pass

    @abstractmethod
    def get_brightness(self) -> int:
        """
        Get the current global brightness level.

        Returns:
            int: Current brightness value from 0 to 255
        """
        pass

    @abstractmethod
    def num_pixels(self) -> int:
        """
        Get the number of pixels in the strip.

        Returns:
            int: Number of LEDs in the strip
        """
        pass

    @abstractmethod
    def set_pixel_color(self, index: int, color: int) -> None:
        """
        Set a pixel's color using a packed 32-bit integer.

        The color format is 0xWWRRGGBB where:
        - WW = white channel (bits 24-31)
        - RR = red channel (bits 16-23)
        - GG = green channel (bits 8-15)
        - BB = blue channel (bits 0-7)

        For RGB strips, the white channel is ignored.

        Args:
            index (int): Pixel index (0-based)
            color (int): 32-bit packed color value
        """
        pass

    @abstractmethod
    def set_pixel_color_rgb(self, index: int, r: int, g: int, b: int, w: int = 0) -> None:
        """
        Set a pixel's color using separate R, G, B, W values.

        Args:
            index (int): Pixel index (0-based)
            r (int): Red value (0-255)
            g (int): Green value (0-255)
            b (int): Blue value (0-255)
            w (int, optional): White value (0-255), defaults to 0
        """
        pass

    @abstractmethod
    def get_pixel_color(self, index: int) -> int:
        """
        Get a pixel's color as a packed 32-bit integer.

        Returns:
            int: 32-bit packed color in 0xWWRRGGBB format
        """
        pass

    @abstractmethod
    def get_pixel_color_rgb(self, index: int) -> Tuple[int, int, int, int]:
        """
        Get a pixel's color as separate R, G, B, W values.

        Returns:
            tuple: (r, g, b, w) where each value is 0-255
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """
        Clean up resources and reset the hardware.

        This method should be called before shutting down to ensure
        proper cleanup of hardware resources, GPIO pins, etc.
        """
        pass


def color_rgb_to_packed(r: int, g: int, b: int, w: int = 0) -> int:
    """
    Convert separate R, G, B, W values to a packed 32-bit color.

    Args:
        r (int): Red value (0-255)
        g (int): Green value (0-255)
        b (int): Blue value (0-255)
        w (int, optional): White value (0-255), defaults to 0

    Returns:
        int: Packed 32-bit color in 0xWWRRGGBB format
    """
    return (int(w) << 24) | (int(r) << 16) | (int(g) << 8) | int(b)


def color_packed_to_rgb(color: int) -> Tuple[int, int, int, int]:
    """
    Convert a packed 32-bit color to separate R, G, B, W values.

    Args:
        color (int): Packed 32-bit color in 0xWWRRGGBB format

    Returns:
        tuple: (r, g, b, w) where each value is 0-255
    """
    w = (color >> 24) & 0xFF
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    return (r, g, b, w)


def validate_pixel_index(index: int, num_pixels: int) -> None:
    """
    Validate that a pixel index is within valid range.

    Args:
        index (int): Pixel index to validate
        num_pixels (int): Total number of pixels in strip

    Raises:
        IndexError: If index is out of range
    """
    if not isinstance(index, int):
        raise TypeError(f"Pixel index must be an integer, got {type(index)}")
    if index < 0 or index >= num_pixels:
        raise IndexError(
            f"Pixel index {index} out of range (0-{num_pixels - 1})"
        )


def validate_color_value(value: Any, name: str = "color") -> None:
    """
    Validate that a color component value is in valid range.

    Args:
        value: Value to validate
        name (str): Name of the component for error messages

    Raises:
        ValueError: If value is out of range
        TypeError: If value is not an integer
    """
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an integer, got {type(value)}")
    if value < 0 or value > 255:
        raise ValueError(f"{name} must be in range 0-255, got {value}")
