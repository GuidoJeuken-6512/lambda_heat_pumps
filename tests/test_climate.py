# File: tests/test_climate.py
"""Tests for the Lambda Heat Pumps climate platform."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.climate import HVACMode
from homeassistant.const import UnitOfTemperature

from custom_components.lambda_heat_pumps.climate import (
    LambdaClimateEntity,
    async_setup_entry,
)
from custom_components.lambda_heat_pumps.const import DOMAIN

pytestmark = pytest.mark.asyncio


class MockConfigEntry:
    """Mock config entry for testing."""

    def __init__(self, domain, data, entry_id):
        self.domain = domain
        self.data = data
        self.entry_id = entry_id
        self.options = {}


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "192.168.1.100",
            "port": 502,
            "unit_id": 1,
            "num_boil": 1,
            "num_hc": 1,
        },
        entry_id="test_entry_id",
    )


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.data = {
        "temperature": 20.0,
        "target_temperature": 22.0,
        "hvac_mode": HVACMode.HEAT,
        "boil1_actual_high_temperature": 55.0,
        "boil1_target_high_temperature": 60.0,
    }
    return coordinator


@pytest.mark.asyncio
async def test_climate_setup(mock_hass, mock_config_entry, mock_coordinator):
    """Test climate entity setup."""
    from unittest.mock import AsyncMock
    
    mock_hass.data = {
        DOMAIN: {mock_config_entry.entry_id: {"coordinator": mock_coordinator}}
    }
    
    mock_config_entry.data = {
        "name": "test",
        "num_boil": 1,
        "num_hc": 1,
        "firmware_version": "V1.0.0",
    }
    mock_config_entry.options = {}
    
    mock_add_entities = AsyncMock()

    with patch(
        "custom_components.lambda_heat_pumps.climate.LambdaClimateEntity"
    ) as mock_climate:
        instance = mock_climate.return_value
        instance._attr_name = "Test Climate"
        instance._attr_unique_id = "test_climate"
        instance._attr_hvac_mode = HVACMode.HEAT
        instance._attr_hvac_modes = [HVACMode.HEAT]
        instance._attr_min_temp = 5
        instance._attr_max_temp = 35
        instance._attr_target_temperature_step = 0.5
        instance._attr_temperature_unit = UnitOfTemperature.CELSIUS

        await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)
        
        # Verify entities were added
        mock_add_entities.assert_called_once()


@pytest.mark.asyncio
async def test_lambda_climate_entity_properties():
    """Test properties of LambdaClimateEntity."""
    coordinator_mock = MagicMock()
    coordinator_mock.data = {
        "boil1_actual_high_temperature": 60,
        "boil1_target_high_temperature": 65,
    }

    entry_mock = MagicMock()
    entry_mock.entry_id = "test_entry"
    entry_mock.data = {"name": "test", "use_legacy_modbus_names": True}
    entry_mock.options = {}

    device_type = "hot_water"
    idx = 1
    base_address = 2000

    entity = LambdaClimateEntity(
        coordinator_mock,
        entry_mock,
        device_type,
        idx,
        base_address,
    )
    assert entity is not None
    # Entity name no longer includes device prefix (BOIL1), just the sensor name
    assert entity._attr_name == "Hot Water"
    # unique_id includes name_prefix when use_legacy_modbus_names is True
    assert entity._attr_unique_id == "test_boil1_hot_water"
    assert entity._attr_min_temp == 25
    assert entity._attr_max_temp == 65
    assert entity.current_temperature == 60
    assert entity.target_temperature == 65


@pytest.mark.asyncio
async def test_lambda_climate_entity_set_temperature():
    """Test set temperature method of LambdaClimateEntity."""
    coordinator_mock = MagicMock()
    coordinator_mock.data = {}
    coordinator_mock.client = MagicMock()
    # async_write_registers uses await client.write_registers, so it must be AsyncMock
    coordinator_mock.client.write_registers = AsyncMock(
        return_value=MagicMock(isError=lambda: False)
    )
    coordinator_mock.async_refresh = AsyncMock()

    entry_mock = MagicMock()
    entry_mock.entry_id = "test_entry"
    entry_mock.data = {"name": "test", "slave_id": 1}
    entry_mock.options = {}

    hass_mock = MagicMock()
    hass_mock.async_add_executor_job = AsyncMock(
        return_value=MagicMock(isError=lambda: False)
    )
    hass_mock.config = MagicMock()
    hass_mock.config.units = MagicMock()
    hass_mock.config.units.temperature_unit = "°C"

    device_type = "hot_water"
    idx = 1
    base_address = 2000

    entity = LambdaClimateEntity(
        coordinator_mock,
        entry_mock,
        device_type,
        idx,
        base_address,
    )
    entity.hass = hass_mock

    # Mock async_write_ha_state um Home Assistant Konfiguration zu vermeiden
    with patch.object(entity, "async_write_ha_state"):
        # Patch async_write_registers to verify it's called correctly
        with patch("custom_components.lambda_heat_pumps.climate.async_write_registers") as mock_write:
            mock_write.return_value = MagicMock(isError=lambda: False)
            await entity.async_set_temperature(temperature=60)

            # Verify async_write_registers was called with correct parameters
            mock_write.assert_called_once()
            call_args = mock_write.call_args
            # client (coordinator_mock.client)
            assert call_args[0][0] == coordinator_mock.client
            # base_address + relative_set_address (sollte 2050 sein für hot_water)
            assert call_args[0][1] == 2050
            # Temperatur * scale (10.0) - temperature 60 * scale 10 = 600
            assert call_args[0][2] == [600]
            assert call_args[0][3] == 1  # slave_id

    # Überprüfe, ob der Coordinator-Cache aktualisiert wurde
    assert coordinator_mock.data["boil1_target_high_temperature"] == 60

    # Überprüfe, ob async_refresh aufgerufen wurde
    coordinator_mock.async_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_lambda_climate_entity_device_info():
    """Test device info method of LambdaClimateEntity."""
    coordinator_mock = MagicMock()
    coordinator_mock.data = {}

    entry_mock = MagicMock()
    entry_mock.entry_id = "test_entry"
    entry_mock.data = {"name": "test"}
    entry_mock.options = {}
    entry_mock.domain = "lambda_heat_pumps"

    device_type = "hot_water"
    idx = 1
    base_address = 2000

    entity = LambdaClimateEntity(
        coordinator_mock,
        entry_mock,
        device_type,
        idx,
        base_address,
    )

    device_info = entity.device_info
    assert device_info is not None
    # For hot_water, device_type is "boil", so it should return subdevice info
    # Subdevice identifier: (domain, entry_id, device_type, device_index)
    assert device_info["identifiers"] == {("lambda_heat_pumps", "test_entry", "boil", 1)}
    assert device_info["via_device"] == ("lambda_heat_pumps", "test_entry")
    assert "Boiler1" in device_info["name"] or "test - Boiler1" in device_info["name"]
