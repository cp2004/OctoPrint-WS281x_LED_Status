# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

import re

import rpi_ws281x

# noinspection PyPackageRequirements
from octoprint.events import Events

from octoprint_ws281x_led_status.effects import progress, standard

PI_REGEX = r"Raspberry Pi (\w*)"
PROC_DT_MODEL_PATH = "/proc/device-tree/model"

BLOCKING_TEMP_GCODES = {
    "M109": "tool",
    "M190": "bed",
}

ON_AT_COMMAND = "WS_LIGHTSON"
OFF_AT_COMMAND = "WS_LIGHTSOFF"
TORCH_AT_COMMAND = "WS_TORCH"
TORCH_ON_AT_COMMAND = "WS_TORCH_ON"
TORCH_OFF_AT_COMMAND = "WS_TORCH_OFF"


SUPPORTED_EVENTS = {
    Events.CONNECTED: "idle",
    Events.DISCONNECTED: "disconnected",
    Events.PRINT_FAILED: "failed",
    Events.PRINT_DONE: "success",
    Events.PRINT_PAUSED: "paused",
}

KILL_MSG = "KILL"

STRIP_TYPES = {
    "WS2811_STRIP_GRB": rpi_ws281x.WS2811_STRIP_GRB,
    "WS2812_STRIP": rpi_ws281x.WS2812_STRIP,
    "WS2811_STRIP_RGB": rpi_ws281x.WS2811_STRIP_RGB,
    "WS2811_STRIP_RBG": rpi_ws281x.WS2811_STRIP_RBG,
    "WS2811_STRIP_GBR": rpi_ws281x.WS2811_STRIP_GBR,
    "WS2811_STRIP_BGR": rpi_ws281x.WS2811_STRIP_BGR,
    "WS2811_STRIP_BRG": rpi_ws281x.WS2811_STRIP_BRG,
    "SK6812_STRIP": rpi_ws281x.SK6812_STRIP,
    "SK6812W_STRIP": rpi_ws281x.SK6812W_STRIP,
    "SK6812_STRIP_RGBW": rpi_ws281x.SK6812_STRIP_RGBW,
    "SK6812_STRIP_RBGW": rpi_ws281x.SK6812_STRIP_RBGW,
    "SK6812_STRIP_GRBW": rpi_ws281x.SK6812_STRIP_GRBW,
    "SK6812_STRIP_GBRW": rpi_ws281x.SK6812_STRIP_GBRW,
    "SK6812_STRIP_BRGW": rpi_ws281x.SK6812_STRIP_BRGW,
    "SK6812_STRIP_BGRW": rpi_ws281x.SK6812_STRIP_BGRW,
}
EFFECTS = {
    "Solid Color": standard.solid_color,
    "Color Wipe": standard.color_wipe,
    "Color Wipe 2": standard.color_wipe_2,
    "Pulse": standard.simple_pulse,
    "Bounce": standard.bounce,
    "Bounce Solo": standard.solo_bounce,
    "Rainbow": standard.rainbow,
    "Rainbow Cycle": standard.rainbow_cycle,
    "Random": standard.random_single,
    "Blink": standard.blink,
    "Crossover": standard.crossover,
    "Bouncy Balls": standard.bouncy_balls,
    "progress_heatup": progress.progress,
    "progress_cooling": progress.progress,
    "progress_print": progress.progress,
}
MODES = [
    "startup",
    "idle",
    "disconnected",
    "progress_print",
    "progress_heatup",
    "progress_cooling",
    "failed",
    "success",
    "paused",
    "printing",
    "torch",
]

# Example command: M150 R10 G200 B300
# more => https://github.com/cp2004/OctoPrint-WS281x_LED_Status/wiki/Features#m150-intercept
regex_r_param = re.compile(r"(^|[^A-Za-z])[Rr](?P<value>\d{1,3})")
regex_g_param = re.compile(r"(^|[^A-Za-z])[GgUu](?P<value>\d{1,3})")
regex_b_param = re.compile(r"(^|[^A-Za-z])[Bb](?P<value>\d{1,3})")
regex_w_param = re.compile(r"(^|[^A-Za-z])[Ww](?P<value>\d{1,3})")
regex_p_param = re.compile(r"(^|[^A-Za-z])[Pp](?P<value>\d{1,3})")
