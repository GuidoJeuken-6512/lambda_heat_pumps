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
    assert sensor._attr_unique_id == "test_heating_cycling_yesterday"
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
    
    # Test daily reset (async method) - jetzt _handle_reset für alle Perioden
    import asyncio
    asyncio.run(daily_sensor._handle_reset("test_entry"))
    assert daily_sensor._cycling_value == 0
    daily_sensor.async_write_ha_state.assert_called_once()
    
    # Test with wrong entry_id
    daily_sensor._cycling_value = 50
    daily_sensor.async_write_ha_state.reset_mock()
    asyncio.run(daily_sensor._handle_reset("wrong_entry"))
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
    
    # Test 2h reset (async method) - jetzt _handle_reset für alle Perioden
    import asyncio
    asyncio.run(sensor._handle_reset("test_entry"))
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
    
    # Test 4h reset (async method) - jetzt _handle_reset für alle Perioden
    import asyncio
    asyncio.run(sensor._handle_reset("test_entry"))
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
    
    # Test monthly reset (async method) - jetzt _handle_reset für alle Perioden
    import asyncio
    asyncio.run(sensor._handle_reset("test_entry"))
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
    assert sensor._attr_unique_id == "test_compressor_start_cycling_total"
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
    asyncio.run(sensor._handle_reset("test_entry"))
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
    asyncio.run(sensor._handle_reset("test_entry"))
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
         patch("custom_components.lambda_heat_pumps.reset_manager.ResetManager") as mock_reset_manager_class:
        
        # Create mock sensor instances
        mock_cycling_sensor = Mock()
        mock_cycling_sensor.entity_id = "sensor.test_heating_cycling_total"
        mock_cycling_sensor._sensor_id = "heating_cycling_total"
        mock_cycling_class.return_value = mock_cycling_sensor
        
        # Create mock sensors with correct entity_id format (including hp_index)
        # Make yesterday_class return sensors with proper entity_id format
        def yesterday_sensor_side_effect(*args, **kwargs):
            sensor_id = kwargs.get('sensor_id', args[2] if len(args) > 2 else 'unknown')
            hp_idx = kwargs.get('hp_index', args[-2] if len(args) >= 8 else 1)
            mode = sensor_id.replace('_cycling_yesterday', '')
            mock_yesterday = Mock()
            mock_yesterday.entity_id = f"sensor.test_hp{hp_idx}_{mode}_cycling_yesterday"
            mock_yesterday._sensor_id = sensor_id
            return mock_yesterday
        
        mock_yesterday_class.side_effect = yesterday_sensor_side_effect
        
        # Make cycling_class return different sensors based on sensor_id with proper entity_id format
        def cycling_sensor_side_effect(*args, **kwargs):
            sensor_id = kwargs.get('sensor_id', args[2] if len(args) > 2 else 'unknown')
            hp_idx = kwargs.get('hp_index', args[-1] if len(args) >= 8 else 1)
            
            if 'daily' in sensor_id:
                mode = sensor_id.replace('_cycling_daily', '')
                mock_daily = Mock()
                mock_daily.entity_id = f"sensor.test_hp{hp_idx}_{mode}_cycling_daily"
                mock_daily._sensor_id = sensor_id
                return mock_daily
            elif '2h' in sensor_id:
                mode = sensor_id.replace('_cycling_2h', '')
                mock_2h = Mock()
                mock_2h.entity_id = f"sensor.test_hp{hp_idx}_{mode}_cycling_2h"
                mock_2h._sensor_id = sensor_id
                return mock_2h
            elif '4h' in sensor_id:
                mode = sensor_id.replace('_cycling_4h', '')
                mock_4h = Mock()
                mock_4h.entity_id = f"sensor.test_hp{hp_idx}_{mode}_cycling_4h"
                mock_4h._sensor_id = sensor_id
                return mock_4h
            elif 'monthly' in sensor_id:
                mode = sensor_id.replace('_cycling_monthly', '')
                mock_monthly = Mock()
                mock_monthly.entity_id = f"sensor.test_hp{hp_idx}_{mode}_cycling_monthly"
                mock_monthly._sensor_id = sensor_id
                return mock_monthly
            else:
                # Total sensors
                mode = sensor_id.replace('_cycling_total', '')
                mock_total = Mock()
                mock_total.entity_id = f"sensor.test_hp{hp_idx}_{mode}_cycling_total"
                mock_total._sensor_id = sensor_id
                return mock_total
        
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
         patch("custom_components.lambda_heat_pumps.reset_manager.ResetManager") as mock_reset_manager_class:
        
        # Create mock yesterday sensor with proper entity_id format
        def yesterday_sensor_side_effect(*args, **kwargs):
            sensor_id = kwargs.get('sensor_id', args[2] if len(args) > 2 else 'unknown')
            hp_idx = kwargs.get('hp_index', args[-2] if len(args) >= 8 else 1)
            mode = sensor_id.replace('_cycling_yesterday', '')
            mock_yesterday = Mock()
            mock_yesterday.entity_id = f"sensor.test_hp{hp_idx}_{mode}_cycling_yesterday"
            mock_yesterday._sensor_id = sensor_id
            return mock_yesterday
        
        mock_yesterday_class.side_effect = yesterday_sensor_side_effect
        
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
@pytest.mark.asyncio
async def test_update_yesterday_sensors_function(mock_hass, mock_entry):
    """Test the _update_yesterday_sensors_async function from automations."""
    from custom_components.lambda_heat_pumps.automations import _update_yesterday_sensors_async
    
    # Mock cycling entities - use proper entity_id format with hp1
    mock_daily_sensor = Mock()
    mock_daily_sensor.entity_id = "sensor.test_hp1_heating_cycling_daily"
    mock_daily_sensor._sensor_id = "heating_cycling_daily"
    
    mock_yesterday_sensor = Mock()
    mock_yesterday_sensor.entity_id = "sensor.test_hp1_heating_cycling_yesterday"
    mock_yesterday_sensor._sensor_id = "heating_cycling_yesterday"
    # set_cycling_value is async, so use AsyncMock
    from unittest.mock import AsyncMock
    mock_yesterday_sensor.set_cycling_value = AsyncMock()
    
    # Mock hass.data structure
    mock_hass.data = {
        "lambda_heat_pumps": {
            mock_entry.entry_id: {
                "cycling_entities": {
                    "sensor.test_hp1_heating_cycling_daily": mock_daily_sensor,
                    "sensor.test_hp1_heating_cycling_yesterday": mock_yesterday_sensor,
                }
            }
        }
    }
    
    # Mock hass.states.get to return a daily value
    mock_state = Mock()
    mock_state.state = "42"
    mock_hass.states.get.return_value = mock_state
    
    # Call the async function
    await _update_yesterday_sensors_async(mock_hass, mock_entry.entry_id)
    
    # Verify that set_cycling_value was called on the yesterday sensor
    mock_yesterday_sensor.set_cycling_value.assert_called_once_with(42)



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
         patch("custom_components.lambda_heat_pumps.reset_manager.ResetManager") as mock_reset_manager_class:
        
        # Create mock sensors with proper entity_id format
        def yesterday_sensor_side_effect(*args, **kwargs):
            sensor_id = kwargs.get('sensor_id', args[2] if len(args) > 2 else 'unknown')
            hp_idx = kwargs.get('hp_index', args[-2] if len(args) >= 8 else 1)
            mode = sensor_id.replace('_cycling_yesterday', '')
            mock_yesterday = Mock()
            mock_yesterday.entity_id = f"sensor.test_hp{hp_idx}_{mode}_cycling_yesterday"
            mock_yesterday._sensor_id = sensor_id
            return mock_yesterday
        
        mock_yesterday_class.side_effect = yesterday_sensor_side_effect
        
        def cycling_sensor_side_effect(*args, **kwargs):
            sensor_id = kwargs.get('sensor_id', args[2] if len(args) > 2 else 'unknown')
            hp_idx = kwargs.get('hp_index', args[-1] if len(args) >= 8 else 1)
            mode = sensor_id.replace('_cycling_total', '')
            mock_total = Mock()
            mock_total.entity_id = f"sensor.test_hp{hp_idx}_{mode}_cycling_total"
            mock_total._sensor_id = sensor_id
            return mock_total
        
        mock_cycling_class.side_effect = cycling_sensor_side_effect
        
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


