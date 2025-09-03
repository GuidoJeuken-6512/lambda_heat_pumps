"""Circuit Breaker Binary Sensor for Lambda Heat Pumps integration."""

from __future__ import annotations

import logging
from typing import Any, Dict

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from .circuit_breaker import SmartCircuitBreaker

_LOGGER = logging.getLogger(__name__)


class CircuitBreakerSensor(BinarySensorEntity):
    """Binary sensor representing the circuit breaker status."""
    
    def __init__(
        self,
        circuit_breaker: SmartCircuitBreaker,
        device_info: DeviceInfo,
        unique_id: str
    ):
        """Initialize the circuit breaker sensor.
        
        Args:
            circuit_breaker: SmartCircuitBreaker instance
            device_info: Device information
            unique_id: Unique identifier for the sensor
        """
        self._circuit_breaker = circuit_breaker
        self._attr_name = "Lambda Modbus Circuit Breaker"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_device_info = device_info
        self._attr_unique_id = unique_id
        self._attr_icon = "mdi:connection"
    
    @property
    def is_on(self) -> bool:
        """Return True if circuit breaker is closed (connection OK)."""
        return not self._circuit_breaker.is_open
    
    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        status = self._circuit_breaker.get_status()
        return {
            "failure_count": status["failure_count"],
            "last_failure_time": status["last_failure_time"],
            "state": status["state"],
            "force_open": status["force_open"],
            "failure_threshold": status["failure_threshold"],
            "recovery_timeout": status["recovery_timeout"],
        }
    
    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True  # Circuit breaker sensor is always available
    
    def update(self) -> None:
        """Update the sensor state."""
        # The state is automatically updated when circuit breaker changes
        # This method can be used for additional updates if needed
        pass
