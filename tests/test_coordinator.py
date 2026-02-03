"""Test the coordinator module."""

import os
from datetime import timedelta
from types import SimpleNamespace
from io import StringIO
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, Mock, patch, mock_open

import pytest
import yaml
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from custom_components.lambda_heat_pumps.const import (
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    HP_SENSOR_TEMPLATES,
    SENSOR_TYPES,
)
from custom_components.lambda_heat_pumps.coordinator import LambdaDataUpdateCoordinator
from tests.conftest import DummyLoop


@pytest.fixture
def mock_hass():
    """Create a mock hass object."""
    hass = MagicMock()
    hass.config = MagicMock()
    hass.config.config_dir = "/tmp/test_config"
    hass.config.language = "en"
    hass.config.locale = SimpleNamespace(language="en")
    hass.loop = DummyLoop()
    hass.is_running = True
    hass.is_stopping = False
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
    }
    entry.options = {"update_interval": 30, "write_interval": 30}
    return entry


def test_coordinator_init(mock_hass, mock_entry):
    """Test coordinator initialization."""
    coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)

    assert coordinator.host == "192.168.1.100"
    assert coordinator.port == 502
    assert coordinator.slave_id == 1
    assert coordinator.debug_mode is False
    assert coordinator.client is None
    assert coordinator.config_entry_id == "test_entry"
    assert coordinator.hass == mock_hass
    assert coordinator.entry == mock_entry
    assert coordinator.name == "Lambda Coordinator"
    assert coordinator.update_interval == timedelta(seconds=30)
    assert coordinator._config_dir == "/tmp/test_config"
    # Test _last_state initialization for HP_STATE flank detection
    assert hasattr(coordinator, "_last_state")
    assert isinstance(coordinator._last_state, dict)
    assert coordinator._last_state == {}


def test_coordinator_init_with_debug_mode(mock_hass, mock_entry):
    """Test coordinator initialization with debug mode."""
    mock_entry.data["debug_mode"] = True

    coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)

    assert coordinator.debug_mode is True
    assert coordinator.hass == mock_hass
    assert coordinator.entry == mock_entry
    assert coordinator.name == "Lambda Coordinator"
    assert coordinator.update_interval == timedelta(seconds=30)
    assert coordinator._config_dir == "/tmp/test_config"


def test_coordinator_init_with_default_update_interval(mock_hass, mock_entry):
    """Test coordinator initialization with default update interval."""
    del mock_entry.data["update_interval"]

    coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)

    assert coordinator.update_interval == timedelta(seconds=DEFAULT_UPDATE_INTERVAL)
    assert coordinator.hass == mock_hass
    assert coordinator.entry == mock_entry
    assert coordinator.name == "Lambda Coordinator"
    assert coordinator._config_dir == "/tmp/test_config"


@pytest.mark.asyncio
async def test_coordinator_async_init_success(mock_hass, mock_entry):
    """Test successful async initialization."""
    mock_hass.async_add_executor_job = AsyncMock()

    with patch(
        "custom_components.lambda_heat_pumps.coordinator.os.makedirs"
    ) as mock_makedirs:
        with patch(
            "custom_components.lambda_heat_pumps.coordinator.load_disabled_registers",
            return_value=set(),
        ) as mock_load_disabled:
            with patch.object(
                LambdaDataUpdateCoordinator, "_load_sensor_overrides", return_value={}
            ) as mock_load_overrides, patch.object(
                LambdaDataUpdateCoordinator, "_connect", AsyncMock(return_value=None)
            ) as mock_connect:
                coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
                await coordinator.async_init()

                mock_hass.async_add_executor_job.assert_called()
                mock_load_disabled.assert_called_once_with(mock_hass)
                mock_load_overrides.assert_called_once()
                mock_connect.assert_called_once()
                assert coordinator.disabled_registers == set()
                assert coordinator.sensor_overrides == {}


@pytest.mark.asyncio
async def test_coordinator_async_init_exception(mock_hass, mock_entry):
    """Test async initialization with exception."""
    mock_hass.async_add_executor_job = AsyncMock(
        side_effect=OSError("Permission denied")
    )

    with patch(
        "custom_components.lambda_heat_pumps.coordinator.os.makedirs",
        side_effect=OSError("Permission denied"),
    ), patch.object(
        LambdaDataUpdateCoordinator, "_connect", AsyncMock(return_value=None)
    ):
        coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
        with pytest.raises(OSError):
            await coordinator.async_init()


@pytest.mark.asyncio
async def test_ensure_config_dir_success(mock_hass, mock_entry):
    """Test successful config directory creation."""
    mock_hass.async_add_executor_job = AsyncMock()

    with patch(
        "custom_components.lambda_heat_pumps.coordinator.os.makedirs"
    ) as mock_makedirs:
        coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
        await coordinator._ensure_config_dir()

        # Verify that async_add_executor_job was called (which calls makedirs internally)
        mock_hass.async_add_executor_job.assert_called()


