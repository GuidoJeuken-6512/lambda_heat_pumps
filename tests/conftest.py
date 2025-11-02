"""Common test fixtures for Lambda Heat Pumps integration tests."""

import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = Mock()
    hass.data = {}  # Make hass.data a dictionary so it's iterable
    hass.config = Mock()
    hass.config.config_dir = "/tmp/test_config"
    return hass


@pytest.fixture
def mock_entry():
    """Mock ConfigEntry instance."""
    entry = Mock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        "name": "eu08l",
        "host": "192.168.1.100",
        "port": 502,
        "num_hps": 1,
        "num_boil": 1,
        "num_buff": 0,
        "num_sol": 0,
        "num_hc": 1,
        "use_legacy_modbus_names": True,
        "firmware_version": "V1.0.0",
    }
    entry.version = 1
    return entry


@pytest.fixture
def mock_coordinator():
    """Mock LambdaCoordinator instance."""
    coordinator = Mock()
    coordinator.sensor_overrides = {}
    coordinator.disabled_registers = set()
    return coordinator


@pytest.fixture
def mock_entity_registry():
    """Mock Entity Registry instance."""
    registry = Mock()
    registry.entities.get_entries_for_config_entry_id.return_value = []
    return registry


@pytest.fixture
def sample_sensor_data():
    """Sample sensor data for testing."""
    return {
        "ambient_temp": {
            "name": "Ambient Temperature",
            "address": 1000,
            "unit": "°C",
            "device_class": "temperature",
            "state_class": "measurement",
        },
        "hp1_flow_temp": {
            "name": "Flow Temperature",
            "address": 1100,
            "unit": "°C",
            "device_class": "temperature",
            "state_class": "measurement",
        },
    }


@pytest.fixture
def sample_climate_data():
    """Sample climate data for testing."""
    return {
        "hot_water": {
            "name": "Hot Water",
            "device_type": "boil",
            "target_temp_address": 2000,
            "current_temp_address": 2001,
        },
        "heating_circuit": {
            "name": "Heating Circuit",
            "device_type": "hc",
            "target_temp_address": 3000,
            "current_temp_address": 3001,
        },
    }
