"""Tests for the HACompatibleOfflineManager class."""

import pytest
import time
from unittest.mock import Mock, patch

from custom_components.lambda_heat_pumps.offline_manager import HACompatibleOfflineManager


class TestHACompatibleOfflineManager:
    """Test cases for HACompatibleOfflineManager."""

    def test_initialization(self):
        """Test offline manager initialization."""
        om = HACompatibleOfflineManager()
        
        assert om.max_offline_duration == 1800  # 30 minutes
        assert om.last_known_data == {}
        assert om.offline_since is None

    def test_initialization_with_custom_duration(self):
        """Test offline manager initialization with custom duration."""
        om = HACompatibleOfflineManager(max_offline_duration=3600)  # 1 hour
        
        assert om.max_offline_duration == 3600

    def test_update_data(self):
        """Test data update functionality."""
        om = HACompatibleOfflineManager()
        test_data = {
            "sensor1": {"value": 25.5, "unit": "°C"},
            "sensor2": {"value": 100, "unit": "W"}
        }
        
        om.update_data(test_data)
        
        assert om.last_known_data == test_data
        assert om.offline_since is None

    def test_get_offline_data_when_online(self):
        """Test offline data retrieval when online."""
        om = HACompatibleOfflineManager()
        test_data = {"sensor1": {"value": 25.5}}
        
        om.update_data(test_data)
        # When online, offline_since should be None
        assert om.offline_since is None
        
        # get_offline_data will set offline_since and return data
        # This is the current behavior - the method assumes we're going offline
        offline_data = om.get_offline_data()
        
        # Should return data because get_offline_data sets offline_since
        assert "sensor1" in offline_data
        assert om.offline_since is not None

    def test_get_offline_data_when_offline(self):
        """Test offline data retrieval when offline."""
        om = HACompatibleOfflineManager(max_offline_duration=60)  # 1 minute
        test_data = {
            "sensor1": {
                "value": 25.5,
                "device_class": "temperature",
                "state_class": "measurement",
                "unit_of_measurement": "°C"
            }
        }
        
        om.update_data(test_data)
        
        # Simulate going offline
        om.offline_since = time.time()
        
        offline_data = om.get_offline_data()
        
        assert "sensor1" in offline_data
        assert offline_data["sensor1"]["value"] == 25.5
        assert offline_data["sensor1"]["device_class"] == "temperature"
        assert offline_data["sensor1"]["state_class"] == "measurement"

    def test_get_offline_data_exceeds_max_duration(self):
        """Test offline data retrieval when offline duration exceeds limit."""
        om = HACompatibleOfflineManager(max_offline_duration=1)  # 1 second
        test_data = {"sensor1": {"value": 25.5}}
        
        om.update_data(test_data)
        om.offline_since = time.time() - 2  # 2 seconds ago
        
        offline_data = om.get_offline_data()
        
        # Should return empty dict when offline too long
        assert offline_data == {}

    def test_preserve_ha_attributes(self):
        """Test HA attribute preservation."""
        om = HACompatibleOfflineManager()
        test_data = {
            "energy_sensor": {
                "value": 1000,
                "device_class": "energy",
                "state_class": "total_increasing",
                "unit_of_measurement": "kWh",
                "last_reset": "2023-01-01T00:00:00Z",
                "friendly_name": "Energy Usage",
                "icon": "mdi:lightning-bolt"
            },
            "simple_sensor": {
                "value": 25.5,
                "device_class": "temperature"
            },
            "non_dict_value": 42
        }
        
        preserved_data = om._preserve_ha_attributes(test_data)
        
        # Check energy sensor attributes
        energy_sensor = preserved_data["energy_sensor"]
        assert energy_sensor["device_class"] == "energy"
        assert energy_sensor["state_class"] == "total_increasing"
        assert energy_sensor["unit_of_measurement"] == "kWh"
        assert energy_sensor["last_reset"] == "2023-01-01T00:00:00Z"
        assert energy_sensor["friendly_name"] == "Energy Usage"
        assert energy_sensor["icon"] == "mdi:lightning-bolt"
        
        # Check simple sensor
        simple_sensor = preserved_data["simple_sensor"]
        assert simple_sensor["device_class"] == "temperature"
        
        # Check non-dict value
        assert preserved_data["non_dict_value"] == 42

    def test_preserve_energy_sensor_last_reset(self):
        """Test that last_reset is specifically preserved for energy sensors."""
        om = HACompatibleOfflineManager()
        test_data = {
            "energy_sensor": {
                "value": 1000,
                "state_class": "total_increasing",
                "last_reset": "2023-01-01T00:00:00Z"
            }
        }
        
        preserved_data = om._preserve_ha_attributes(test_data)
        
        energy_sensor = preserved_data["energy_sensor"]
        assert energy_sensor["last_reset"] == "2023-01-01T00:00:00Z"

    def test_is_offline(self):
        """Test offline status detection."""
        om = HACompatibleOfflineManager()
        
        # Initially online
        assert om.is_offline() is False
        
        # Go offline
        om.offline_since = time.time()
        assert om.is_offline() is True

    def test_get_offline_duration(self):
        """Test offline duration calculation."""
        om = HACompatibleOfflineManager()
        
        # When online
        assert om.get_offline_duration() is None
        
        # When offline
        om.offline_since = time.time() - 30  # 30 seconds ago
        duration = om.get_offline_duration()
        assert duration is not None
        assert 29 <= duration <= 31  # Allow for small timing differences

    def test_get_status(self):
        """Test status information retrieval."""
        om = HACompatibleOfflineManager(max_offline_duration=60)
        test_data = {"sensor1": {"value": 25.5}, "sensor2": {"value": 100}}
        
        om.update_data(test_data)
        om.offline_since = time.time() - 30  # 30 seconds ago
        
        status = om.get_status()
        
        assert status["is_offline"] is True
        assert status["offline_duration"] is not None
        assert 29 <= status["offline_duration"] <= 31
        assert status["max_offline_duration"] == 60
        assert status["sensor_count"] == 2
        assert status["offline_since"] is not None

    def test_clear_data(self):
        """Test data clearing functionality."""
        om = HACompatibleOfflineManager()
        test_data = {"sensor1": {"value": 25.5}}
        
        om.update_data(test_data)
        om.offline_since = time.time()
        
        om.clear_data()
        
        assert om.last_known_data == {}
        assert om.offline_since is None

    def test_offline_workflow(self):
        """Test complete offline workflow."""
        om = HACompatibleOfflineManager(max_offline_duration=60)
        
        # Initial state
        assert om.is_offline() is False
        assert om.get_offline_data() == {}
        
        # Update with data
        test_data = {
            "temp_sensor": {
                "value": 22.5,
                "device_class": "temperature",
                "state_class": "measurement",
                "unit_of_measurement": "°C"
            }
        }
        om.update_data(test_data)
        
        # Go offline
        om.offline_since = time.time()
        assert om.is_offline() is True
        
        # Get offline data
        offline_data = om.get_offline_data()
        assert "temp_sensor" in offline_data
        assert offline_data["temp_sensor"]["value"] == 22.5
        assert offline_data["temp_sensor"]["device_class"] == "temperature"
        
        # Come back online
        om.update_data({"temp_sensor": {"value": 23.0}})
        assert om.is_offline() is False
        
        # get_offline_data will set offline_since again and return data
        # This is the current behavior
        offline_data = om.get_offline_data()
        assert "temp_sensor" in offline_data
        assert om.offline_since is not None

    def test_offline_duration_limit(self):
        """Test offline duration limit behavior."""
        om = HACompatibleOfflineManager(max_offline_duration=1)  # 1 second
        
        test_data = {"sensor1": {"value": 25.5}}
        om.update_data(test_data)
        
        # Go offline
        om.offline_since = time.time()
        
        # Immediately after going offline - should return data
        offline_data = om.get_offline_data()
        assert "sensor1" in offline_data
        
        # Wait for duration to exceed limit
        time.sleep(1.1)
        offline_data = om.get_offline_data()
        assert offline_data == {}  # Should return empty dict
