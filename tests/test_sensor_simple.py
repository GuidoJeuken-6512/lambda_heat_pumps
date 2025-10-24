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
    
    # Test HP templates
    assert "ambient_temp" in HP_SENSOR_TEMPLATES
    ambient_temp = HP_SENSOR_TEMPLATES["ambient_temp"]
    assert "name" in ambient_temp
    assert "unit" in ambient_temp
    assert ambient_temp["name"] == "Ambient Temperature"
    assert ambient_temp["unit"] == "°C"
    assert ambient_temp["device_class"] == SensorDeviceClass.TEMPERATURE


def test_lambda_sensor_basic():
    """Test basic LambdaSensor functionality."""
    from homeassistant.core import HomeAssistant
    from homeassistant.config_entries import ConfigEntry
    
    # Create proper mock objects
    mock_hass = Mock()
    mock_hass.data = {DOMAIN: {}}
    
    mock_entry = Mock()
    mock_entry.entry_id = "test_entry"
    mock_entry.data = {"name": "test", "host": "192.168.1.100", "port": 502}
    
    mock_coordinator = Mock()
    mock_coordinator._entity_addresses = {}
    mock_coordinator.sensor_overrides = {}
    mock_coordinator.disabled_registers = set()
    mock_coordinator.data = {"ambient_temp": {"value": 20.5, "unit": "°C"}}
    
    # Test sensor creation
    sensor = LambdaSensor(
        hass=mock_hass,
        entry=mock_entry,
        coordinator=mock_coordinator,
        sensor_id="ambient_temp",
        name="Ambient Temperature",
        entity_id="sensor.test_ambient_temp",
        unique_id="test_ambient_temp",
        address=1000,
        unit="°C",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        precision=1,
        scale=0.1,
        txt_mapping=None,
        device_info=None,
    )
    
    # Test basic properties
    assert sensor.name == "Ambient Temperature"
    assert sensor.unique_id == "test_ambient_temp"
    assert sensor.native_unit_of_measurement == "°C"
    assert sensor.device_class == SensorDeviceClass.TEMPERATURE
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.should_poll is False


def test_lambda_template_sensor_basic():
    """Test basic LambdaTemplateSensor functionality."""
    from homeassistant.core import HomeAssistant
    from homeassistant.config_entries import ConfigEntry
    
    # Create proper mock objects
    mock_hass = Mock()
    mock_hass.data = {DOMAIN: {}}
    
    mock_entry = Mock()
    mock_entry.entry_id = "test_entry"
    mock_entry.data = {"name": "test", "host": "192.168.1.100", "port": 502}
    
    mock_coordinator = Mock()
    mock_coordinator.data = {"ambient_temp": {"value": 20.5, "unit": "°C"}}
    
    # Test template sensor creation
    sensor = LambdaTemplateSensor(
        hass=mock_hass,
        entry=mock_entry,
        coordinator=mock_coordinator,
        sensor_id="cop_calc",
        name="COP Calculated",
        entity_id="sensor.test_cop_calc",
        unique_id="test_cop_calc",
        template="{{ states('sensor.test_ambient_temp') | float * 2 }}",
        unit=None,
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        precision=6,
        device_info=None,
    )
    
    # Test basic properties
    assert sensor.name == "COP Calculated"
    assert sensor.unique_id == "test_cop_calc"
    assert sensor.device_class == SensorDeviceClass.POWER_FACTOR
    assert sensor.state_class == SensorStateClass.MEASUREMENT


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