@pytest.mark.asyncio
async def test_ensure_config_dir_exception(mock_hass, mock_entry):
    """Test config directory creation with exception."""
    mock_hass.async_add_executor_job = AsyncMock(
        side_effect=OSError("Permission denied")
    )

    with patch(
        "custom_components.lambda_heat_pumps.coordinator.os.makedirs",
        side_effect=OSError("Permission denied"),
    ):
        coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
        with pytest.raises(OSError):
            await coordinator._ensure_config_dir()


@pytest.mark.asyncio
async def test_is_register_disabled_not_initialized(mock_hass, mock_entry):
    """Test register disabled check when not initialized."""
    coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)

    # Should return False when not initialized
    assert coordinator.is_register_disabled(1000) is False


@pytest.mark.asyncio
async def test_is_register_disabled_true(mock_hass, mock_entry):
    """Test register disabled check when register is disabled."""
    coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
    coordinator.disabled_registers = {1000, 2000}

    assert coordinator.is_register_disabled(1000) is True
    assert coordinator.is_register_disabled(2000) is True
    assert coordinator.is_register_disabled(3000) is False


@pytest.mark.asyncio
async def test_is_register_disabled_false(mock_hass, mock_entry):
    """Test register disabled check when register is not disabled."""
    coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
    coordinator.disabled_registers = {1000, 2000}

    assert coordinator.is_register_disabled(3000) is False
    assert coordinator.is_register_disabled(4000) is False


@pytest.mark.asyncio
async def test_async_update_data_success(mock_hass, mock_entry):
    """Test successful data update."""
    mock_client = AsyncMock()
    mock_result = Mock()
    mock_result.isError.return_value = False
    mock_result.registers = [100]
    mock_client.read_holding_registers = AsyncMock(return_value=mock_result)

    coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
    coordinator.client = mock_client
    coordinator.disabled_registers = set()

    result = await coordinator._async_update_data()

    assert result is not None
    mock_client.read_holding_registers.assert_called()


@pytest.mark.asyncio
async def test_async_update_data_no_client(mock_hass, mock_entry):
    """Test data update when no client is available (Coordinator liefert weiterhin Data-Dict)."""
    coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
    coordinator.client = None

    result = await coordinator._async_update_data()

    # Coordinator gibt bei fehlendem Client ein Data-Dict zurück (kein None)
    assert result is not None
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_async_update_data_disabled_register(mock_hass, mock_entry):
    """Test data update with disabled register."""
    mock_client = AsyncMock()
    mock_result = Mock()
    mock_result.isError.return_value = False
    mock_result.registers = [100]
    mock_client.read_holding_registers = AsyncMock(return_value=mock_result)

    coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
    coordinator.client = mock_client
    coordinator.disabled_registers = {1000}  # Disable register 1000


@pytest.mark.asyncio
async def test_dynamic_batch_read_failure_handling(mock_hass, mock_entry):
    """Test dynamic batch read failure handling."""
    mock_client = AsyncMock()
    
    # Mock failed batch read
    mock_failed_result = Mock()
    mock_failed_result.isError.return_value = True
    
    # Mock successful individual read
    mock_success_result = Mock()
    mock_success_result.isError.return_value = False
    mock_success_result.registers = [100]
    
    # First call fails, subsequent calls succeed
    mock_client.read_holding_registers = AsyncMock(side_effect=[
        mock_failed_result,  # First batch read fails
        mock_success_result,  # Individual read succeeds
        mock_success_result,  # Individual read succeeds
        mock_success_result,  # Individual read succeeds
        mock_success_result,  # Individual read succeeds
    ])

    coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
    coordinator.client = mock_client
    
    # Test that batch failures are tracked
    assert len(coordinator._batch_failures) == 0
    assert len(coordinator._individual_read_addresses) == 0
    
    # Simulate batch read failure
    batch_key = (1050, 11)  # Register 1050-1060
    coordinator._batch_failures[batch_key] = 1
    
    # After max failures, should switch to individual reads
    coordinator._batch_failures[batch_key] = coordinator._max_batch_failures + 1
    coordinator._individual_read_addresses.add(batch_key)
    
    assert batch_key in coordinator._individual_read_addresses