@pytest.mark.asyncio
async def test_cycling_offset_application(mock_entry, mock_coordinator):
    """Test that cycling offsets from lambda_wp_config.yaml are correctly applied to cycling total sensors."""
    from custom_components.lambda_heat_pumps.sensor import LambdaCyclingSensor
    from homeassistant.helpers.restore_state import RestoreStateData
    
    # Create a cycling total sensor
    sensor = LambdaCyclingSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_total",
        name="Heating Cycling Total",
        entity_id="sensor.test_hp1_heating_cycling_total",
        unique_id="test_hp1_heating_cycling_total",
        unit="cycles",
        state_class="total_increasing",
        device_class=None,
        device_type="hp",
        hp_index=1,
    )
    
    sensor.async_write_ha_state = Mock()
    
    # Mock load_lambda_config to return cycling offsets from config
    mock_config = {
        "cycling_offsets": {
            "hp1": {
                "heating_cycling_total": 1500,  # Offset from config
                "hot_water_cycling_total": 0,
                "cooling_cycling_total": 0,
                "defrost_cycling_total": 0,
            }
        }
    }
    
    # Create a mock last_state with initial value
    mock_last_state = Mock()
    mock_last_state.state = "100"  # Initial value from previous state
    mock_last_state.attributes = {"applied_offset": 0}  # No offset applied yet
    
    with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value=mock_config):
        # Call restore_state which triggers _apply_cycling_offset
        await sensor.restore_state(mock_last_state)
        
        # Verify offset was applied: restored value (100) + offset (1500) = 1600
        assert sensor._cycling_value == 1600
        assert sensor._applied_offset == 1500
        sensor.async_write_ha_state.assert_called()


