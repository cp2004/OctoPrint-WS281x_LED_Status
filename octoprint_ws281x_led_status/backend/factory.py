__author__ = "Jason Antman <jason@jasonantman.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Jason Antman 2025 - released under the terms of the AGPLv3 License"

import logging
from typing import Any, Dict, Type

from octoprint_ws281x_led_status.backend import LEDBackend
from octoprint_ws281x_led_status.backend.rpi_ws281x_backend import RpiWS281xBackend

# Module-level logger
_logger = logging.getLogger("octoprint.plugins.ws281x_led_status.backend.factory")

# Try to import Adafruit PWM backend - may not be available
# Note: This can fail due to missing dependencies OR due to issues with lgpio
# initialization (e.g., working directory permissions). We catch both cases.
try:
    from octoprint_ws281x_led_status.backend.adafruit_neopixel_pwm_backend import (
        AdafruitNeoPixelPWMBackend,
    )

    ADAFRUIT_BACKEND_AVAILABLE = True
except (ImportError, FileNotFoundError, OSError) as e:
    ADAFRUIT_BACKEND_AVAILABLE = False
    AdafruitNeoPixelPWMBackend = None
    _logger.debug(f"Adafruit PWM backend not available: {e}")


class BackendRegistry:
    """
    Registry of available LED backend implementations.

    This class maintains a mapping of backend names to their implementation
    classes and provides methods to query available backends and their metadata.
    """

    def __init__(self) -> None:
        """Initialize the backend registry."""
        self._backends: Dict[str, Type[LEDBackend]] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        backend_class: Type[LEDBackend],
        display_name: str = None,
        description: str = None,
    ) -> None:
        """
        Register a backend implementation.

        Args:
            name: Internal name/identifier for the backend
            backend_class: The backend implementation class
            display_name: Human-readable name (defaults to name if not provided)
            description: Brief description of the backend
        """
        if name in self._backends:
            raise ValueError(f"Backend '{name}' is already registered")

        if not issubclass(backend_class, LEDBackend):
            raise TypeError(
                f"Backend class must be a subclass of LEDBackend, "
                f"got {backend_class}"
            )

        self._backends[name] = backend_class
        self._metadata[name] = {
            "display_name": display_name or name,
            "description": description or "",
        }

        _logger.debug(
            f"Registered LED backend: '{name}' ({display_name or name}) - {backend_class.__name__}"
        )

    def unregister(self, name: str) -> None:
        """
        Unregister a backend implementation.

        Args:
            name: Name of the backend to unregister

        Raises:
            KeyError: If backend is not registered
        """
        if name not in self._backends:
            raise KeyError(f"Backend '{name}' is not registered")

        del self._backends[name]
        del self._metadata[name]

    def get(self, name: str) -> Type[LEDBackend]:
        """
        Get a backend implementation class by name.

        Args:
            name: Name of the backend

        Returns:
            The backend implementation class

        Raises:
            KeyError: If backend is not registered
        """
        if name not in self._backends:
            available = ", ".join(self.list_backends())
            raise KeyError(
                f"Backend '{name}' is not registered. "
                f"Available backends: {available}"
            )
        return self._backends[name]

    def list_backends(self) -> list:
        """
        List all registered backend names.

        Returns:
            List of registered backend names
        """
        return list(self._backends.keys())

    def get_metadata(self, name: str) -> Dict[str, Any]:
        """
        Get metadata for a backend.

        Args:
            name: Name of the backend

        Returns:
            Dictionary containing metadata (display_name, description)

        Raises:
            KeyError: If backend is not registered
        """
        if name not in self._metadata:
            raise KeyError(f"Backend '{name}' is not registered")
        return self._metadata[name].copy()

    def is_registered(self, name: str) -> bool:
        """
        Check if a backend is registered.

        Args:
            name: Name of the backend

        Returns:
            True if backend is registered, False otherwise
        """
        return name in self._backends


# Global backend registry instance
_registry = BackendRegistry()