@pytest.mark.asyncio
async def test_dynamic_cycling_warnings(mock_hass, mock_entry):
    """Test dynamic cycling warnings suppression."""
    coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
    
    entity_id = "sensor.test_heating_cycling_total"
    
    # Test warning counter
    assert len(coordinator._cycling_warnings) == 0
    
    # Simulate multiple warnings
    coordinator._cycling_warnings[entity_id] = 1
    assert coordinator._cycling_warnings[entity_id] == 1
    
    # Test max warnings threshold
    coordinator._cycling_warnings[entity_id] = coordinator._max_cycling_warnings
    assert coordinator._cycling_warnings[entity_id] == coordinator._max_cycling_warnings
    
    # Test reset mechanism
    del coordinator._cycling_warnings[entity_id]
    assert entity_id not in coordinator._cycling_warnings


@pytest.mark.asyncio
async def test_async_update_data_read_error(mock_hass, mock_entry):
    """Test data update with read error (Coordinator liefert weiterhin Data-Dict)."""
    mock_client = AsyncMock()
    mock_result = Mock()
    mock_result.isError.return_value = True
    mock_client.read_holding_registers = AsyncMock(return_value=mock_result)

    coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
    coordinator.client = mock_client
    coordinator.disabled_registers = set()

    result = await coordinator._async_update_data()

    # Coordinator gibt bei Read-Fehler ein Data-Dict zurück (kein None)
    assert result is not None
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_async_update_data_int32_sensor(mock_hass, mock_entry):
    """Test data update with int32 sensor."""
    mock_client = AsyncMock()
    mock_result = Mock()
    mock_result.isError.return_value = False
    mock_result.registers = [100, 200]  # Two registers for int32
    mock_client.read_holding_registers = AsyncMock(return_value=mock_result)

    coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
    coordinator.client = mock_client
    coordinator.disabled_registers = set()

    result = await coordinator._async_update_data()

    assert result is not None
    mock_client.read_holding_registers.assert_called()


@pytest.mark.asyncio
async def test_async_update_data_int16_sensor(mock_hass, mock_entry):
    """Test data update with int16 sensor."""
    mock_client = AsyncMock()
    mock_result = Mock()
    mock_result.isError.return_value = False
    mock_result.registers = [100]  # One register for int16
    mock_client.read_holding_registers = AsyncMock(return_value=mock_result)

    coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
    coordinator.client = mock_client
    coordinator.disabled_registers = set()

    result = await coordinator._async_update_data()

    assert result is not None
    mock_client.read_holding_registers.assert_called()


@pytest.mark.asyncio
async def test_connect_success(mock_hass, mock_entry):
    """Test successful connection."""
    mock_client = AsyncMock()
    mock_client.connect = AsyncMock(return_value=True)

    with patch("pymodbus.client.AsyncModbusTcpClient", return_value=mock_client):
        coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
        await coordinator._connect()

        assert coordinator.client == mock_client
        mock_client.connect.assert_called_once()


@pytest.mark.asyncio
async def test_connect_failure(mock_hass, mock_entry):
    """Test connection failure."""
    from homeassistant.helpers.update_coordinator import UpdateFailed
    
    mock_client = AsyncMock()
    mock_client.connect = AsyncMock(return_value=False)

    with patch("pymodbus.client.AsyncModbusTcpClient", return_value=mock_client):
        coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
        
        with pytest.raises(UpdateFailed):
            await coordinator._connect()
        
        assert coordinator.client is None


@pytest.mark.asyncio
async def test_load_sensor_overrides_success(mock_hass, mock_entry):
    """Test successful sensor overrides loading."""
    config_data = {
        "sensors_names_override": [{"id": "test_sensor", "override_name": "new_name"}]
    }

    async def run_sync(fn):
        """Führt synchrone Funktion aus (Ersatz für async_add_executor_job)."""
        return fn()

    mock_hass.async_add_executor_job = run_sync

    with patch(
        "custom_components.lambda_heat_pumps.coordinator.os.path.exists",
        return_value=True,
    ):
        with patch("builtins.open", mock_open(read_data=yaml.dump(config_data))):
            coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
            result = await coordinator._load_sensor_overrides()

            assert result == {"test_sensor": "new_name"}


@pytest.mark.asyncio
async def test_load_sensor_overrides_file_not_exists(mock_hass, mock_entry):
    """Test sensor overrides loading when file doesn't exist."""
    with patch(
        "custom_components.lambda_heat_pumps.coordinator.os.path.exists",
        return_value=False,
    ):
        coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
        result = await coordinator._load_sensor_overrides()

        assert result == {}


@pytest.mark.asyncio
async def test_load_sensor_overrides_yaml_error(mock_hass, mock_entry):
    """Test sensor overrides loading with YAML error."""
    @asynccontextmanager
    async def fake_open_error(*args, **kwargs):
        yield StringIO("invalid yaml")

    with patch(
        "custom_components.lambda_heat_pumps.coordinator.os.path.exists",
        return_value=True,
    ):
        with patch("aiofiles.open", fake_open_error):
            coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
            result = await coordinator._load_sensor_overrides()

            assert result == {}