@pytest.mark.asyncio
async def test_cycling_offset_no_config(mock_entry, mock_coordinator):
    """Test that cycling sensor works correctly when no offsets are configured."""
    from custom_components.lambda_heat_pumps.sensor import LambdaCyclingSensor
    
    sensor = LambdaCyclingSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_total",
        name="Heating Cycling Total",
        entity_id="sensor.test_hp1_heating_cycling_total",
        unique_id="test_hp1_heating_cycling_total",
        unit="cycles",
        state_class="total_increasing",
        device_class=None,
        device_type="hp",
        hp_index=1,
    )
    
    sensor.async_write_ha_state = Mock()
    
    # Mock config with no cycling_offsets
    mock_config = {}
    
    # Create a mock last_state with initial value
    mock_last_state = Mock()
    mock_last_state.state = "100"
    mock_last_state.attributes = {"applied_offset": 0}
    
    with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value=mock_config):
        await sensor.restore_state(mock_last_state)
        
        # Value should remain unchanged when no offset configured
        assert sensor._cycling_value == 100
        assert sensor._applied_offset == 0


# ===========================================================================
# Regression tests: NameError bug in increment_cycling_counter
#
# Pre-fix: cycling_entity was referenced on line 871 before being defined on
# line 884. On the first iteration of the for-sensor_id loop Python raised
# NameError. The exception was silently swallowed in _async_fast_update at
# debug level — edges were detected but counters were never incremented.
#
# Secondary effect: _last_operating_state was never updated after the failed
# call, so the same edge was re-detected every 2 s indefinitely.
# ===========================================================================

def _make_increment_hass(entity_id, fake_entity, state_value="0"):
    """Return a minimal hass mock wired up for increment_cycling_counter tests."""
    hass = Mock()
    hass.data = {
        "lambda_heat_pumps": {
            "test_entry": {
                "cycling_entities": {entity_id: fake_entity}
            }
        }
    }
    state_obj = Mock()
    state_obj.state = str(state_value)
    state_obj.attributes = {}
    hass.states.get = Mock(return_value=state_obj)
    return hass, state_obj


