from typing import Tuple, Optional

import socket


class WLEDStrip:
    """Emulates the PixelStrip class provided by rpi-ws281x but instead of
    outputing data to a local LED strip, it outputs data over UDP to WLED."""

    # Magic bytes for WLED, specifies DRGB mode with a 5 second return delay.
    _CONTROL_BYTES: bytes

    # Number of pixels to control
    _numPixels: int
    # If RGBW values are buffered and sent to WLED
    _enableRGBW = False

    # Address of WLED instance's UDP realtime control
    _addr: Tuple[str, int]
    # Socket used to connect to WLED
    _socket: socket.socket

    # Buffer of LED values to allow selective updates
    _pixel_buffer: bytearray

    def __init__(
        self,
        numPixels: int,
        host: str,
        port: int = 21324,
        enableRGBW: bool = False,
    ):
        self._numPixels = numPixels
        self._enableRGBW = enableRGBW

        self._addr = (host, port)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.settimeout(1.0)

        if enableRGBW:
            self._CONTROL_BYTES = bytes([3, 255])
        else:
            self._CONTROL_BYTES = bytes([2, 255])

        self._pixel_buffer = bytearray(
            self._CONTROL_BYTES + bytes([0] * numPixels * self.bytesPerPixel)
        )

    @property
    def bytesPerPixel(self) -> int:
        """The number of bytes required to store each pixel.

        This value is typically 3, but can be 4 if RGBW mode is enabled."""
        return 4 if self._enableRGBW else 3

    @property
    def _pixelDataOffset(self) -> int:
        """The offset in the data buffer to hold the control bytes."""
        return len(self._CONTROL_BYTES)

    def begin(self):
        """Initialize the strip by displaying the buffer."""
        self.show()

    def numPixels(self):
        """The number of pixels in the LED strip."""
        return self._numPixels

    def setBrightness(self, brightness: int):
        """Control brightness for all pixels, currently not implemented."""
        pass

    def setPixelColorRGB(
        self, index: int, red: int, green: int, blue: int, white: Optional[int] = None
    ):
        """Set the color of a single pixel at a specific index."""
        if index > self._numPixels:
            raise Exception("Invalid index")

        if white:
            if not self._enableRGBW:
                raise Exception("White value was provided but RGBW was not enabled")

            data = [red, green, blue, white]
        else:
            data = [red, green, blue]

        start = self._pixelDataOffset + index * self.bytesPerPixel
        self._pixel_buffer[start : start + self.bytesPerPixel] = data

    def show(self):
        """Send the buffer to the strip."""
        self._socket.sendto(self._pixel_buffer, self._addr)
