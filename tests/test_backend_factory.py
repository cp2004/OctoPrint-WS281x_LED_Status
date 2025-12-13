__author__ = "Jason Antman <jason@jasonantman.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Jason Antman 2025 - released under the terms of the AGPLv3 License"

import unittest
from typing import Any, Dict, Tuple

from octoprint_ws281x_led_status.backend import LEDBackend
from octoprint_ws281x_led_status.backend.factory import (
    BackendRegistry,
    create_backend,
    get_available_backends,
    get_registry,
    register_backend,
)


class DummyBackend(LEDBackend):
    """Dummy backend for testing."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.brightness = 255

    def begin(self) -> None:
        pass

    def show(self) -> None:
        pass

    def set_brightness(self, value: int) -> None:
        self.brightness = value

    def get_brightness(self) -> int:
        return self.brightness

    def num_pixels(self) -> int:
        return self.config.get("count", 0)

    def set_pixel_color(self, index: int, color: int) -> None:
        pass

    def set_pixel_color_rgb(
        self, index: int, r: int, g: int, b: int, w: int = 0
    ) -> None:
        pass

    def get_pixel_color(self, index: int) -> int:
        return 0

    def get_pixel_color_rgb(self, index: int) -> Tuple[int, int, int, int]:
        return (0, 0, 0, 0)

    def cleanup(self) -> None:
        pass


class TestBackendRegistry(unittest.TestCase):
    """Test BackendRegistry class."""

    def setUp(self):
        """Create a fresh registry for each test."""
        self.registry = BackendRegistry()

    def test_register_backend(self):
        """Test registering a backend."""
        self.registry.register("dummy", DummyBackend)
        self.assertIn("dummy", self.registry.list_backends())

    def test_register_backend_with_metadata(self):
        """Test registering a backend with display name and description."""
        self.registry.register(
            "dummy",
            DummyBackend,
            display_name="Dummy Backend",
            description="A test backend",
        )

        metadata = self.registry.get_metadata("dummy")
        self.assertEqual(metadata["display_name"], "Dummy Backend")
        self.assertEqual(metadata["description"], "A test backend")

    def test_register_backend_default_display_name(self):
        """Test that display_name defaults to backend name."""
        self.registry.register("dummy", DummyBackend)

        metadata = self.registry.get_metadata("dummy")
        self.assertEqual(metadata["display_name"], "dummy")

    def test_register_duplicate_backend(self):
        """Test that registering duplicate backend raises error."""
        self.registry.register("dummy", DummyBackend)

        with self.assertRaises(ValueError):
            self.registry.register("dummy", DummyBackend)

    def test_register_non_backend_class(self):
        """Test that registering non-backend class raises error."""

        class NotABackend:
            pass

        with self.assertRaises(TypeError):
            self.registry.register("invalid", NotABackend)

    def test_unregister_backend(self):
        """Test unregistering a backend."""
        self.registry.register("dummy", DummyBackend)
        self.assertIn("dummy", self.registry.list_backends())

        self.registry.unregister("dummy")
        self.assertNotIn("dummy", self.registry.list_backends())

    def test_unregister_nonexistent_backend(self):
        """Test that unregistering nonexistent backend raises error."""
        with self.assertRaises(KeyError):
            self.registry.unregister("nonexistent")

    def test_get_backend(self):
        """Test getting a registered backend class."""
        self.registry.register("dummy", DummyBackend)
        backend_class = self.registry.get("dummy")
        self.assertEqual(backend_class, DummyBackend)

    def test_get_nonexistent_backend(self):
        """Test that getting nonexistent backend raises error."""
        with self.assertRaisesRegex(KeyError, "not registered"):
            self.registry.get("nonexistent")

    def test_get_nonexistent_backend_shows_available(self):
        """Test that error message includes available backends."""
        self.registry.register("backend1", DummyBackend)
        self.registry.register("backend2", DummyBackend)

        with self.assertRaisesRegex(KeyError, "backend1, backend2"):
            self.registry.get("nonexistent")

    def test_list_backends(self):
        """Test listing all registered backends."""
        self.registry.register("backend1", DummyBackend)
        self.registry.register("backend2", DummyBackend)

        backends = self.registry.list_backends()
        self.assertIn("backend1", backends)
        self.assertIn("backend2", backends)
        self.assertEqual(len(backends), 2)

    def test_list_backends_empty(self):
        """Test listing backends when none are registered."""
        backends = self.registry.list_backends()
        self.assertEqual(backends, [])

    def test_get_metadata(self):
        """Test getting backend metadata."""
        self.registry.register(
            "dummy", DummyBackend, display_name="Test", description="Testing"
        )

        metadata = self.registry.get_metadata("dummy")
        self.assertEqual(metadata["display_name"], "Test")
        self.assertEqual(metadata["description"], "Testing")

    def test_get_metadata_nonexistent(self):
        """Test that getting metadata for nonexistent backend raises error."""
        with self.assertRaises(KeyError):
            self.registry.get_metadata("nonexistent")

    def test_is_registered(self):
        """Test checking if backend is registered."""
        self.assertFalse(self.registry.is_registered("dummy"))

        self.registry.register("dummy", DummyBackend)
        self.assertTrue(self.registry.is_registered("dummy"))


class TestFactoryFunctions(unittest.TestCase):
    """Test factory functions."""

    def setUp(self):
        """Register a test backend before each test."""
        # Get the global registry and register our test backend
        registry = get_registry()
        if not registry.is_registered("test_dummy"):
            register_backend("test_dummy", DummyBackend, display_name="Test Dummy")

    def tearDown(self):
        """Clean up test backend after each test."""
        registry = get_registry()
        if registry.is_registered("test_dummy"):
            registry.unregister("test_dummy")

    def test_get_registry(self):
        """Test getting the global registry."""
        registry = get_registry()
        self.assertIsInstance(registry, BackendRegistry)

    def test_get_registry_is_singleton(self):
        """Test that get_registry always returns the same instance."""
        registry1 = get_registry()
        registry2 = get_registry()
        self.assertIs(registry1, registry2)

    def test_register_backend_function(self):
        """Test register_backend convenience function."""
        register_backend("another_dummy", DummyBackend)

        registry = get_registry()
        self.assertTrue(registry.is_registered("another_dummy"))

        # Clean up
        registry.unregister("another_dummy")

    def test_create_backend(self):
        """Test creating a backend instance."""
        config = {"count": 10}
        backend = create_backend("test_dummy", config)

        self.assertIsInstance(backend, DummyBackend)
        self.assertEqual(backend.config, config)
        self.assertEqual(backend.num_pixels(), 10)

    def test_create_nonexistent_backend(self):
        """Test that creating nonexistent backend raises error."""
        with self.assertRaises(KeyError):
            create_backend("nonexistent", {})

    def test_create_backend_with_bad_config(self):
        """Test that backend initialization errors are wrapped."""

        class BadBackend(LEDBackend):
            def __init__(self, config: Dict[str, Any]) -> None:
                raise ValueError("Bad configuration")

            def begin(self) -> None:
                pass

            def show(self) -> None:
                pass

            def set_brightness(self, value: int) -> None:
                pass

            def get_brightness(self) -> int:
                return 0

            def num_pixels(self) -> int:
                return 0

            def set_pixel_color(self, index: int, color: int) -> None:
                pass

            def set_pixel_color_rgb(
                self, index: int, r: int, g: int, b: int, w: int = 0
            ) -> None:
                pass

            def get_pixel_color(self, index: int) -> int:
                return 0

            def get_pixel_color_rgb(self, index: int) -> Tuple[int, int, int, int]:
                return (0, 0, 0, 0)

            def cleanup(self) -> None:
                pass

        register_backend("bad", BadBackend)

        with self.assertRaisesRegex(RuntimeError, "Failed to create backend"):
            create_backend("bad", {})

        # Clean up
        get_registry().unregister("bad")

    def test_rpi_ws281x_backend_registered(self):
        """Test that rpi_ws281x backend is registered by default."""
        registry = get_registry()
        self.assertTrue(registry.is_registered("rpi_ws281x"))

        metadata = registry.get_metadata("rpi_ws281x")
        self.assertIn("PWM", metadata["display_name"])

    def test_adafruit_pwm_backend_registered_if_available(self):
        """Test that Adafruit PWM backend is registered if dependencies available."""
        registry = get_registry()

        # Check if backend is registered
        if registry.is_registered("adafruit_neopixel_pwm"):
            # If registered, verify metadata
            metadata = registry.get_metadata("adafruit_neopixel_pwm")
            self.assertIn("PWM", metadata["display_name"])
            self.assertIn("Adafruit", metadata["display_name"])
            self.assertIn("PWM", metadata["description"])

    def test_get_available_backends(self):
        """Test that get_available_backends returns properly structured dict."""
        backends = get_available_backends()

        # Should be a dictionary
        self.assertIsInstance(backends, dict)

        # Should contain rpi_ws281x backend
        self.assertIn("rpi_ws281x", backends)

        # Each backend should have metadata dict with display_name and description
        for backend_name, metadata in backends.items():
            self.assertIsInstance(metadata, dict)
            self.assertIn("display_name", metadata)
            self.assertIn("description", metadata)
            self.assertIsInstance(metadata["display_name"], str)
            self.assertIsInstance(metadata["description"], str)

        # Verify rpi_ws281x metadata
        rpi_metadata = backends["rpi_ws281x"]
        self.assertIn("PWM", rpi_metadata["display_name"])
        self.assertIn("rpi_ws281x", rpi_metadata["description"])


if __name__ == "__main__":
    unittest.main()