class TestIncrementCyclingCounterEntityLookupOrder:
    """
    Ensure cycling_entity is looked up BEFORE the current counter value is read.

    The old code used cycling_entity on line 871 but only defined it on line 884.
    Moving the lookup before the read fixes the NameError and ensures the entity's
    authoritative _cycling_value is used instead of the potentially stale HA state.
    """

    @pytest.mark.asyncio
    async def test_no_name_error_on_first_call(self, mock_entry, mock_coordinator):
        """increment_cycling_counter must not raise NameError on the first invocation.

        Pre-fix: cycling_entity was used before definition → NameError on first
        loop iteration → exception silently caught in _async_fast_update.
        """
        from custom_components.lambda_heat_pumps.utils import increment_cycling_counter

        entity_id = "sensor.eu08l_hp1_heating_cycling_total"

        class FakeCyclingEntity:
            _cycling_value = 10
            def set_cycling_value(self, value): pass

        hass, _ = _make_increment_hass(entity_id, FakeCyclingEntity(), state_value="10")

        mock_registry = Mock()
        mock_registry.async_get = Mock(return_value=Mock())

        with patch(
            "custom_components.lambda_heat_pumps.utils.async_get_entity_registry",
            return_value=mock_registry,
        ), patch(
            "custom_components.lambda_heat_pumps.utils.async_update_entity",
            new_callable=AsyncMock,
        ), patch(
            "custom_components.lambda_heat_pumps.utils._get_coordinator",
            return_value=None,
        ):
            try:
                await increment_cycling_counter(
                    hass=hass, mode="heating", hp_index=1,
                    name_prefix="eu08l", use_legacy_modbus_names=True,
                )
            except NameError as exc:
                pytest.fail(
                    f"NameError raised in increment_cycling_counter: {exc}. "
                    "Regression: cycling_entity used before being defined."
                )

    @pytest.mark.asyncio
    async def test_entity_cycling_value_takes_precedence_over_ha_state(self, mock_entry, mock_coordinator):
        """Entity._cycling_value (50) must be used, not state_obj.state (200).

        This is the direct regression test: with the old code the NameError
        prevented the entity lookup entirely, so the increment silently failed.
        With the fix the entity is found first, _cycling_value=50 is used, and
        the result is 51 — not 201 (from HA state) and not an exception.
        """
        from custom_components.lambda_heat_pumps.utils import increment_cycling_counter

        received_values = []

        class FakeCyclingEntity:
            _cycling_value = 50  # authoritative internal counter

            def set_cycling_value(self, value):
                received_values.append(value)

        entity_id = "sensor.eu08l_hp1_heating_cycling_total"
        # HA state reports 200 — wrong result if entity lookup fails
        hass, _ = _make_increment_hass(entity_id, FakeCyclingEntity(), state_value="200")

        mock_registry = Mock()
        mock_registry.async_get = Mock(return_value=Mock())

        with patch(
            "custom_components.lambda_heat_pumps.utils.async_get_entity_registry",
            return_value=mock_registry,
        ), patch(
            "custom_components.lambda_heat_pumps.utils.async_update_entity",
            new_callable=AsyncMock,
        ), patch(
            "custom_components.lambda_heat_pumps.utils._get_coordinator",
            return_value=None,
        ):
            await increment_cycling_counter(
                hass=hass, mode="heating", hp_index=1,
                name_prefix="eu08l", use_legacy_modbus_names=True,
            )

        assert any(v == 51 for v in received_values), (
            f"Expected 51 (entity._cycling_value=50 + 1) but got {received_values}. "
            "Regression: entity lookup happens after current value is read, or entity not found."
        )
        assert not any(v == 201 for v in received_values), (
            "Regression: HA state (200) was used instead of entity._cycling_value (50). "
            "Entity lookup must happen BEFORE reading current value."
        )

    @pytest.mark.asyncio
    async def test_ha_state_used_as_fallback_when_entity_has_no_cycling_value(self, mock_entry, mock_coordinator):
        """When entity exists but has no _cycling_value, HA state is the fallback."""
        from custom_components.lambda_heat_pumps.utils import increment_cycling_counter

        received_values = []

        class FakeCyclingEntity:
            # No _cycling_value attribute
            def set_cycling_value(self, value):
                received_values.append(value)

        entity_id = "sensor.eu08l_hp1_heating_cycling_total"
        hass, _ = _make_increment_hass(entity_id, FakeCyclingEntity(), state_value="300")

        mock_registry = Mock()
        mock_registry.async_get = Mock(return_value=Mock())

        with patch(
            "custom_components.lambda_heat_pumps.utils.async_get_entity_registry",
            return_value=mock_registry,
        ), patch(
            "custom_components.lambda_heat_pumps.utils.async_update_entity",
            new_callable=AsyncMock,
        ), patch(
            "custom_components.lambda_heat_pumps.utils._get_coordinator",
            return_value=None,
        ):
            await increment_cycling_counter(
                hass=hass, mode="heating", hp_index=1,
                name_prefix="eu08l", use_legacy_modbus_names=True,
            )

        assert any(v == 301 for v in received_values), (
            f"Expected 301 (HA state 300 + 1) but got {received_values}."
        )


