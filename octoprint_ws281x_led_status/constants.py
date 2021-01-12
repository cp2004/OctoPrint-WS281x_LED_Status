# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

import rpi_ws281x
from octoprint.events import Events

from octoprint_ws281x_led_status.effects import standard, progress


PI_REGEX = r"Raspberry Pi (\w*)"
PROC_DT_MODEL_PATH = "/proc/device-tree/model"

BLOCKING_TEMP_GCODES = [
    "M109",
    "M190",
]  # TODO make configurable? No one has complained about it yet...

ON_AT_COMMAND = "WS_LIGHTSON"
OFF_AT_COMMAND = "WS_LIGHTSOFF"
TORCH_AT_COMMAND = "WS_TORCH"
TORCH_ON_AT_COMMAND = "WS_TORCH_ON"
TORCH_OFF_AT_COMMAND = "WS_TORCH_OFF"
AT_COMMANDS = [
    ON_AT_COMMAND,
    OFF_AT_COMMAND,
    TORCH_AT_COMMAND,
    TORCH_ON_AT_COMMAND,
    TORCH_OFF_AT_COMMAND,
]

STANDARD_EFFECT_NICE_NAMES = {
    "Solid Color": "solid",
    "Color Wipe": "wipe",
    "Color Wipe 2": "wipe2",
    "Pulse": "pulse",
    "Bounce": "bounce",
    "Bounce Solo": "bounce_solo",
    "Rainbow": "rainbow",
    "Rainbow Cycle": "cycle",
    "Random": "random",
    "Blink": "blink",
    "Crossover": "cross",
    "Bouncy Balls": "balls",
}

SUPPORTED_EVENTS = {
        Events.CONNECTED: "idle",
        Events.DISCONNECTED: "disconnected",
        Events.PRINT_FAILED: "failed",
        Events.PRINT_DONE: "success",
        Events.PRINT_PAUSED: "paused",
    }

KILL_MSG = "KILL"
STRIP_SETTINGS = [  # ALL LED SETTINGS, for rpi_ws281x.PixelStrip
    "led_count",
    "led_pin",
    "led_freq_hz",
    "led_dma",
    "led_invert",
    "led_brightness",
    "led_channel",
    "strip_type",
    "reverse",
]
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
    "solid": standard.solid_color,
    "wipe": standard.color_wipe,
    "wipe2": standard.color_wipe_2,
    "pulse": standard.simple_pulse,
    "rainbow": standard.rainbow,
    "cycle": standard.rainbow_cycle,
    "bounce": standard.bounce,
    "bounce_solo": standard.solo_bounce,
    "random": standard.random_single,
    "blink": standard.blink,
    "cross": standard.crossover,
    "balls": standard.bouncy_balls,
    "progress_print": progress.progress,
    "progress_heatup": progress.progress,
    "progress_cooling": progress.progress,
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
