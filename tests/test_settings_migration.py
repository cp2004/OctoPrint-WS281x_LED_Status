__author__ = "Jason Antman <jason@jasonantman.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Jason Antman 2025 - released under the terms of the AGPLv3 License"

import unittest
from typing import Any, Dict
from unittest import mock

from octoprint_ws281x_led_status.settings import (
    migrate_three_to_four,
    filter_none,
)


class MockSettingsData:
    """Mock OctoPrint settings data object with remove() method."""

    def __init__(self, data: Dict[str, Any]) -> None:
        self._data = data

    def remove(self, path: list) -> None:
        """Remove a setting by path."""
        current = self._data
        for key in path[:-1]:
            if key in current:
                current = current[key]
            else:
                return
        if path[-1] in current:
            del current[path[-1]]

    def get_dict(self) -> Dict[str, Any]:
        """Get the underlying dictionary."""
        return self._data


class MockSettings:
    """Mock OctoPrint settings object for testing migrations."""

    def __init__(self, initial_settings: Dict[str, Any]) -> None:
        # Store settings at the plugin level (without plugins/ws281x_led_status prefix)
        self._data = initial_settings
        # But settings.remove() expects the full path with plugins/ws281x_led_status
        self._full_data = {"plugins": {"ws281x_led_status": self._data}}
        self.settings = MockSettingsData(self._full_data)

    def get(self, path: list, merged: bool = False) -> Any:
        """Get a setting value by path."""
        current = self._data
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current

    def set(self, path: list, value: Any) -> None:
        """Set a setting value by path."""
        current = self._data
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value


class TestSettingsMigrationV3toV4(unittest.TestCase):
    """Test settings migration from version 3 to version 4."""

    def test_migrate_backend_settings(self):
        """Test that backend settings are moved to backend section."""
        settings = MockSettings({
            "strip": {
                "count": 50,
                "brightness": 75,
                "pin": 10,
                "freq_hz": 800000,
                "dma": 10,
                "invert": False,
                "channel": 0,
                "type": "WS2811_STRIP_GRB",
                "adjustment": {"R": 100, "G": 100, "B": 100},
                "white_override": False,
                "white_brightness": 50,
            }
        })

        migrate_three_to_four(settings)

        # Check backend section was created
        backend = settings.get(["backend"])
        self.assertIsNotNone(backend)
        self.assertEqual(backend["type"], "rpi_ws281x")

        # Check backend-specific settings were moved
        backend_config = backend["config"]
        self.assertEqual(backend_config["count"], 50)
        self.assertEqual(backend_config["brightness"], 75)
        self.assertEqual(backend_config["pin"], 10)
        self.assertEqual(backend_config["freq_hz"], 800000)
        self.assertEqual(backend_config["dma"], 10)
        self.assertEqual(backend_config["invert"], False)
        self.assertEqual(backend_config["channel"], 0)
        self.assertEqual(backend_config["type"], "WS2811_STRIP_GRB")

        # Check backend-agnostic settings remain in strip
        strip = settings.get(["strip"])
        self.assertIn("adjustment", strip)
        self.assertEqual(strip["adjustment"]["R"], 100)
        self.assertIn("white_override", strip)
        self.assertIn("white_brightness", strip)

        # Check backend-specific settings were removed from strip
        self.assertNotIn("count", strip)
        self.assertNotIn("brightness", strip)
        self.assertNotIn("pin", strip)
        self.assertNotIn("freq_hz", strip)
        self.assertNotIn("dma", strip)
        self.assertNotIn("invert", strip)
        self.assertNotIn("channel", strip)
        self.assertNotIn("type", strip)

    def test_migrate_with_missing_settings(self):
        """Test migration handles missing settings gracefully."""
        settings = MockSettings({
            "strip": {
                "count": 24,
                "adjustment": {"R": 100, "G": 100, "B": 100},
            }
        })

        migrate_three_to_four(settings)

        # Should create backend section even with minimal settings
        backend = settings.get(["backend"])
        self.assertIsNotNone(backend)
        self.assertEqual(backend["type"], "rpi_ws281x")

        # Only count should be in config (other values were None and filtered)
        backend_config = backend["config"]
        self.assertEqual(backend_config["count"], 24)

    def test_migrate_with_all_none_uses_defaults(self):
        """Test migration uses defaults when all strip settings are None."""
        from octoprint_ws281x_led_status.settings import defaults

        # Simulate a fresh install or completely empty strip config
        settings = MockSettings({
            "strip": {
                "adjustment": {"R": 100, "G": 100, "B": 100},
            }
        })

        migrate_three_to_four(settings)

        # Should create backend section with defaults, not empty config
        backend = settings.get(["backend"])
        self.assertIsNotNone(backend)
        self.assertEqual(backend["type"], "rpi_ws281x")

        # Backend config should have default values, not be empty
        backend_config = backend["config"]
        self.assertIsNotNone(backend_config)
        self.assertGreater(len(backend_config), 0, "Backend config should not be empty")

        # Should have all the default backend config values
        self.assertEqual(backend_config["count"], defaults["backend"]["config"]["count"])
        self.assertEqual(backend_config["brightness"], defaults["backend"]["config"]["brightness"])
        self.assertEqual(backend_config["pin"], defaults["backend"]["config"]["pin"])

    def test_migrate_preserves_non_backend_settings(self):
        """Test that non-backend settings are not affected."""
        settings = MockSettings({
            "strip": {
                "count": 24,
                "brightness": 50,
                "adjustment": {"R": 90, "G": 95, "B": 100},
                "white_override": True,
                "white_brightness": 60,
            },
            "effects": {
                "startup": {
                    "enabled": True,
                    "effect": "Color Wipe",
                }
            },
            "features": {
                "sacrifice_pixel": True,
            }
        })

        migrate_three_to_four(settings)

        # Check that effects and features were not modified
        effects = settings.get(["effects"])
        self.assertIsNotNone(effects)
        self.assertTrue(effects["startup"]["enabled"])

        features = settings.get(["features"])
        self.assertIsNotNone(features)
        self.assertTrue(features["sacrifice_pixel"])