class TestEdgeDetectionStateUpdate:
    """
    Regression tests for the secondary consequence of the NameError bug.

    Pre-fix: NameError in increment_cycling_counter exited
    _run_cycling_edge_detection before the line
        self._last_operating_state[str(hp_idx)] = op_state_val
    was reached. The same transition was therefore re-detected on every
    subsequent fast poll (every 2 s) without ever incrementing the counter.
    """

    def _make_coordinator(self, last_op_state_val):
        """Return a minimal coordinator mock for _run_cycling_edge_detection."""
        coordinator = Mock()
        coordinator._last_operating_state = {"1": last_op_state_val}
        coordinator._last_compressor_rating = {}
        coordinator._initialization_complete = True
        coordinator._cycling_entities_ready = Mock(return_value=True)
        coordinator._persist_dirty = False
        coordinator.entry = Mock()
        coordinator.entry.data = {"num_hps": 1, "name": "eu08l"}
        coordinator.hass = Mock()
        coordinator._use_legacy_names = True
        # _run_cycling_edge_detection uses setattr/getattr for "{mode}_cycles" dicts.
        # Pre-seed them so item assignment works (Mock attributes don't support it).
        for mode in ("heating", "hot_water", "cooling", "defrost", "compressor_start"):
            setattr(coordinator, f"{mode}_cycles", {})
        return coordinator

    @pytest.mark.asyncio
    async def test_last_operating_state_updated_after_successful_edge(self):
        """_last_operating_state must be updated after a successful edge + increment.

        Simulates STBY-FROST (8) → CH (1): heating edge detected.
        After the call, _last_operating_state["1"] must be 1, not still 8.
        """
        from custom_components.lambda_heat_pumps.coordinator import LambdaDataUpdateCoordinator

        coordinator = self._make_coordinator(last_op_state_val=8)  # STBY-FROST

        with patch(
            "custom_components.lambda_heat_pumps.coordinator.increment_cycling_counter",
            new_callable=AsyncMock,
        ) as mock_increment:
            await LambdaDataUpdateCoordinator._run_cycling_edge_detection(
                coordinator,
                {"hp1_operating_state": 1},   # transition to CH
            )

        assert coordinator._last_operating_state["1"] == 1, (
            f"Regression: _last_operating_state not updated after edge detection "
            f"(got {coordinator._last_operating_state['1']!r}, expected 1). "
            "Pre-fix, an exception exited the function before the state was written — "
            "causing the same edge to be re-detected every 2 s indefinitely."
        )
        assert mock_increment.called, (
            "increment_cycling_counter was not called for the heating edge (STBY-FROST→CH)."
        )

    @pytest.mark.asyncio
    async def test_last_operating_state_not_updated_when_no_edge(self):
        """_last_operating_state is updated to current value even when no edge occurs.

        Ensures that a state update without a mode change still moves
        _last_operating_state forward so stale transitions don't fire later.
        """
        from custom_components.lambda_heat_pumps.coordinator import LambdaDataUpdateCoordinator

        coordinator = self._make_coordinator(last_op_state_val=8)  # STBY-FROST

        with patch(
            "custom_components.lambda_heat_pumps.coordinator.increment_cycling_counter",
            new_callable=AsyncMock,
        ) as mock_increment:
            # State stays at STBY-FROST (8) — no edge
            await LambdaDataUpdateCoordinator._run_cycling_edge_detection(
                coordinator,
                {"hp1_operating_state": 8},
            )

        # State must still be updated (to 8)
        assert coordinator._last_operating_state["1"] == 8
        # No increment must have fired
        assert not mock_increment.called, (
            "increment_cycling_counter fired without a mode transition."
        )