"""Test the config flow module."""

from unittest.mock import AsyncMock, Mock, patch
from types import SimpleNamespace

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.lambda_heat_pumps.config_flow import (
    CannotConnectError,
    LambdaConfigFlow,
    LambdaOptionsFlow,
    validate_input,
)
from custom_components.lambda_heat_pumps.const import (
    CONF_FIRMWARE_VERSION,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SLAVE_ID,
    DOMAIN,
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
    hass.config_entries.async_entries = AsyncMock(return_value=[])
    hass.data = {}
    hass.data["entity_registry"] = Mock()
    hass.states = Mock()
    hass.states.async_all = AsyncMock(return_value=[])
    hass.bus = Mock()
    hass.bus.async_listen = AsyncMock()
    hass.entity_registry = Mock()
    hass.entity_registry.async_get_entries = AsyncMock(return_value=[])
    # Setze DOMAIN-Eintrag für Tests, die ihn benötigen
    hass.data[DOMAIN] = {}
    hass.loop = DummyLoop()
    return hass


@pytest.fixture
def mock_entry():
    """Create a mock config entry."""
    entry = Mock()
    entry.entry_id = "test_entry"
    entry.data = {
        CONF_NAME: "Test Lambda WP",
        CONF_HOST: "192.168.1.100",
        CONF_PORT: 502,
        CONF_SLAVE_ID: 1,
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
        "use_legacy_naming": False,
    }
    entry.options = {
        "update_interval": 30,
        "write_interval": 30,
        "heating_circuit_min_temp": 15,
        "heating_circuit_max_temp": 35,
        "heating_circuit_temp_step": 0.5,
        "room_thermostat_control": False,
        "pv_surplus": False,
        "room_temperature_entity_1": "sensor.room_temp",
        "pv_power_sensor_entity": "sensor.pv_power",
        "use_legacy_naming": False,
    }
    return entry


class TestLambdaConfigFlow:
    """Test the LambdaConfigFlow class."""

    def test_init(self):
        """Test config flow initialization."""
        flow = LambdaConfigFlow()

        # VERSION comes from MIGRATION_VERSION (currently 8)
        from custom_components.lambda_heat_pumps.const_migration import MIGRATION_VERSION
        assert flow.VERSION == MIGRATION_VERSION
        assert flow._data == {}

    @pytest.mark.asyncio
    async def test_async_step_user_form(self):
        """Test user step shows form."""
        flow = LambdaConfigFlow()
        flow.hass = Mock()
        flow.hass.config_entries = Mock()
        flow.hass.config_entries.async_entries = AsyncMock(return_value=[])

        with patch.object(flow, "_async_current_entries", return_value=[]):
            result = await flow.async_step_user()

            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "user"

    @pytest.mark.asyncio
    async def test_async_step_user_success(self, mock_hass):
        """Test successful user step."""
        flow = LambdaConfigFlow()
        flow.hass = mock_hass

        user_input = {
            CONF_NAME: "Test Lambda WP",
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 502,
            CONF_SLAVE_ID: 1,
            "firmware_version": "V0.0.3-3K",
            "num_hps": 1,
            "num_boil": 1,
            "num_hc": 1,
            "num_buffer": 0,
            "num_solar": 0,
        }

        with patch.object(flow, "_async_current_entries", return_value=[]):
            with patch(
                "custom_components.lambda_heat_pumps.config_flow.validate_input",
                return_value=True,
            ):
                result = await flow.async_step_user(user_input)

                assert result["type"] == FlowResultType.CREATE_ENTRY
                # firmware_version wird aus data entfernt und in options gespeichert
                expected_data = {k: v for k, v in user_input.items() if k != "firmware_version"}
                assert result["data"] == expected_data

    @pytest.mark.asyncio
    async def test_async_step_user_validation_error(self, mock_hass):
        """Test user step with validation error."""
        flow = LambdaConfigFlow()
        flow.hass = mock_hass

        user_input = {
            CONF_NAME: "Test Lambda WP",
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 502,
            CONF_SLAVE_ID: 1,
            "firmware_version": "V0.0.3-3K",
            "num_hps": 1,
            "num_boil": 1,
            "num_hc": 1,
        }

        with patch.object(flow, "_async_current_entries", return_value=[]):
            with patch(
                "custom_components.lambda_heat_pumps.config_flow.validate_input",
                side_effect=CannotConnectError("Connection failed"),
            ):
                result = await flow.async_step_user(user_input)

                assert result["type"] == FlowResultType.FORM
                assert "errors" in result
                assert "base" in result["errors"]

    @pytest.mark.asyncio
    async def test_async_step_user_with_existing_entry(self, mock_hass):
        """Test user step with existing entry."""
        flow = LambdaConfigFlow()
        flow.hass = mock_hass

        # Simuliere existierende Einträge
        mock_entry = Mock()
        mock_entry.data = {CONF_HOST: "192.168.1.100", CONF_PORT: 502}
        mock_entry.options = {}

        with patch.object(flow, "_async_current_entries", return_value=[mock_entry]):
            result = await flow.async_step_user()

            assert result["type"] == FlowResultType.FORM


class TestLambdaOptionsFlow:
    """Test the LambdaOptionsFlow class."""

    def test_init(self, mock_entry):
        """Test options flow initialization."""
        flow = LambdaOptionsFlow(mock_entry)

        assert flow._config_entry == mock_entry

    @pytest.mark.asyncio
    async def test_async_step_init_form(self, mock_entry):
        """Test init step shows form."""
        flow = LambdaOptionsFlow(mock_entry)

        result = await flow.async_step_init()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "init"

    @pytest.mark.asyncio
    async def test_async_step_init_success(self, mock_hass, mock_entry):
        """Test successful init step."""
        flow = LambdaOptionsFlow(mock_entry)
        flow.hass = mock_hass

        user_input = {
            "update_interval": 60,
            "write_interval": 60,
            "heating_circuit_min_temp": 10,
            "heating_circuit_max_temp": 40,
            "heating_circuit_temp_step": 1.0,
            "room_thermostat_control": True,
            "pv_surplus": True,
            "room_temperature_entity_1": "sensor.room_temp",
            "pv_power_sensor_entity": "sensor.pv_power",
            "use_legacy_naming": True,
        }

        with patch.object(flow, "_get_entities", return_value=[]):
            result = await flow.async_step_init(user_input)

            # Should show form for sensor selection
            assert result["type"] == FlowResultType.FORM

    @pytest.mark.asyncio
    async def test_async_step_init_with_defaults(self, mock_hass, mock_entry):
        """Test init step with default values."""
        flow = LambdaOptionsFlow(mock_entry)
        flow.hass = mock_hass

        user_input = {}

        with patch.object(flow, "_get_entities", return_value=[]):
            result = await flow.async_step_init(user_input)

            assert result["type"] == FlowResultType.CREATE_ENTRY
            # Should use defaults from entry.data
            assert result["data"]["update_interval"] == 30

    @pytest.mark.asyncio
    async def test_async_step_init_validation_error(self, mock_hass, mock_entry):
        """Test init step with validation error."""
        flow = LambdaOptionsFlow(mock_entry)
        flow.hass = mock_hass

        user_input = {
            "update_interval": -1,  # Invalid value
        }

        with patch.object(flow, "_get_entities", return_value=[]):
            result = await flow.async_step_init(user_input)

            assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_async_step_init_empty_input(self, mock_hass, mock_entry):
        """Test init step with empty input."""
        flow = LambdaOptionsFlow(mock_entry)
        flow.hass = mock_hass

        with patch.object(flow, "_get_entities", return_value=[]):
            result = await flow.async_step_init({})

            assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_async_step_init_cancel(self, mock_hass, mock_entry):
        """Test init step cancel."""
        flow = LambdaOptionsFlow(mock_entry)
        flow.hass = mock_hass

        result = await flow.async_step_init(user_input=None)

        assert result["type"] == FlowResultType.FORM

    @pytest.mark.asyncio
    async def test_async_step_thermostat_sensor(self, mock_hass, mock_entry):
        """Test thermostat sensor step."""
        flow = LambdaOptionsFlow(mock_entry)
        flow.hass = mock_hass

        with patch.object(flow, "_get_entities", return_value=[]):
            result = await flow.async_step_thermostat_sensor()

            assert result["type"] == FlowResultType.FORM

    @pytest.mark.asyncio
    async def test_async_step_pv_sensor(self, mock_hass, mock_entry):
        """Test PV sensor step."""
        flow = LambdaOptionsFlow(mock_entry)
        flow.hass = mock_hass

        with patch.object(flow, "_get_entities", return_value=[]):
            result = await flow.async_step_pv_sensor()

            assert result["type"] == FlowResultType.FORM

    @pytest.mark.asyncio
    async def test_get_entities(self, mock_hass, mock_entry):
        """Test get_entities method."""
        flow = LambdaOptionsFlow(mock_entry)
        flow.hass = mock_hass

        # Mock entity registry entries
        mock_entity1 = Mock()
        mock_entity1.entity_id = "sensor.temp1"
        mock_entity1.name = "Temperature 1"
        mock_entity1.config_entry_id = mock_entry.entry_id

        mock_entity2 = Mock()
        mock_entity2.entity_id = "sensor.temp2"
        mock_entity2.name = "Temperature 2"
        mock_entity2.config_entry_id = "other_entry_id"  # Different entry ID

        # Mock the entity registry
        mock_registry = Mock()
        mock_registry.entities = {
            "sensor.temp1": mock_entity1,
            "sensor.temp2": mock_entity2,
        }

        # Mock the states
        mock_state1 = Mock()
        mock_state1.entity_id = "sensor.temp1"
        mock_state1.attributes = {"device_class": "temperature"}
        mock_state1.name = "Temperature 1"
        mock_state1.domain = "sensor"

        mock_state2 = Mock()
        mock_state2.entity_id = "sensor.temp2"
        mock_state2.attributes = {"device_class": "temperature"}
        mock_state2.name = "Temperature 2"
        mock_state2.domain = "sensor"

        # Mock async_all - it's used without await in the code, so make it a regular function that returns a list
        mock_hass.states.async_all = Mock(return_value=[mock_state1, mock_state2])
        mock_hass.states.get = Mock(
            side_effect=lambda eid: (
                mock_state1 if eid == "sensor.temp1" else mock_state2
            )
        )

        with patch(
            "homeassistant.helpers.entity_registry.async_get",
            return_value=mock_registry,
        ):
            entities = await flow._get_entities("temperature")

            # Should only return sensor.temp2 since sensor.temp1 belongs to our entry
            assert len(entities) == 1
            assert "sensor.temp2" in entities


@pytest.mark.asyncio
async def test_validate_input_success(mock_hass):
    """Test successful input validation."""
    user_input = {
        CONF_HOST: "192.168.1.100",
        CONF_PORT: 502,
        CONF_SLAVE_ID: 1,
        CONF_FIRMWARE_VERSION: "V0.0.3-3K",
    }

    # Mock the AsyncModbusTcpClient
    mock_client = AsyncMock()
    mock_client.connect.return_value = True
    mock_client.close.return_value = None
    
    # Mock the read_holding_registers result
    mock_result = Mock()
    mock_result.isError.return_value = False

    with patch("pymodbus.client.AsyncModbusTcpClient", return_value=mock_client):
        with patch("custom_components.lambda_heat_pumps.config_flow.async_read_holding_registers", return_value=mock_result):
            result = await validate_input(mock_hass, user_input)

            assert result is None  # validate_input returns None on success
            mock_client.connect.assert_called_once()
            mock_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_validate_input_connection_failed(mock_hass):
    """Test input validation with connection failure."""
    user_input = {
        CONF_HOST: "192.168.1.100",
        CONF_PORT: 502,
        CONF_SLAVE_ID: 1,
    }

    mock_client = AsyncMock()
    mock_client.connect.return_value = False

    with patch("pymodbus.client.ModbusTcpClient", return_value=mock_client):
        with pytest.raises(CannotConnectError):
            await validate_input(mock_hass, user_input)


@pytest.mark.asyncio
async def test_validate_input_read_error(mock_hass):
    """Test input validation with read error."""
    user_input = {
        CONF_HOST: "192.168.1.100",
        CONF_PORT: 502,
        CONF_SLAVE_ID: 1,
    }

    mock_client = AsyncMock()
    mock_client.connect.return_value = True
    mock_client.read_holding_registers = AsyncMock(
        return_value=Mock(isError=lambda: True)
    )

    with patch("pymodbus.client.ModbusTcpClient", return_value=mock_client):
        with pytest.raises(CannotConnectError):
            await validate_input(mock_hass, user_input)


@pytest.mark.asyncio
async def test_validate_input_exception(mock_hass):
    """Test input validation with exception."""
    user_input = {
        CONF_HOST: "192.168.1.100",
        CONF_PORT: 502,
        CONF_SLAVE_ID: 1,
        CONF_FIRMWARE_VERSION: "V0.0.3-3K",
    }

    with patch("pymodbus.client.ModbusTcpClient", side_effect=Exception("Test error")):
        with pytest.raises(CannotConnectError, match="Failed to connect to device"):
            await validate_input(mock_hass, user_input)


def test_cannot_connect_error():
    """Test CannotConnectError exception."""
    error = CannotConnectError("Connection failed")

    assert str(error) == "Connection failed"