class TestFilterNone(unittest.TestCase):
    """Test the filter_none utility function."""

    def test_filter_simple_dict(self):
        """Test filtering None from simple dict."""
        input_dict = {
            "a": 1,
            "b": None,
            "c": "value",
            "d": None,
        }
        result = filter_none(input_dict)

        self.assertEqual(result, {"a": 1, "c": "value"})
        self.assertNotIn("b", result)
        self.assertNotIn("d", result)

    def test_filter_nested_dict(self):
        """Test filtering None from nested dict."""
        input_dict = {
            "a": 1,
            "b": {
                "x": None,
                "y": 2,
                "z": None,
            },
            "c": None,
        }
        result = filter_none(input_dict)

        self.assertEqual(result["a"], 1)
        self.assertNotIn("c", result)
        self.assertEqual(result["b"]["y"], 2)
        self.assertNotIn("x", result["b"])
        self.assertNotIn("z", result["b"])

    def test_filter_empty_result(self):
        """Test that all None values results in empty dict."""
        input_dict = {
            "a": None,
            "b": None,
        }
        result = filter_none(input_dict)

        self.assertEqual(result, {})

    def test_filter_preserves_zero_and_false(self):
        """Test that 0 and False are not filtered (only None)."""
        input_dict = {
            "a": 0,
            "b": False,
            "c": "",
            "d": None,
        }
        result = filter_none(input_dict)

        self.assertIn("a", result)
        self.assertEqual(result["a"], 0)
        self.assertIn("b", result)
        self.assertEqual(result["b"], False)
        self.assertIn("c", result)
        self.assertEqual(result["c"], "")
        self.assertNotIn("d", result)


if __name__ == "__main__":
    unittest.main()
