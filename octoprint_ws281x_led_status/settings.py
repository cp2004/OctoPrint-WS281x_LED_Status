# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

__author__ = "Charlie Powell <cp2004.github@gmail.com"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Charlie Powell 2020-2021 - released under the terms of the AGPLv3 License"

# noinspection PyPackageRequirements
from octoprint.util import dict_merge

VERSION = 1

defaults = {
    "strip": {
        "count": 24,
        "pin": 10,
        "freq_hz": 800000,
        "dma": 10,
        "invert": False,
        "channel": 0,
        "reverse": False,
        "type": "WS2811_STRIP_GRB",
        "brightness": 50,
        "adjustment": {"R": 100, "G": 100, "B": 100},
        "white_override": False,
        "white_brightness": 50,
    },
    "effects": {
        "startup": {
            "enabled": True,
            "effect": "Color Wipe",
            "color": "#00ff00",
            "delay": "75",
        },
        "idle": {
            "enabled": True,
            "effect": "Color Wipe 2",
            "color": "#00ff00",
            "delay": "75",
        },
        "disconnected": {
            "enabled": True,
            "effect": "Rainbow Cycle",
            "color": "#000000",
            "delay": "25",
        },
        "failed": {
            "enabled": True,
            "effect": "Pulse",
            "color": "#ff0000",
            "delay": 10,
        },
        "success": {
            "enabled": True,
            "effect": "Rainbow",
            "color": "#000000",
            "delay": "25",
            "return_to_idle": "0",
        },
        "paused": {
            "enabled": True,
            "effect": "Bounce",
            "color": "#0000ff",
            "delay": "40",
        },
        "printing": {
            "enabled": False,
            "effect": "Solid Color",
            "color": "#ffffff",
            "delay": "1",
        },
        "torch": {
            "enabled": True,
            "effect": "Solid Color",
            "color": "#ffffff",
            "delay": "1",
            "toggle": False,
            "timer": "15",
            "auto_on_webcam": True,
        },
        "progress_print": {
            "enabled": True,
            "base": "#000000",
            "color": "#00ff00",
            "effect": "Progress Bar",
        },
        "progress_heatup": {
            "enabled": True,
            "base": "#0000ff",
            "color": "#ff0000",
            "tool_enabled": True,
            "bed_enabled": True,
            "tool_key": 0,
            "effect": "Progress Bar",
        },
        "progress_cooling": {
            "enabled": True,
            "base": "#0000ff",
            "color": "#ff0000",
            "bed_or_tool": "tool",
            "threshold": 40,
            "effect": "Progress Bar",
        },
    },
    "active_times": {
        "enabled": False,
        "start": "09:00",
        "end": "21:00",
    },
    "transitions": {
        "fade": {
            "enabled": True,
            "time": 1000,
        }
    },
    "progress_temp_start": 0,
    "at_command_reaction": True,
    "intercept_m150": True,
    "debug_logging": False,
}


def migrate_settings(target, current, settings):
    if current is None and target is not None:
        # None => 1
        migrate_none_to_one(settings)


def migrate_none_to_one(settings):
    new_settings = {
        "strip": {
            "count": settings.get_int(["led_count"]),
            "pin": settings.get_int(["led_pin"]),
            "freq_hz": settings.get_int(["led_freq_hz"]),
            "dma": settings.get_int(["led_dma"]),
            "invert": settings.get_boolean(["led_invert"]),
            "channel": settings.get_int(["led_channel"]),
            "reverse": settings.get_boolean(["reverse"]),
            "type": settings.get(["strip_type"]),
            "brightness": settings.get(["brightness"]),
        },
        "effects": {
            "startup": {
                "enabled": settings.get_boolean(["startup_enabled"]),
                "effect": settings.get(["startup_effect"]),
                "color": settings.get(["startup_color"]),
                "delay": settings.get(["startup_delay"]),
            },
            "idle": {
                "enabled": settings.get_boolean(["idle_enabled"]),
                "effect": settings.get(["idle_effect"]),
                "color": settings.get(["idle_color"]),
                "delay": settings.get(["idle_delay"]),
            },
            "disconnected": {
                "enabled": settings.get_boolean(["disconnected_enabled"]),
                "effect": settings.get(["disconnected_effect"]),
                "color": settings.get(["disconnected_color"]),
                "delay": settings.get(["disconnected_delay"]),
            },
            "failed": {
                "enabled": settings.get_boolean(["failed_enabled"]),
                "effect": settings.get(["failed_effect"]),
                "color": settings.get(["failed_color"]),
                "delay": settings.get(["failed_delay"]),
            },
            "success": {
                "enabled": settings.get_boolean(["success_enabled"]),
                "effect": settings.get(["success_effect"]),
                "color": settings.get(["success_color"]),
                "delay": settings.get(["success_delay"]),
                "return_to_idle": settings.get(["success_return_idle"]),
            },
            "paused": {
                "enabled": settings.get_boolean(["paused_enabled"]),
                "effect": settings.get(["paused_effect"]),
                "color": settings.get(["paused_color"]),
                "delay": settings.get(["paused_delay"]),
            },
            "printing": {
                "enabled": settings.get_boolean(["printing_enabled"]),
                "effect": settings.get(["printing_effect"]),
                "color": settings.get(["printing_color"]),
                "delay": settings.get(["printing_delay"]),
            },
            "torch": {
                "enabled": settings.get_boolean(["torch_enabled"]),
                "effect": settings.get(["torch_effect"]),
                "color": settings.get(["torch_color"]),
                "delay": settings.get(["torch_delay"]),
                "toggle": settings.get(["torch_toggle"]),
                "timer": settings.get_int(["torch_timer"]),
            },
            "progress_print": {
                "enabled": settings.get_boolean(["progress_print_enabled"]),
                "base": settings.get(["progress_print_color_base"]),
                "color": settings.get(["progress_print_color"]),
            },
            "progress_heatup": {
                "enabled": settings.get_boolean(["progress_heatup_enabled"]),
                "base": settings.get(["progress_heatup_color_base"]),
                "color": settings.get(["progress_heatup_color"]),
                "tool_enabled": settings.get_boolean(["progress_heatup_tool_enabled"]),
                "bed_enabled": settings.get_boolean(["progress_heatup_bed_enabled"]),
                "tool_key": settings.get_int(["progress_heatup_tool_key"]),
            },
            "progress_cooling": {
                "enabled": settings.get_boolean(["progress_cooling_enabled"]),
                "base": settings.get(["progress_cooling_color_base"]),
                "color": settings.get(["progress_cooling_color"]),
                "bed_or_tool": settings.get(["progress_cooling_bed_or_tool"]),
                "threshold": settings.get_int(["progress_cooling_threshold"]),
            },
        },
        "active_times": {
            "enabled": settings.get(["active_hours_enabled"]),
            "start": settings.get(["active_hours_start"]),
            "end": settings.get(["active_hours_end"]),
        },
    }
    # Filter out None values
    filtered = filter_none(new_settings)
    # Merge with default settings that were not set
    result = dict_merge(defaults, filtered)
    # SAVE!
    settings.global_set(["plugins", "ws281x_led_status"], result)


def filter_none(target):
    """
    Recursively remove any key/value pairs where the value is None
    :param target: (dict) Target dict to filter
    :return result: (dict) Filtered dict with no None values
    """
    result = {}
    for k, v in target.items():
        if isinstance(v, dict):
            result[k] = filter_none(v)
        else:
            if v is not None:
                result[k] = v
    return result