def test_on_ha_started(mock_hass, mock_entry):
    """Test on_ha_started method."""
    coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
    mock_event = Mock()

    # _on_ha_started is not async, it just sets a flag
    coordinator._on_ha_started(mock_event)

    assert coordinator._ha_started is True


def test_coordinator_update_interval_from_options(mock_hass, mock_entry):
    """Test coordinator uses update interval from options."""
    mock_entry.options = {"update_interval": 60}

    coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)

    assert coordinator.update_interval == timedelta(seconds=60)


def test_coordinator_config_paths(mock_hass, mock_entry):
    """Test coordinator config paths."""
    coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)

    assert coordinator._config_dir == "/tmp/test_config"
    assert coordinator._config_path == os.path.join("/tmp/test_config", "lambda_heat_pumps")


@pytest.mark.asyncio
async def test_coordinator_last_state_initialization(mock_hass, mock_entry):
    """Test that _last_state is initialized for HP_STATE flank detection."""
    coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
    
    # Test that _last_state is initialized as empty dict
    assert hasattr(coordinator, "_last_state")
    assert isinstance(coordinator._last_state, dict)
    assert coordinator._last_state == {}
    
    # Test that _last_state can store HP state values
    coordinator._last_state["1"] = "3"  # HP1 state = READY
    coordinator._last_state["2"] = "5"  # HP2 state = START COMPRESSOR
    
    assert coordinator._last_state["1"] == "3"
    assert coordinator._last_state["2"] == "5"


@pytest.mark.asyncio
async def test_coordinator_last_state_persistence(mock_hass, mock_entry):
    """Test that _last_state is persisted and restored correctly."""
    coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
    
    # Set some state values
    coordinator._last_state["1"] = "5"  # HP1 state = START COMPRESSOR
    coordinator._last_state["2"] = "3"  # HP2 state = READY
    
    # Mock persist data structure
    persist_data = {
        "last_operating_states": {"1": "1", "2": "2"},
        "last_states": {"1": "5", "2": "3"},
    }
    
    # Simulate loading persisted data
    coordinator._last_operating_state = persist_data.get("last_operating_states", {})
    coordinator._last_state = persist_data.get("last_states", {})
    
    # Verify restored values
    assert coordinator._last_state["1"] == "5"
    assert coordinator._last_state["2"] == "3"
    assert coordinator._last_operating_state["1"] == "1"
    assert coordinator._last_operating_state["2"] == "2"


def test_collect_energy_sensor_states_corrects_invalid_daily_monthly_yearly(mock_hass, mock_entry):
    """_collect_energy_sensor_states speichert nie yesterday/previous_* > energy_value (Konsistenz)."""
    from custom_components.lambda_heat_pumps.const import DOMAIN

    # Echte Dict-Struktur, damit coordinator._collect_energy_sensor_states() sie findet
    entities = {}
    mock_hass.data = {DOMAIN: {mock_entry.entry_id: {"energy_entities": entities}}}

    # Daily: yesterday_value > energy_value (inkonsistent)
    daily_ent = MagicMock()
    daily_ent._energy_value = 1668.47
    daily_ent._yesterday_value = 1969.46
    daily_ent._previous_monthly_value = 0.0
    daily_ent._previous_yearly_value = 0.0
    daily_ent.native_value = 0.0
    entities["sensor.eu08l_hp1_heating_energy_daily"] = daily_ent

    # Monthly: previous_monthly_value > energy_value
    monthly_ent = MagicMock()
    monthly_ent._energy_value = 1668.47
    monthly_ent._yesterday_value = 0.0
    monthly_ent._previous_monthly_value = 1800.0
    monthly_ent._previous_yearly_value = 1500.0
    monthly_ent.native_value = 0.0
    entities["sensor.eu08l_hp1_heating_energy_monthly"] = monthly_ent

    # Yearly: previous_yearly_value > energy_value
    yearly_ent = MagicMock()
    yearly_ent._energy_value = 1668.47
    yearly_ent._yesterday_value = 0.0
    yearly_ent._previous_monthly_value = 1600.0
    yearly_ent._previous_yearly_value = 2000.0
    yearly_ent.native_value = 0.0
    entities["sensor.eu08l_hp1_heating_energy_yearly"] = yearly_ent

    coordinator = LambdaDataUpdateCoordinator(mock_hass, mock_entry)
    out = coordinator._collect_energy_sensor_states()

    assert out["sensor.eu08l_hp1_heating_energy_daily"]["attributes"]["yesterday_value"] == 1668.47
    assert out["sensor.eu08l_hp1_heating_energy_monthly"]["attributes"]["previous_monthly_value"] == 1668.47
    assert out["sensor.eu08l_hp1_heating_energy_yearly"]["attributes"]["previous_yearly_value"] == 1668.47