def get_registry() -> BackendRegistry:
    """
    Get the global backend registry instance.

    Returns:
        The global BackendRegistry instance
    """
    return _registry


def create_backend(name: str, config: Dict[str, Any]) -> LEDBackend:
    """
    Create a backend instance from the registry.

    This is the main factory function for creating backend instances.
    It looks up the backend class in the registry and instantiates it
    with the provided configuration.

    Args:
        name: Name of the backend to create
        config: Configuration dictionary to pass to the backend

    Returns:
        An initialized backend instance

    Raises:
        KeyError: If the backend is not registered
        Exception: Any exception raised during backend initialization
    """
    _logger.debug(f"Creating LED backend: '{name}'")
    _logger.debug(f"Backend configuration: {config}")

    backend_class = _registry.get(name)

    try:
        backend = backend_class(config)
        _logger.info(
            f"Successfully created '{name}' backend with {config.get('count', 'unknown')} LEDs"
        )
        return backend
    except Exception as e:
        _logger.error(f"Failed to create backend '{name}': {e}")
        raise RuntimeError(
            f"Failed to create backend '{name}': {e}"
        ) from e


def register_backend(
    name: str,
    backend_class: Type[LEDBackend],
    display_name: str = None,
    description: str = None,
) -> None:
    """
    Register a backend in the global registry.

    Convenience function for registering backends with the global registry.

    Args:
        name: Internal name/identifier for the backend
        backend_class: The backend implementation class
        display_name: Human-readable name (defaults to name if not provided)
        description: Brief description of the backend
    """
    _registry.register(name, backend_class, display_name, description)


def get_available_backends() -> Dict[str, Dict[str, Any]]:
    """
    Get all available backends with their metadata.

    Returns a dictionary mapping backend names to their metadata (display_name, description).

    Returns:
        Dictionary of backend names to metadata dicts
    """
    backends = {}
    for backend_name in _registry.list_backends():
        backends[backend_name] = _registry.get_metadata(backend_name)
    return backends


def get_backend_diagnostics() -> Dict[str, Dict[str, Any]]:
    """
    Get diagnostic information about all registered backends.

    Returns detailed information about each backend including:
    - Metadata (display_name, description)
    - Availability status (if backend has is_available method)
    - Backend class name

    Returns:
        Dictionary mapping backend names to diagnostic info
    """
    diagnostics = {}

    for backend_name in _registry.list_backends():
        backend_class = _registry.get(backend_name)
        metadata = _registry.get_metadata(backend_name)

        # Check if backend has is_available method
        is_available = True
        availability_reason = "Available"

        if hasattr(backend_class, "is_available"):
            try:
                is_available = backend_class.is_available()
                if not is_available:
                    availability_reason = "Backend dependencies not available"
            except Exception as e:
                is_available = False
                availability_reason = f"Error checking availability: {e}"

        diagnostics[backend_name] = {
            "display_name": metadata["display_name"],
            "description": metadata["description"],
            "class": backend_class.__name__,
            "available": is_available,
            "availability_reason": availability_reason,
        }

    return diagnostics


# Register built-in backends
register_backend(
    "rpi_ws281x",
    RpiWS281xBackend,
    display_name="rpi_ws281x (PWM)",
    description="Standard rpi_ws281x library using PWM/PCM interface. "
    "Works on Raspberry Pi 1-4, Zero, Zero 2 (NOT Pi 5). "
    "Requires user to be in the gpio group.",
)

# Register Adafruit PWM backend if available
if ADAFRUIT_BACKEND_AVAILABLE:
    register_backend(
        "adafruit_neopixel_pwm",
        AdafruitNeoPixelPWMBackend,
        display_name="Adafruit CircuitPython NeoPixel (PWM)",
        description="Adafruit CircuitPython NeoPixel library using PWM interface. "
        "Works on all Raspberry Pi models including Pi 5. "
        "Supports any GPIO pin. No special group membership or configuration "
        "required beyond standard GPIO access.",
    )
