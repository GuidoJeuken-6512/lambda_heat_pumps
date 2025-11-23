"""Tests für die neue Cycling-Sensor-Architektur."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch
from types import SimpleNamespace
import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.lambda_heat_pumps.sensor import (
    LambdaCyclingSensor,
    LambdaYesterdaySensor,
    async_setup_entry,
)
from tests.conftest import DummyLoop


@pytest.fixture
def mock_hass():
    """Create a mock hass object."""
    hass = Mock()
    hass.config = Mock()
    hass.config.config_dir = "/tmp/test_config"
    hass.config.language = "en"
    hass.config.locale = SimpleNamespace(language="en")
    hass.config_entries = Mock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.data = {}
    hass.states = Mock()
    hass.states.async_all = AsyncMock(return_value=[])
    hass.states.get = Mock()
    hass.loop = DummyLoop()
    return hass


@pytest.fixture
def mock_entry():
    """Create a mock config entry."""
    entry = Mock()
    entry.entry_id = "test_entry"
    entry.data = {
        "host": "192.168.1.100",
        "port": 502,
        "slave_id": 1,
        "firmware_version": "V0.0.3-3K",
        "num_hps": 1,
        "num_boil": 1,
        "num_hc": 1,
        "num_buffer": 0,
        "num_solar": 0,
        "update_interval": 30,
        "write_interval": 30,
        "heating_circuit_min_temp": 15,
        "heating_circuit_max_temp": 35,
        "heating_circuit_temp_step": 0.5,
        "room_thermostat_control": False,
        "pv_surplus": False,
        "room_temperature_entity_1": "sensor.room_temp",
        "pv_power_sensor_entity": "sensor.pv_power",
        "use_legacy_modbus_names": True,
        "name": "test",
    }
    return entry


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = Mock()
    coordinator.data = {
        "hp1_temperature": 20.5,
        "hp1_state": 1,
        "hp1_operating_state": 2,
    }
    coordinator.sensor_overrides = {}
    coordinator.is_register_disabled = Mock(return_value=False)
    coordinator.hass = Mock()
    return coordinator


# Tests für LambdaYesterdaySensor
def test_lambda_yesterday_sensor_init(mock_entry, mock_coordinator):
    """Test LambdaYesterdaySensor initialization."""
    sensor = LambdaYesterdaySensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_yesterday",
        name="Heating Cycling Yesterday",
        entity_id="sensor.test_heating_cycling_yesterday",
        unique_id="test_heating_cycling_yesterday",
        unit="cycles",
        state_class="total",
        device_class=None,
        device_type="hp",
        hp_index=1,
        mode="heating",
    )
    
    assert sensor._sensor_id == "heating_cycling_yesterday"
    assert sensor._name == "Heating Cycling Yesterday"
    assert sensor.entity_id == "sensor.test_heating_cycling_yesterday"
    assert sensor._unique_id == "test_heating_cycling_yesterday"
    assert sensor._unit == "cycles"
    assert sensor._hp_index == 1
    assert sensor._mode == "heating"
    assert sensor._yesterday_value == 0


def test_lambda_yesterday_sensor_set_cycling_value(mock_entry, mock_coordinator):
    """Test LambdaYesterdaySensor set_cycling_value method."""
    sensor = LambdaYesterdaySensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_yesterday",
        name="Heating Cycling Yesterday",
        entity_id="sensor.test_heating_cycling_yesterday",
        unique_id="test_heating_cycling_yesterday",
        unit="cycles",
        state_class="total",
        device_class=None,
        device_type="hp",
        hp_index=1,
        mode="heating",
    )
    
    # Mock async_write_ha_state
    sensor.async_write_ha_state = Mock()
    
    # Test setting yesterday value (async method)
    import asyncio
    asyncio.run(sensor.set_cycling_value(42))
    assert sensor._yesterday_value == 42
    sensor.async_write_ha_state.assert_called_once()


def test_lambda_yesterday_sensor_native_value(mock_entry, mock_coordinator):
    """Test LambdaYesterdaySensor native_value property."""
    sensor = LambdaYesterdaySensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_yesterday",
        name="Heating Cycling Yesterday",
        entity_id="sensor.test_heating_cycling_yesterday",
        unique_id="test_heating_cycling_yesterday",
        unit="cycles",
        state_class="total",
        device_class=None,
        device_type="hp",
        hp_index=1,
        mode="heating",
    )
    
    # Test initial value
    assert sensor.native_value == 0
    
    # Test with set value
    sensor._yesterday_value = 25
    assert sensor.native_value == 25


def test_lambda_yesterday_sensor_extra_state_attributes(mock_entry, mock_coordinator):
    """Test LambdaYesterdaySensor extra_state_attributes property."""
    sensor = LambdaYesterdaySensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_yesterday",
        name="Heating Cycling Yesterday",
        entity_id="sensor.test_heating_cycling_yesterday",
        unique_id="test_heating_cycling_yesterday",
        unit="cycles",
        state_class="total",
        device_class=None,
        device_type="hp",
        hp_index=1,
        mode="heating",
    )
    
    attrs = sensor.extra_state_attributes
    assert attrs["mode"] == "heating"
    assert attrs["hp_index"] == 1
    assert attrs["sensor_type"] == "cycling_yesterday"


# Tests für LambdaCyclingSensor (neue Architektur)
def test_lambda_cycling_sensor_reset_handlers(mock_entry, mock_coordinator):
    """Test LambdaCyclingSensor reset handlers."""
    # Test Daily sensor
    daily_sensor = LambdaCyclingSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_daily",
        name="Heating Cycling Daily",
        entity_id="sensor.test_heating_cycling_daily",
        unique_id="test_heating_cycling_daily",
        unit="cycles",
        state_class="measurement",
        device_class=None,
        device_type="hp",
        hp_index=1,
    )
    
    # Mock async_write_ha_state
    daily_sensor.async_write_ha_state = Mock()
    
    # Set initial value
    daily_sensor._cycling_value = 50
    
    # Test daily reset (async method)
    import asyncio
    asyncio.run(daily_sensor._handle_daily_reset("test_entry"))
    assert daily_sensor._cycling_value == 0
    daily_sensor.async_write_ha_state.assert_called_once()
    
    # Test with wrong entry_id
    daily_sensor._cycling_value = 50
    daily_sensor.async_write_ha_state.reset_mock()
    asyncio.run(daily_sensor._handle_daily_reset("wrong_entry"))
    assert daily_sensor._cycling_value == 50  # Should not reset
    daily_sensor.async_write_ha_state.assert_not_called()


def test_lambda_cycling_sensor_2h_reset_handler(mock_entry, mock_coordinator):
    """Test LambdaCyclingSensor 2h reset handler."""
    sensor = LambdaCyclingSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_2h",
        name="Heating Cycling 2h",
        entity_id="sensor.test_heating_cycling_2h",
        unique_id="test_heating_cycling_2h",
        unit="cycles",
        state_class="measurement",
        device_class=None,
        device_type="hp",
        hp_index=1,
    )
    
    # Mock async_write_ha_state
    sensor.async_write_ha_state = Mock()
    
    # Set initial value
    sensor._cycling_value = 30
    
    # Test 2h reset (async method)
    import asyncio
    asyncio.run(sensor._handle_2h_reset("test_entry"))
    assert sensor._cycling_value == 0
    sensor.async_write_ha_state.assert_called_once()


def test_lambda_cycling_sensor_4h_reset_handler(mock_entry, mock_coordinator):
    """Test LambdaCyclingSensor 4h reset handler."""
    sensor = LambdaCyclingSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_4h",
        name="Heating Cycling 4h",
        entity_id="sensor.test_heating_cycling_4h",
        unique_id="test_heating_cycling_4h",
        unit="cycles",
        state_class="measurement",
        device_class=None,
        device_type="hp",
        hp_index=1,
    )
    
    # Mock async_write_ha_state
    sensor.async_write_ha_state = Mock()
    
    # Set initial value
    sensor._cycling_value = 75
    
    # Test 4h reset (async method)
    import asyncio
    asyncio.run(sensor._handle_4h_reset("test_entry"))
    assert sensor._cycling_value == 0
    sensor.async_write_ha_state.assert_called_once()


def test_lambda_cycling_sensor_monthly_reset_handler(mock_entry, mock_coordinator):
    """Test LambdaCyclingSensor monthly reset handler."""
    sensor = LambdaCyclingSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="compressor_start_cycling_monthly",
        name="Compressor Start Cycling Monthly",
        entity_id="sensor.test_compressor_start_cycling_monthly",
        unique_id="test_compressor_start_cycling_monthly",
        unit="cycles",
        state_class="total",
        device_class=None,
        device_type="hp",
        hp_index=1,
    )
    
    # Mock async_write_ha_state
    sensor.async_write_ha_state = Mock()
    
    # Set initial value
    sensor._cycling_value = 100
    
    # Test monthly reset (async method)
    import asyncio
    asyncio.run(sensor._handle_monthly_reset("test_entry"))
    assert sensor._cycling_value == 0
    sensor.async_write_ha_state.assert_called_once()


def test_compressor_start_cycling_sensor_init(mock_entry, mock_coordinator):
    """Test compressor_start cycling sensor initialization."""
    sensor = LambdaCyclingSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="compressor_start_cycling_total",
        name="Compressor Start Cycling Total",
        entity_id="sensor.test_compressor_start_cycling_total",
        unique_id="test_compressor_start_cycling_total",
        unit="cycles",
        state_class="total_increasing",
        device_class=None,
        device_type="hp",
        hp_index=1,
    )
    
    assert sensor._sensor_id == "compressor_start_cycling_total"
    assert sensor._name == "Compressor Start Cycling Total"
    assert sensor.entity_id == "sensor.test_compressor_start_cycling_total"
    assert sensor._unique_id == "test_compressor_start_cycling_total"
    assert sensor._unit == "cycles"
    assert sensor._hp_index == 1
    assert sensor._cycling_value == 0


def test_compressor_start_cycling_sensor_2h_reset(mock_entry, mock_coordinator):
    """Test compressor_start 2h sensor reset handler."""
    sensor = LambdaCyclingSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="compressor_start_cycling_2h",
        name="Compressor Start Cycling 2h",
        entity_id="sensor.test_compressor_start_cycling_2h",
        unique_id="test_compressor_start_cycling_2h",
        unit="cycles",
        state_class="total",
        device_class=None,
        device_type="hp",
        hp_index=1,
    )
    
    sensor.async_write_ha_state = Mock()
    sensor._cycling_value = 15
    
    import asyncio
    asyncio.run(sensor._handle_2h_reset("test_entry"))
    assert sensor._cycling_value == 0
    sensor.async_write_ha_state.assert_called_once()


def test_compressor_start_cycling_sensor_4h_reset(mock_entry, mock_coordinator):
    """Test compressor_start 4h sensor reset handler."""
    sensor = LambdaCyclingSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="compressor_start_cycling_4h",
        name="Compressor Start Cycling 4h",
        entity_id="sensor.test_compressor_start_cycling_4h",
        unique_id="test_compressor_start_cycling_4h",
        unit="cycles",
        state_class="total",
        device_class=None,
        device_type="hp",
        hp_index=1,
    )
    
    sensor.async_write_ha_state = Mock()
    sensor._cycling_value = 25
    
    import asyncio
    asyncio.run(sensor._handle_4h_reset("test_entry"))
    assert sensor._cycling_value == 0
    sensor.async_write_ha_state.assert_called_once()


# Tests für cycling_entities Registrierung
@pytest.mark.asyncio
async def test_cycling_entities_registration(mock_hass, mock_entry, mock_coordinator):
    """Test that all cycling sensors are properly registered in cycling_entities."""
    from custom_components.lambda_heat_pumps.const import DOMAIN
    
    mock_add_entities = AsyncMock()
    mock_hass.data[DOMAIN] = {mock_entry.entry_id: {"coordinator": mock_coordinator}}
    
    # Mock the sensor classes to avoid actual instantiation
    with patch("custom_components.lambda_heat_pumps.sensor.LambdaCyclingSensor") as mock_cycling_class, \
         patch("custom_components.lambda_heat_pumps.sensor.LambdaYesterdaySensor") as mock_yesterday_class, \
         patch("custom_components.lambda_heat_pumps.sensor.LambdaSensor") as mock_sensor_class, \
         patch("custom_components.lambda_heat_pumps.automations.setup_cycling_automations") as mock_automations:
        
        # Create mock sensor instances
        mock_cycling_sensor = Mock()
        mock_cycling_sensor.entity_id = "sensor.test_heating_cycling_total"
        mock_cycling_sensor._sensor_id = "heating_cycling_total"
        mock_cycling_class.return_value = mock_cycling_sensor
        
        mock_yesterday_sensor = Mock()
        mock_yesterday_sensor.entity_id = "sensor.test_heating_cycling_yesterday"
        mock_yesterday_sensor._sensor_id = "heating_cycling_yesterday"
        mock_yesterday_class.return_value = mock_yesterday_sensor
        
        mock_daily_sensor = Mock()
        mock_daily_sensor.entity_id = "sensor.test_heating_cycling_daily"
        mock_daily_sensor._sensor_id = "heating_cycling_daily"
        
        mock_2h_sensor = Mock()
        mock_2h_sensor.entity_id = "sensor.test_heating_cycling_2h"
        mock_2h_sensor._sensor_id = "heating_cycling_2h"
        
        mock_4h_sensor = Mock()
        mock_4h_sensor.entity_id = "sensor.test_heating_cycling_4h"
        mock_4h_sensor._sensor_id = "heating_cycling_4h"
        
        # Create mock monthly sensor
        mock_monthly_sensor = Mock()
        mock_monthly_sensor.entity_id = "sensor.test_compressor_start_cycling_monthly"
        mock_monthly_sensor._sensor_id = "compressor_start_cycling_monthly"
        
        # Make cycling_class return different sensors based on sensor_id
        def cycling_sensor_side_effect(*args, **kwargs):
            sensor_id = kwargs.get('sensor_id', args[2] if len(args) > 2 else 'unknown')
            if 'daily' in sensor_id:
                return mock_daily_sensor
            elif '2h' in sensor_id:
                return mock_2h_sensor
            elif '4h' in sensor_id:
                return mock_4h_sensor
            elif 'monthly' in sensor_id:
                return mock_monthly_sensor
            else:
                return mock_cycling_sensor
        
        mock_cycling_class.side_effect = cycling_sensor_side_effect
        
        # Mock regular sensor
        mock_regular_sensor = Mock()
        mock_regular_sensor.entity_id = "sensor.test_hp1_temperature"
        mock_sensor_class.return_value = mock_regular_sensor
        
        await async_setup_entry(mock_hass, mock_entry, mock_add_entities)
        
        # Verify that cycling_entities was set up
        assert "lambda_heat_pumps" in mock_hass.data
        assert mock_entry.entry_id in mock_hass.data["lambda_heat_pumps"]
        assert "cycling_entities" in mock_hass.data["lambda_heat_pumps"][mock_entry.entry_id]
        
        cycling_entities = mock_hass.data["lambda_heat_pumps"][mock_entry.entry_id]["cycling_entities"]
        
        # Verify that all cycling sensor types are registered
        assert "sensor.test_hp1_heating_cycling_total" in cycling_entities
        assert "sensor.test_hp1_heating_cycling_yesterday" in cycling_entities
        assert "sensor.test_hp1_heating_cycling_daily" in cycling_entities
        assert "sensor.test_hp1_heating_cycling_2h" in cycling_entities
        assert "sensor.test_hp1_heating_cycling_4h" in cycling_entities
        
        # Verify compressor_start sensors are registered
        assert "sensor.test_hp1_compressor_start_cycling_total" in cycling_entities
        assert "sensor.test_hp1_compressor_start_cycling_daily" in cycling_entities
        assert "sensor.test_hp1_compressor_start_cycling_2h" in cycling_entities
        assert "sensor.test_hp1_compressor_start_cycling_4h" in cycling_entities
        assert "sensor.test_hp1_compressor_start_cycling_monthly" in cycling_entities


@pytest.mark.asyncio
async def test_yesterday_sensors_in_cycling_entities(mock_hass, mock_entry, mock_coordinator):
    """Test that Yesterday sensors are specifically included in cycling_entities."""
    from custom_components.lambda_heat_pumps.const import DOMAIN
    
    mock_add_entities = AsyncMock()
    mock_hass.data[DOMAIN] = {mock_entry.entry_id: {"coordinator": mock_coordinator}}
    
    with patch("custom_components.lambda_heat_pumps.sensor.LambdaCyclingSensor") as mock_cycling_class, \
         patch("custom_components.lambda_heat_pumps.sensor.LambdaYesterdaySensor") as mock_yesterday_class, \
         patch("custom_components.lambda_heat_pumps.sensor.LambdaSensor") as mock_sensor_class, \
         patch("custom_components.lambda_heat_pumps.automations.setup_cycling_automations") as mock_automations:
        
        # Create mock yesterday sensor
        mock_yesterday_sensor = Mock()
        mock_yesterday_sensor.entity_id = "sensor.test_heating_cycling_yesterday"
        mock_yesterday_sensor._sensor_id = "heating_cycling_yesterday"
        mock_yesterday_class.return_value = mock_yesterday_sensor
        
        # Mock other sensors
        mock_cycling_sensor = Mock()
        mock_cycling_sensor.entity_id = "sensor.test_heating_cycling_total"
        mock_cycling_sensor._sensor_id = "heating_cycling_total"
        mock_cycling_class.return_value = mock_cycling_sensor
        
        mock_regular_sensor = Mock()
        mock_regular_sensor.entity_id = "sensor.test_hp1_temperature"
        mock_sensor_class.return_value = mock_regular_sensor
        
        await async_setup_entry(mock_hass, mock_entry, mock_add_entities)
        
        # Verify that yesterday sensors are in cycling_entities
        cycling_entities = mock_hass.data["lambda_heat_pumps"][mock_entry.entry_id]["cycling_entities"]
        
        # This test specifically checks that yesterday sensors are included
        yesterday_entities = [entity_id for entity_id in cycling_entities.keys() if "yesterday" in entity_id]
        assert len(yesterday_entities) > 0, "Yesterday sensors should be included in cycling_entities"
        
        # Verify the specific yesterday sensor is there
        assert "sensor.test_hp1_heating_cycling_yesterday" in cycling_entities


# Tests für _update_yesterday_sensors Funktion
def test_update_yesterday_sensors_function(mock_hass, mock_entry):
    """Test the _update_yesterday_sensors function from automations."""
    from custom_components.lambda_heat_pumps.automations import _update_yesterday_sensors
    
    # Mock cycling entities
    mock_daily_sensor = Mock()
    mock_daily_sensor.entity_id = "sensor.test_heating_cycling_daily"
    mock_daily_sensor._sensor_id = "heating_cycling_daily"
    
    mock_yesterday_sensor = Mock()
    mock_yesterday_sensor.entity_id = "sensor.test_heating_cycling_yesterday"
    mock_yesterday_sensor._sensor_id = "heating_cycling_yesterday"
    mock_yesterday_sensor.set_cycling_value = Mock()
    
    # Mock hass.data structure
    mock_hass.data = {
        "lambda_heat_pumps": {
            mock_entry.entry_id: {
                "cycling_entities": {
                    "sensor.test_heating_cycling_daily": mock_daily_sensor,
                    "sensor.test_heating_cycling_yesterday": mock_yesterday_sensor,
                }
            }
        }
    }
    
    # Mock hass.states.get to return a daily value
    mock_state = Mock()
    mock_state.state = "42"
    mock_hass.states.get.return_value = mock_state
    
    # Call the function
    _update_yesterday_sensors(mock_hass, mock_entry.entry_id)
    
    # Verify that set_cycling_value was called on the yesterday sensor
    mock_yesterday_sensor.set_cycling_value.assert_called_once_with(42)


def test_update_yesterday_sensors_no_entities(mock_hass, mock_entry):
    """Test _update_yesterday_sensors when no cycling entities exist."""
    from custom_components.lambda_heat_pumps.automations import _update_yesterday_sensors
    
    # Mock empty hass.data
    mock_hass.data = {}
    
    # This should not raise an exception
    _update_yesterday_sensors(mock_hass, mock_entry.entry_id)


def test_update_yesterday_sensors_unavailable_state(mock_hass, mock_entry):
    """Test _update_yesterday_sensors with unavailable state."""
    from custom_components.lambda_heat_pumps.automations import _update_yesterday_sensors
    
    # Mock cycling entities
    mock_daily_sensor = Mock()
    mock_daily_sensor.entity_id = "sensor.test_heating_cycling_daily"
    mock_daily_sensor._sensor_id = "heating_cycling_daily"
    
    mock_yesterday_sensor = Mock()
    mock_yesterday_sensor.entity_id = "sensor.test_heating_cycling_yesterday"
    mock_yesterday_sensor._sensor_id = "heating_cycling_yesterday"
    mock_yesterday_sensor.set_cycling_value = Mock()
    
    # Mock hass.data structure
    mock_hass.data = {
        "lambda_heat_pumps": {
            mock_entry.entry_id: {
                "cycling_entities": {
                    "sensor.test_heating_cycling_daily": mock_daily_sensor,
                    "sensor.test_heating_cycling_yesterday": mock_yesterday_sensor,
                }
            }
        }
    }
    
    # Mock hass.states.get to return unavailable state
    mock_state = Mock()
    mock_state.state = "unavailable"
    mock_hass.states.get.return_value = mock_state
    
    # Call the function
    _update_yesterday_sensors(mock_hass, mock_entry.entry_id)
    
    # Verify that set_cycling_value was NOT called due to unavailable state
    mock_yesterday_sensor.set_cycling_value.assert_not_called()


# Integration Test für das Yesterday-Sensor-Problem
@pytest.mark.asyncio
async def test_yesterday_sensor_problem_detection(mock_hass, mock_entry, mock_coordinator):
    """Test that detects the specific problem where yesterday sensors are not in cycling_entities."""
    from custom_components.lambda_heat_pumps.const import DOMAIN
    
    mock_add_entities = AsyncMock()
    mock_hass.data[DOMAIN] = {mock_entry.entry_id: {"coordinator": mock_coordinator}}
    
    with patch("custom_components.lambda_heat_pumps.sensor.LambdaCyclingSensor") as mock_cycling_class, \
         patch("custom_components.lambda_heat_pumps.sensor.LambdaYesterdaySensor") as mock_yesterday_class, \
         patch("custom_components.lambda_heat_pumps.sensor.LambdaSensor") as mock_sensor_class, \
         patch("custom_components.lambda_heat_pumps.automations.setup_cycling_automations") as mock_automations:
        
        # Create mock sensors
        mock_yesterday_sensor = Mock()
        mock_yesterday_sensor.entity_id = "sensor.test_heating_cycling_yesterday"
        mock_yesterday_sensor._sensor_id = "heating_cycling_yesterday"
        mock_yesterday_class.return_value = mock_yesterday_sensor
        
        mock_cycling_sensor = Mock()
        mock_cycling_sensor.entity_id = "sensor.test_heating_cycling_total"
        mock_cycling_sensor._sensor_id = "heating_cycling_total"
        mock_cycling_class.return_value = mock_cycling_sensor
        
        mock_regular_sensor = Mock()
        mock_regular_sensor.entity_id = "sensor.test_hp1_temperature"
        mock_sensor_class.return_value = mock_regular_sensor
        
        await async_setup_entry(mock_hass, mock_entry, mock_add_entities)
        
        # This test verifies that the fix is working
        cycling_entities = mock_hass.data["lambda_heat_pumps"][mock_entry.entry_id]["cycling_entities"]
        
        # Count yesterday sensors
        yesterday_count = sum(1 for entity_id in cycling_entities.keys() if "yesterday" in entity_id)
        
        # With the fix, we should have yesterday sensors in cycling_entities
        assert yesterday_count > 0, "Yesterday sensors should be present in cycling_entities after the fix"
        
        # Verify specific yesterday sensor is there
        assert "sensor.test_hp1_heating_cycling_yesterday" in cycling_entities