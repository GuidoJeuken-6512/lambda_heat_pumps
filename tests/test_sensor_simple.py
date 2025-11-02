"""Vereinfachte Tests für das sensor Modul."""

import pytest
from unittest.mock import Mock, MagicMock
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

from custom_components.lambda_heat_pumps.const import (
    DOMAIN,
    HP_SENSOR_TEMPLATES,
    BOIL_SENSOR_TEMPLATES,
    HC_SENSOR_TEMPLATES,
)
from custom_components.lambda_heat_pumps.sensor import (
    LambdaSensor,
    LambdaTemplateSensor,
)


def test_sensor_templates_exist():
    """Test that sensor templates exist and have required fields."""
    assert HP_SENSOR_TEMPLATES is not None
    assert BOIL_SENSOR_TEMPLATES is not None
    assert HC_SENSOR_TEMPLATES is not None
    
    # Test HP templates - check for a template that actually exists
    assert len(HP_SENSOR_TEMPLATES) > 0
    # Pick first template to test structure
    first_template_key = list(HP_SENSOR_TEMPLATES.keys())[0]
    first_template = HP_SENSOR_TEMPLATES[first_template_key]
    assert "name" in first_template
    assert "unit" in first_template


def test_lambda_sensor_basic():
    """Test basic LambdaSensor functionality."""
    from homeassistant.config_entries import ConfigEntry
    
    # Create proper mock objects
    mock_entry = Mock(spec=ConfigEntry)
    mock_entry.entry_id = "test_entry"
    mock_entry.data = {"name": "test", "host": "192.168.1.100", "port": 502}
    
    mock_coordinator = Mock()
    mock_coordinator._entity_addresses = {}
    mock_coordinator.sensor_overrides = {}
    mock_coordinator.disabled_registers = set()
    mock_coordinator.data = {"test_sensor": 20.5}
    
    # Test sensor creation with correct signature
    sensor = LambdaSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="test_sensor",
        name="Test Sensor",
        unit="°C",
        address=1000,
        scale=0.1,
        state_class="measurement",
        device_class=SensorDeviceClass.TEMPERATURE,
        relative_address=0,
        data_type="int16",
        device_type="Hp",
        txt_mapping=False,
        precision=1,
        entity_id="sensor.test_sensor",
        unique_id="test_sensor",
    )
    
    # Test basic properties
    assert sensor._attr_name == "Test Sensor"
    assert sensor._attr_unique_id == "test_sensor"
    assert sensor._unit == "°C"
    assert sensor._device_class == SensorDeviceClass.TEMPERATURE
    assert sensor._attr_should_poll is False


def test_lambda_template_sensor_basic():
    """Test basic LambdaTemplateSensor functionality."""
    from homeassistant.config_entries import ConfigEntry
    
    # Create proper mock objects
    mock_entry = Mock(spec=ConfigEntry)
    mock_entry.entry_id = "test_entry"
    mock_entry.data = {"name": "test", "host": "192.168.1.100", "port": 502}
    
    mock_coordinator = Mock()
    mock_coordinator.data = {"test_sensor": 20.5}
    
    # Test template sensor creation with correct signature
    sensor = LambdaTemplateSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="cop_calc",
        name="COP Calculated",
        unit=None,
        state_class="measurement",
        device_class=SensorDeviceClass.POWER_FACTOR,
        device_type="Hp",
        precision=6,
        entity_id="sensor.test_cop_calc",
        unique_id="test_cop_calc",
        template_str="{{ states('sensor.test_ambient_temp') | float * 2 }}",
    )
    
    # Test basic properties
    assert sensor.name == "COP Calculated"
    assert sensor.unique_id == "test_cop_calc"
    assert sensor._device_class == SensorDeviceClass.POWER_FACTOR
    assert sensor._attr_should_poll is False


def test_txt_mapping_sensor_unit():
    """Test that txt_mapping sensors return None as unit."""
    from homeassistant.config_entries import ConfigEntry
    
    # Create proper mock objects
    mock_entry = Mock(spec=ConfigEntry)
    mock_entry.entry_id = "test_entry"
    mock_entry.data = {"name": "test", "host": "192.168.1.100", "port": 502}
    
    mock_coordinator = Mock()
    mock_coordinator._entity_addresses = {}
    mock_coordinator.sensor_overrides = {}
    mock_coordinator.disabled_registers = set()
    mock_coordinator.data = {"operating_state": 1}
    
    # Test sensor with txt_mapping=True
    sensor = LambdaSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="operating_state",
        name="Operating State",
        unit="°C",  # This should be ignored and set to None
        address=1000,
        scale=1.0,
        state_class="measurement",
        device_class=None,
        relative_address=3,
        data_type="uint16",
        device_type="hp",
        txt_mapping=True,
        precision=0,
        entity_id="sensor.operating_state",
        unique_id="operating_state",
    )
    
    # Test that txt_mapping sensors have unit=None
    assert sensor._attr_native_unit_of_measurement is None
    assert sensor.native_unit_of_measurement is None
    assert sensor._is_state_sensor is True


def test_sensor_imports():
    """Test that all required sensor classes can be imported."""
    from custom_components.lambda_heat_pumps.sensor import (
        LambdaSensor,
        LambdaTemplateSensor,
        LambdaCyclingSensor,
        LambdaYesterdaySensor,
        LambdaEnergyConsumptionSensor,
        async_setup_entry,
    )
    
    # Classes should be importable
    assert LambdaSensor is not None
    assert LambdaTemplateSensor is not None
    assert LambdaCyclingSensor is not None
    assert LambdaYesterdaySensor is not None
    assert LambdaEnergyConsumptionSensor is not None
    assert callable(async_setup_entry)


def test_constants():
    """Test that required constants are available."""
    assert DOMAIN == "lambda_heat_pumps"
    
    # Test that templates have expected structure
    for template_name, template in HP_SENSOR_TEMPLATES.items():
        assert "name" in template
        assert "unit" in template
        assert isinstance(template["name"], str)
        assert template["name"] != ""


if __name__ == "__main__":
    pytest.main([__file__])

