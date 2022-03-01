__author__ = "Charlie Powell <cp2004.github@gmail.com"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Charlie Powell 2020-2021 - released under the terms of the AGPLv3 License"


class SegmentManager:
    def __init__(self, strip, settings):
        self.strip = strip
        self.settings = settings
        self.segments = []

    def create_segments(self):
        segments = []
        for segment_config in self.settings:
            segment = {
                "id": len(self.segments) + 1,  # Check order is guaranteed...
                "class": StripSegment(
                    self.strip, segment_config["start"], end=segment_config["end"]
                ),
            }
            segments.append(segment)

        self.segments = segments

    def get_segment(self, segment_id):
        # There should only be one segment with given id, so use first of filtered list
        return list(filter(lambda x: x["id"] == segment_id, self.segments))[0]["class"]

    def list_segments(self):
        return self.segments


class StripSegment:
    def __init__(self, strip, start, num=None, end=None):
        # Bunch of validations to make sure this is viable
        if end < start:
            raise InvalidSegmentError("Segment cannot end before it starts")

        if (num is not None and num <= 0) or (end is not None and end - start <= 0):
            raise InvalidSegmentError("Segment must be longer than 0")

        if num is not None:
            self.num_pixels = num
        elif end is not None:
            self.num_pixels = end - start
        else:
            raise InvalidSegmentError("Number of pixels and end cannot both be None")

        self.strip = strip
        self.start = start

        # Functions that map 1:1
        # TODO some sort of resource lock/management here? Or just assume we will be fast enough...
        self.show = self.strip.show
        self.getBrightness = self.strip.getBrightness

    def numPixels(self):
        return self.num_pixels

    def setPixelColor(self, index, color):
        self.strip.setPixelColor(index + self.start, color)

    def setPixelColorRGB(self, index, r, g, b, w=0):
        self.strip.setPixelColorRGB(index + self.start, r, g, b, w)

    def getPixels(self):
        raise NotImplementedError

    def getPixelColor(self, index):
        return self.strip.getPixelColor(index + self.start)

    def getPixelColorRGB(self, index):
        self.strip.getPixelColorRGB(index + self.start)

    def getPixelColorRGBW(self, index):
        self.strip.getPixelColorRGBW(index + self.start)


class InvalidSegmentError(Exception):
    pass
