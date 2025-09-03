"""Tests for the CircuitBreakerSensor class."""

import pytest
from unittest.mock import Mock, patch

from custom_components.lambda_heat_pumps.circuit_breaker_sensor import CircuitBreakerSensor
from custom_components.lambda_heat_pumps.circuit_breaker import SmartCircuitBreaker


class TestCircuitBreakerSensor:
    """Test cases for CircuitBreakerSensor."""

    def test_initialization(self):
        """Test sensor initialization."""
        mock_circuit_breaker = Mock(spec=SmartCircuitBreaker)
        mock_device_info = {"identifiers": {("lambda_heat_pumps", "test_device")}}
        unique_id = "test_circuit_breaker"
        
        sensor = CircuitBreakerSensor(mock_circuit_breaker, mock_device_info, unique_id)
        
        assert sensor._circuit_breaker == mock_circuit_breaker
        assert sensor._attr_name == "Lambda Modbus Circuit Breaker"
        assert sensor._attr_unique_id == unique_id
        assert sensor._attr_device_info == mock_device_info
        assert sensor._attr_icon == "mdi:connection"

    def test_is_on_when_circuit_closed(self):
        """Test is_on property when circuit breaker is closed."""
        mock_circuit_breaker = Mock(spec=SmartCircuitBreaker)
        mock_circuit_breaker.is_open = False
        
        sensor = CircuitBreakerSensor(mock_circuit_breaker, {}, "test_id")
        
        assert sensor.is_on is True

    def test_is_on_when_circuit_open(self):
        """Test is_on property when circuit breaker is open."""
        mock_circuit_breaker = Mock(spec=SmartCircuitBreaker)
        mock_circuit_breaker.is_open = True
        
        sensor = CircuitBreakerSensor(mock_circuit_breaker, {}, "test_id")
        
        assert sensor.is_on is False

    def test_extra_state_attributes(self):
        """Test extra state attributes."""
        mock_circuit_breaker = Mock(spec=SmartCircuitBreaker)
        mock_circuit_breaker.get_status.return_value = {
            "failure_count": 2,
            "last_failure_time": 1234567890.0,
            "state": "open",
            "force_open": True,
            "failure_threshold": 3,
            "recovery_timeout": 60,
        }
        
        sensor = CircuitBreakerSensor(mock_circuit_breaker, {}, "test_id")
        attributes = sensor.extra_state_attributes
        
        expected_attributes = {
            "failure_count": 2,
            "last_failure_time": 1234567890.0,
            "state": "open",
            "force_open": True,
            "failure_threshold": 3,
            "recovery_timeout": 60,
        }
        
        assert attributes == expected_attributes
        mock_circuit_breaker.get_status.assert_called_once()

    def test_available_property(self):
        """Test that sensor is always available."""
        mock_circuit_breaker = Mock(spec=SmartCircuitBreaker)
        
        sensor = CircuitBreakerSensor(mock_circuit_breaker, {}, "test_id")
        
        assert sensor.available is True

    def test_update_method(self):
        """Test update method (should not raise exceptions)."""
        mock_circuit_breaker = Mock(spec=SmartCircuitBreaker)
        
        sensor = CircuitBreakerSensor(mock_circuit_breaker, {}, "test_id")
        
        # Should not raise any exceptions
        sensor.update()

    def test_device_class(self):
        """Test that device class is set correctly."""
        mock_circuit_breaker = Mock(spec=SmartCircuitBreaker)
        
        sensor = CircuitBreakerSensor(mock_circuit_breaker, {}, "test_id")
        
        # Import the device class to check
        from homeassistant.components.binary_sensor import BinarySensorDeviceClass
        assert sensor._attr_device_class == BinarySensorDeviceClass.CONNECTIVITY

    def test_sensor_state_changes(self):
        """Test sensor state changes with circuit breaker state changes."""
        mock_circuit_breaker = Mock(spec=SmartCircuitBreaker)
        
        sensor = CircuitBreakerSensor(mock_circuit_breaker, {}, "test_id")
        
        # Circuit closed
        mock_circuit_breaker.is_open = False
        assert sensor.is_on is True
        
        # Circuit open
        mock_circuit_breaker.is_open = True
        assert sensor.is_on is False
        
        # Circuit closed again
        mock_circuit_breaker.is_open = False
        assert sensor.is_on is True

    def test_status_attributes_update(self):
        """Test that status attributes update when circuit breaker status changes."""
        mock_circuit_breaker = Mock(spec=SmartCircuitBreaker)
        
        # Initial status
        mock_circuit_breaker.get_status.return_value = {
            "failure_count": 0,
            "last_failure_time": None,
            "state": "closed",
            "force_open": False,
            "failure_threshold": 3,
            "recovery_timeout": 60,
        }
        
        sensor = CircuitBreakerSensor(mock_circuit_breaker, {}, "test_id")
        initial_attributes = sensor.extra_state_attributes
        
        assert initial_attributes["state"] == "closed"
        assert initial_attributes["failure_count"] == 0
        
        # Updated status
        mock_circuit_breaker.get_status.return_value = {
            "failure_count": 2,
            "last_failure_time": 1234567890.0,
            "state": "open",
            "force_open": False,
            "failure_threshold": 3,
            "recovery_timeout": 60,
        }
        
        updated_attributes = sensor.extra_state_attributes
        
        assert updated_attributes["state"] == "open"
        assert updated_attributes["failure_count"] == 2

    def test_force_open_attribute(self):
        """Test force_open attribute handling."""
        mock_circuit_breaker = Mock(spec=SmartCircuitBreaker)
        mock_circuit_breaker.get_status.return_value = {
            "failure_count": 999,
            "last_failure_time": 1234567890.0,
            "state": "open",
            "force_open": True,
            "failure_threshold": 3,
            "recovery_timeout": 60,
        }
        
        sensor = CircuitBreakerSensor(mock_circuit_breaker, {}, "test_id")
        attributes = sensor.extra_state_attributes
        
        assert attributes["force_open"] is True
        assert attributes["failure_count"] == 999

    def test_unique_id_format(self):
        """Test unique ID format."""
        mock_circuit_breaker = Mock(spec=SmartCircuitBreaker)
        mock_device_info = {"identifiers": {("lambda_heat_pumps", "device_123")}}
        unique_id = "device_123_circuit_breaker"
        
        sensor = CircuitBreakerSensor(mock_circuit_breaker, mock_device_info, unique_id)
        
        assert sensor._attr_unique_id == unique_id

    def test_sensor_name(self):
        """Test sensor name."""
        mock_circuit_breaker = Mock(spec=SmartCircuitBreaker)
        
        sensor = CircuitBreakerSensor(mock_circuit_breaker, {}, "test_id")
        
        assert sensor._attr_name == "Lambda Modbus Circuit Breaker"

    def test_icon_property(self):
        """Test icon property."""
        mock_circuit_breaker = Mock(spec=SmartCircuitBreaker)
        
        sensor = CircuitBreakerSensor(mock_circuit_breaker, {}, "test_id")
        
        assert sensor._attr_icon == "mdi:connection"

    def test_circuit_breaker_integration(self):
        """Test integration with actual circuit breaker."""
        # Create a real circuit breaker for integration testing
        circuit_breaker = SmartCircuitBreaker()
        mock_device_info = {"identifiers": {("lambda_heat_pumps", "integration_test")}}
        unique_id = "integration_test_circuit_breaker"
        
        sensor = CircuitBreakerSensor(circuit_breaker, mock_device_info, unique_id)
        
        # Initial state - circuit closed
        assert sensor.is_on is True
        assert sensor.extra_state_attributes["state"] == "closed"
        assert sensor.extra_state_attributes["failure_count"] == 0
        
        # Simulate failures to open circuit
        circuit_breaker.record_failure(ConnectionError("Network error"))
        circuit_breaker.record_failure(ConnectionError("Another network error"))
        circuit_breaker.record_failure(ConnectionError("Third network error"))
        
        # Circuit should now be open
        assert sensor.is_on is False
        assert sensor.extra_state_attributes["state"] == "open"
        assert sensor.extra_state_attributes["failure_count"] == 3
        
        # Record success to close circuit
        circuit_breaker.record_success()
        
        # Circuit should be closed again
        assert sensor.is_on is True
        assert sensor.extra_state_attributes["state"] == "closed"
        assert sensor.extra_state_attributes["failure_count"] == 0
