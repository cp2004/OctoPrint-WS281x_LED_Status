__author__ = "Charlie Powell <cp2004.github@gmail.com"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Charlie Powell 2020-2021 - released under the terms of the AGPLv3 License"

from typing import Any, Dict, List, Optional, Tuple

from octoprint_ws281x_led_status.backend import LEDBackend


class SegmentManager:
    def __init__(self, strip: LEDBackend, settings: List[Dict[str, int]]) -> None:
        self.strip: LEDBackend = strip
        self.settings: List[Dict[str, int]] = settings
        self.segments: List[Dict[str, Any]] = []

    def create_segments(self) -> None:
        segments: List[Dict[str, Any]] = []
        for segment_config in self.settings:
            segment = {
                "id": len(segments) + 1,  # Check order is guaranteed...
                "class": StripSegment(
                    self.strip, segment_config["start"], end=segment_config["end"]
                ),
            }
            segments.append(segment)

        self.segments = segments

    def get_segment(self, segment_id: int) -> "StripSegment":
        # There should only be one segment with given id, so use first of filtered list
        return list(filter(lambda x: x["id"] == segment_id, self.segments))[0]["class"]

    def list_segments(self) -> List[Dict[str, Any]]:
        return self.segments


class StripSegment:
    def __init__(
        self,
        strip: LEDBackend,
        start: int,
        num: Optional[int] = None,
        end: Optional[int] = None,
    ) -> None:
        # Bunch of validations to make sure this is viable
        if end is not None and end < start:
            raise InvalidSegmentError("Segment cannot end before it starts")

        if (num is not None and num <= 0) or (end is not None and end - start <= 0):
            raise InvalidSegmentError("Segment must be longer than 0")

        if num is not None:
            self.num_pixels: int = num
        elif end is not None:
            self.num_pixels = end - start
        else:
            raise InvalidSegmentError("Number of pixels and end cannot both be None")

        self.strip: LEDBackend = strip
        self.start: int = start

        # Functions that map 1:1
        # TODO some sort of resource lock/management here? Or just assume we will be fast enough...
        self.show = self.strip.show
        self.getBrightness = self.strip.get_brightness

    def numPixels(self) -> int:
        return self.num_pixels

    def setPixelColor(self, index: int, color: int) -> None:
        self.strip.set_pixel_color(index + self.start, color)

    def setPixelColorRGB(self, index: int, r: int, g: int, b: int, w: int = 0) -> None:
        self.strip.set_pixel_color_rgb(index + self.start, r, g, b, w)

    def getPixels(self) -> None:
        raise NotImplementedError

    def getPixelColor(self, index: int) -> int:
        return self.strip.get_pixel_color(index + self.start)

    def getPixelColorRGB(self, index: int) -> Tuple[int, int, int, int]:
        return self.strip.get_pixel_color_rgb(index + self.start)

    def getPixelColorRGBW(self, index: int) -> Tuple[int, int, int, int]:
        return self.strip.get_pixel_color_rgb(index + self.start)


class InvalidSegmentError(Exception):
    pass
