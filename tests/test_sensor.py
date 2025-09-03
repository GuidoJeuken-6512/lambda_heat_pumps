"""Test the sensor module."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant

from custom_components.lambda_heat_pumps.const import (
    BOIL_SENSOR_TEMPLATES,
    BUFF_SENSOR_TEMPLATES,
    DOMAIN,
    HC_SENSOR_TEMPLATES,
    HP_SENSOR_TEMPLATES,
    SENSOR_TYPES,
    SOL_SENSOR_TEMPLATES,
)
from custom_components.lambda_heat_pumps.sensor import (
    LambdaSensor,
    LambdaTemplateSensor,
    async_setup_entry,
)


@pytest.fixture
def mock_hass():
    """Create a mock hass object."""
    hass = Mock()
    hass.config = Mock()
    hass.config.config_dir = "/tmp/test_config"
    hass.config_entries = Mock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.data = {}
    hass.states = Mock()
    hass.states.async_all = AsyncMock(return_value=[])
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
    return coordinator


@pytest.mark.asyncio
async def test_async_setup_entry_no_coordinator(mock_hass, mock_entry):
    """Test async setup entry when no coordinator exists."""
    mock_add_entities = AsyncMock()

    # Don't set up coordinator in hass.data
    mock_hass.data[DOMAIN] = {}

    # This should raise a KeyError, which is expected behavior
    with pytest.raises(KeyError):
        await async_setup_entry(mock_hass, mock_entry, mock_add_entities)


@pytest.mark.asyncio
async def test_async_setup_entry_with_coordinator(
    mock_hass, mock_entry, mock_coordinator
):
    """Test async setup entry with coordinator."""
    mock_add_entities = AsyncMock()
    mock_hass.data[DOMAIN] = {mock_entry.entry_id: {"coordinator": mock_coordinator}}

    with patch(
        "custom_components.lambda_heat_pumps.sensor.LambdaSensor"
    ) as mock_sensor_class:
        mock_sensor = Mock()
        mock_sensor_class.return_value = mock_sensor

        result = await async_setup_entry(mock_hass, mock_entry, mock_add_entities)

        # Should call add_entities
        mock_add_entities.assert_called()


@pytest.mark.asyncio
async def test_async_setup_entry_with_disabled_registers(
    mock_hass, mock_entry, mock_coordinator
):
    """Test async setup entry with disabled registers."""
    mock_add_entities = AsyncMock()
    mock_hass.data[DOMAIN] = {mock_entry.entry_id: {"coordinator": mock_coordinator}}
    mock_coordinator.is_register_disabled.return_value = True

    with patch(
        "custom_components.lambda_heat_pumps.sensor.LambdaSensor"
    ) as mock_sensor_class:
        mock_sensor = Mock()
        mock_sensor_class.return_value = mock_sensor

        result = await async_setup_entry(mock_hass, mock_entry, mock_add_entities)

        # Should call add_entities but skip disabled registers
        mock_add_entities.assert_called()


@pytest.mark.asyncio
async def test_async_setup_entry_with_legacy_names(
    mock_hass, mock_entry, mock_coordinator
):
    """Test async setup entry with legacy names."""
    mock_add_entities = AsyncMock()
    mock_hass.data[DOMAIN] = {mock_entry.entry_id: {"coordinator": mock_coordinator}}
    mock_entry.data["use_legacy_modbus_names"] = True

    with patch(
        "custom_components.lambda_heat_pumps.sensor.LambdaSensor"
    ) as mock_sensor_class:
        mock_sensor = Mock()
        mock_sensor_class.return_value = mock_sensor

        result = await async_setup_entry(mock_hass, mock_entry, mock_add_entities)

        # Should call add_entities
        mock_add_entities.assert_called()


def test_lambda_sensor_init(mock_entry, mock_coordinator):
    """Test LambdaSensor initialization."""
    sensor = LambdaSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_temperature",
        name="Test Sensor",
        unit="°C",
        address=1000,
        scale=1.0,
        state_class="measurement",
        device_class="temperature",
        relative_address=0,
        data_type="int16",
        device_type="HP",
        txt_mapping=False,
        precision=1,
        entity_id="sensor.hp1_temperature",
        unique_id="hp1_temperature",
    )

    assert sensor.coordinator == mock_coordinator
    assert sensor._entry == mock_entry
    assert sensor._sensor_id == "hp1_temperature"
    assert sensor._attr_name == "Test Sensor"
    assert sensor._unit == "°C"
    assert sensor._address == 1000
    assert sensor._scale == 1.0
    assert sensor._state_class == "measurement"
    assert sensor._device_class == "temperature"
    assert sensor._relative_address == 0
    assert sensor._data_type == "int16"
    assert sensor._device_type == "HP"
    assert sensor._txt_mapping is False
    assert sensor._precision == 1
    assert sensor.entity_id == "sensor.hp1_temperature"
    assert sensor._attr_unique_id == "hp1_temperature"


def test_lambda_sensor_name_property(mock_entry, mock_coordinator):
    """Test LambdaSensor name property."""
    sensor = LambdaSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_temperature",
        name="Test Sensor",
        unit="°C",
        address=1000,
        scale=1.0,
        state_class="measurement",
        device_class="temperature",
        relative_address=0,
        data_type="int16",
        device_type="HP",
        txt_mapping=False,
        precision=1,
        entity_id="sensor.hp1_temperature",
        unique_id="hp1_temperature",
    )

    # Test with sensor_overrides
    mock_coordinator.sensor_overrides = {"hp1_temperature": "Custom Name"}
    mock_entry.data = {"use_legacy_modbus_names": True}
    assert sensor.name == "Custom Name"

    # Test without sensor_overrides
    mock_coordinator.sensor_overrides = {}
    assert sensor.name == "Test Sensor"


def test_lambda_sensor_native_value_none(mock_entry, mock_coordinator):
    """Test LambdaSensor native_value when data is None."""
    sensor = LambdaSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_temperature",
        name="Test Sensor",
        unit="°C",
        address=1000,
        scale=1.0,
        state_class="measurement",
        device_class="temperature",
        relative_address=0,
        data_type="int16",
        device_type="HP",
        txt_mapping=False,
        precision=1,
        entity_id="sensor.hp1_temperature",
        unique_id="hp1_temperature",
    )
    mock_coordinator.data = {}

    assert sensor.native_value is None


def test_lambda_sensor_native_value_with_data(mock_entry, mock_coordinator):
    """Test LambdaSensor native_value with data."""
    sensor = LambdaSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_temperature",
        name="Test Sensor",
        unit="°C",
        address=1000,
        scale=1.0,
        state_class="measurement",
        device_class="temperature",
        relative_address=0,
        data_type="int16",
        device_type="HP",
        txt_mapping=False,
        precision=1,
        entity_id="sensor.hp1_temperature",
        unique_id="hp1_temperature",
    )
    mock_coordinator.data = {"hp1_temperature": 20.5}

    assert sensor.native_value == 20.5


def test_lambda_sensor_native_value_with_txt_mapping(mock_entry, mock_coordinator):
    """Test LambdaSensor native_value with text mapping."""
    sensor = LambdaSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_state",
        name="HP1 Operating State",
        unit="",
        address=1000,
        scale=1.0,
        state_class="",
        device_class=None,
        relative_address=0,
        data_type="int16",
        device_type="HP",
        txt_mapping=True,
        precision=None,
        entity_id="sensor.hp1_state",
        unique_id="hp1_state",
    )
    mock_coordinator.data = {"hp1_state": 1}

    # Mock the text mapping
    with patch(
        "custom_components.lambda_heat_pumps.sensor.HP_OPERATING_STATE", {1: "Running"}
    ):
        assert sensor.native_value == "Running"


def test_lambda_sensor_native_value_with_precision(mock_entry, mock_coordinator):
    """Test LambdaSensor native_value with precision."""
    sensor = LambdaSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_temperature",
        name="Test Sensor",
        unit="°C",
        address=1000,
        scale=0.01,
        state_class="measurement",
        device_class="temperature",
        relative_address=0,
        data_type="int16",
        device_type="HP",
        txt_mapping=False,
        precision=2,
        entity_id="sensor.hp1_temperature",
        unique_id="hp1_temperature",
    )
    mock_coordinator.data = {"hp1_temperature": 20.57}

    assert sensor.native_value == 20.57


def test_lambda_sensor_device_info(mock_entry, mock_coordinator):
    """Test LambdaSensor device_info."""
    sensor = LambdaSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_temperature",
        name="Test Sensor",
        unit="°C",
        address=1000,
        scale=1.0,
        state_class="measurement",
        device_class="temperature",
        relative_address=0,
        data_type="int16",
        device_type="HP",
        txt_mapping=False,
        precision=1,
        entity_id="sensor.hp1_temperature",
        unique_id="hp1_temperature",
    )

    device_info = sensor.device_info
    assert device_info is not None
    assert "identifiers" in device_info
    assert "name" in device_info


def test_lambda_sensor_unique_id(mock_entry, mock_coordinator):
    """Test LambdaSensor unique_id."""
    sensor = LambdaSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_temperature",
        name="Test Sensor",
        unit="°C",
        address=1000,
        scale=1.0,
        state_class="measurement",
        device_class="temperature",
        relative_address=0,
        data_type="int16",
        device_type="HP",
        txt_mapping=False,
        precision=1,
        entity_id="sensor.hp1_temperature",
        unique_id="hp1_temperature",
    )

    assert sensor.unique_id == "hp1_temperature"


def test_lambda_sensor_entity_id(mock_entry, mock_coordinator):
    """Test LambdaSensor entity_id."""
    sensor = LambdaSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_temperature",
        name="Test Sensor",
        unit="°C",
        address=1000,
        scale=1.0,
        state_class="measurement",
        device_class="temperature",
        relative_address=0,
        data_type="int16",
        device_type="HP",
        txt_mapping=False,
        precision=1,
        entity_id="sensor.hp1_temperature",
        unique_id="hp1_temperature",
    )

    assert sensor.entity_id == "sensor.hp1_temperature"


def test_lambda_sensor_native_unit_of_measurement(mock_entry, mock_coordinator):
    """Test LambdaSensor native_unit_of_measurement."""
    sensor = LambdaSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_temperature",
        name="Test Sensor",
        unit="°C",
        address=1000,
        scale=1.0,
        state_class="measurement",
        device_class="temperature",
        relative_address=0,
        data_type="int16",
        device_type="HP",
        txt_mapping=False,
        precision=1,
        entity_id="sensor.hp1_temperature",
        unique_id="hp1_temperature",
    )

    assert sensor.native_unit_of_measurement == "°C"


def test_lambda_sensor_state_class(mock_entry, mock_coordinator):
    """Test LambdaSensor state_class."""
    sensor = LambdaSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_temperature",
        name="Test Sensor",
        unit="°C",
        address=1000,
        scale=1.0,
        state_class="measurement",
        device_class="temperature",
        relative_address=0,
        data_type="int16",
        device_type="HP",
        txt_mapping=False,
        precision=1,
        entity_id="sensor.hp1_temperature",
        unique_id="hp1_temperature",
    )

    assert sensor.state_class == "measurement"


def test_lambda_sensor_device_class(mock_entry, mock_coordinator):
    """Test LambdaSensor device_class."""
    sensor = LambdaSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_temperature",
        name="Test Sensor",
        unit="°C",
        address=1000,
        scale=1.0,
        state_class="measurement",
        device_class="temperature",
        relative_address=0,
        data_type="int16",
        device_type="HP",
        txt_mapping=False,
        precision=1,
        entity_id="sensor.hp1_temperature",
        unique_id="hp1_temperature",
    )

    assert sensor.device_class == "temperature"


def test_lambda_sensor_should_poll(mock_entry, mock_coordinator):
    """Test LambdaSensor should_poll."""
    sensor = LambdaSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_temperature",
        name="Test Sensor",
        unit="°C",
        address=1000,
        scale=1.0,
        state_class="measurement",
        device_class="temperature",
        relative_address=0,
        data_type="int16",
        device_type="HP",
        txt_mapping=False,
        precision=1,
        entity_id="sensor.hp1_temperature",
        unique_id="hp1_temperature",
    )

    assert sensor.should_poll is False


def test_lambda_sensor_has_entity_name(mock_entry, mock_coordinator):
    """Test LambdaSensor has_entity_name."""
    sensor = LambdaSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_temperature",
        name="Test Sensor",
        unit="°C",
        address=1000,
        scale=1.0,
        state_class="measurement",
        device_class="temperature",
        relative_address=0,
        data_type="int16",
        device_type="HP",
        txt_mapping=False,
        precision=1,
        entity_id="sensor.hp1_temperature",
        unique_id="hp1_temperature",
    )

    assert sensor.has_entity_name is True


# Template Sensor Tests
def test_lambda_template_sensor_init(mock_entry, mock_coordinator):
    """Test LambdaTemplateSensor initialization."""
    sensor = LambdaTemplateSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_cop_calc",
        name="HP1 COP Calculated",
        unit=None,
        state_class="measurement",
        device_class=None,
        device_type="HP",
        precision=2,
        entity_id="sensor.hp1_cop_calc",
        unique_id="hp1_cop_calc",
        template_str="{{ states('sensor.hp1_cop') | float(0) }}",
    )

    assert sensor.coordinator == mock_coordinator
    assert sensor._entry == mock_entry
    assert sensor._sensor_id == "hp1_cop_calc"
    assert sensor._name == "HP1 COP Calculated"
    assert sensor._unit is None
    assert sensor._state_class == "measurement"
    assert sensor._device_class is None
    assert sensor._device_type == "HP"
    assert sensor._precision == 2
    assert sensor._entity_id == "sensor.hp1_cop_calc"
    assert sensor._unique_id == "hp1_cop_calc"
    assert sensor._template_str == "{{ states('sensor.hp1_cop') | float(0) }}"
    assert sensor._state is None


def test_lambda_template_sensor_name_property(mock_entry, mock_coordinator):
    """Test LambdaTemplateSensor name property."""
    sensor = LambdaTemplateSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_cop_calc",
        name="HP1 COP Calculated",
        unit=None,
        state_class="measurement",
        device_class=None,
        device_type="HP",
        precision=2,
        entity_id="sensor.hp1_cop_calc",
        unique_id="hp1_cop_calc",
        template_str="{{ states('sensor.hp1_cop') | float(0) }}",
    )

    assert sensor.name == "HP1 COP Calculated"


def test_lambda_template_sensor_unique_id_property(mock_entry, mock_coordinator):
    """Test LambdaTemplateSensor unique_id property."""
    sensor = LambdaTemplateSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_cop_calc",
        name="HP1 COP Calculated",
        unit=None,
        state_class="measurement",
        device_class=None,
        device_type="HP",
        precision=2,
        entity_id="sensor.hp1_cop_calc",
        unique_id="hp1_cop_calc",
        template_str="{{ states('sensor.hp1_cop') | float(0) }}",
    )

    assert sensor.unique_id == "hp1_cop_calc"


def test_lambda_template_sensor_native_value_property(mock_entry, mock_coordinator):
    """Test LambdaTemplateSensor native_value property."""
    sensor = LambdaTemplateSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_cop_calc",
        name="HP1 COP Calculated",
        unit=None,
        state_class="measurement",
        device_class=None,
        device_type="HP",
        precision=2,
        entity_id="sensor.hp1_cop_calc",
        unique_id="hp1_cop_calc",
        template_str="{{ states('sensor.hp1_cop') | float(0) }}",
    )

    # Initially should be None
    assert sensor.native_value is None

    # Set a value
    sensor._state = 3.5
    assert sensor.native_value == 3.5


def test_lambda_template_sensor_native_unit_of_measurement_property(
    mock_entry, mock_coordinator
):
    """Test LambdaTemplateSensor native_unit_of_measurement property."""
    sensor = LambdaTemplateSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_cop_calc",
        name="HP1 COP Calculated",
        unit="°C",
        state_class="measurement",
        device_class=None,
        device_type="HP",
        precision=2,
        entity_id="sensor.hp1_cop_calc",
        unique_id="hp1_cop_calc",
        template_str="{{ states('sensor.hp1_cop') | float(0) }}",
    )

    assert sensor.native_unit_of_measurement == "°C"


def test_lambda_template_sensor_state_class_property(mock_entry, mock_coordinator):
    """Test LambdaTemplateSensor state_class property."""
    # Test measurement state class
    sensor = LambdaTemplateSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_cop_calc",
        name="HP1 COP Calculated",
        unit=None,
        state_class="measurement",
        device_class=None,
        device_type="HP",
        precision=2,
        entity_id="sensor.hp1_cop_calc",
        unique_id="hp1_cop_calc",
        template_str="{{ states('sensor.hp1_cop') | float(0) }}",
    )

    from homeassistant.components.sensor import SensorStateClass

    assert sensor.state_class == SensorStateClass.MEASUREMENT

    # Test total state class
    sensor._state_class = "total"
    assert sensor.state_class == SensorStateClass.TOTAL

    # Test total_increasing state class
    sensor._state_class = "total_increasing"
    assert sensor.state_class == SensorStateClass.TOTAL_INCREASING

    # Test unknown state class
    sensor._state_class = "unknown"
    assert sensor.state_class is None


def test_lambda_template_sensor_device_class_property(mock_entry, mock_coordinator):
    """Test LambdaTemplateSensor device_class property."""
    from homeassistant.components.sensor import SensorDeviceClass

    # Test temperature device class
    sensor = LambdaTemplateSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_temp_diff",
        name="HP1 Temperature Difference",
        unit="°C",
        state_class="measurement",
        device_class="temperature",
        device_type="HP",
        precision=1,
        entity_id="sensor.hp1_temp_diff",
        unique_id="hp1_temp_diff",
        template_str="{{ states('sensor.hp1_flow_temp') | float(0) - states('sensor.hp1_return_temp') | float(0) }}",
    )

    assert sensor.device_class == SensorDeviceClass.TEMPERATURE

    # Test power device class
    sensor._device_class = "power"
    assert sensor.device_class == SensorDeviceClass.POWER

    # Test energy device class
    sensor._device_class = "energy"
    assert sensor.device_class == SensorDeviceClass.ENERGY

    # Test None device class
    sensor._device_class = None
    assert sensor.device_class is None


def test_lambda_template_sensor_should_poll(mock_entry, mock_coordinator):
    """Test LambdaTemplateSensor should_poll property."""
    sensor = LambdaTemplateSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_cop_calc",
        name="HP1 COP Calculated",
        unit=None,
        state_class="measurement",
        device_class=None,
        device_type="HP",
        precision=2,
        entity_id="sensor.hp1_cop_calc",
        unique_id="hp1_cop_calc",
        template_str="{{ states('sensor.hp1_cop') | float(0) }}",
    )

    assert sensor._attr_should_poll is False


def test_lambda_template_sensor_has_entity_name(mock_entry, mock_coordinator):
    """Test LambdaTemplateSensor has_entity_name property."""
    sensor = LambdaTemplateSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_cop_calc",
        name="HP1 COP Calculated",
        unit=None,
        state_class="measurement",
        device_class=None,
        device_type="HP",
        precision=2,
        entity_id="sensor.hp1_cop_calc",
        unique_id="hp1_cop_calc",
        template_str="{{ states('sensor.hp1_cop') | float(0) }}",
    )

    assert sensor._attr_has_entity_name is True


@patch("custom_components.lambda_heat_pumps.sensor.build_device_info")
def test_lambda_template_sensor_device_info(
    mock_build_device_info, mock_entry, mock_coordinator
):
    """Test LambdaTemplateSensor device_info property."""
    mock_device_info = {"test": "device_info"}
    mock_build_device_info.return_value = mock_device_info

    sensor = LambdaTemplateSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_cop_calc",
        name="HP1 COP Calculated",
        unit=None,
        state_class="measurement",
        device_class=None,
        device_type="HP",
        precision=2,
        entity_id="sensor.hp1_cop_calc",
        unique_id="hp1_cop_calc",
        template_str="{{ states('sensor.hp1_cop') | float(0) }}",
    )

    device_info = sensor.device_info
    assert device_info == mock_device_info
    mock_build_device_info.assert_called_once_with(mock_entry, "HP", "hp1_cop_calc")


@pytest.mark.asyncio
async def test_lambda_template_sensor_async_added_to_hass(mock_entry, mock_coordinator):
    """Test LambdaTemplateSensor async_added_to_hass method."""
    sensor = LambdaTemplateSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_cop_calc",
        name="HP1 COP Calculated",
        unit=None,
        state_class="measurement",
        device_class=None,
        device_type="HP",
        precision=2,
        entity_id="sensor.hp1_cop_calc",
        unique_id="hp1_cop_calc",
        template_str="{{ states('sensor.hp1_cop') | float(0) }}",
    )

    # Mock the _handle_coordinator_update method
    sensor._handle_coordinator_update = Mock()

    await sensor.async_added_to_hass()

    # Should call _handle_coordinator_update
    sensor._handle_coordinator_update.assert_called_once()


@patch("homeassistant.helpers.template.Template")
@patch("homeassistant.helpers.template.TemplateError")
def test_lambda_template_sensor_handle_coordinator_update_success(
    mock_template_error, mock_template_class, mock_entry, mock_coordinator
):
    """Test LambdaTemplateSensor _handle_coordinator_update with successful template rendering."""
    # Mock template
    mock_template = Mock()
    mock_template.async_render.return_value = "3.5"
    mock_template_class.return_value = mock_template

    sensor = LambdaTemplateSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_cop_calc",
        name="HP1 COP Calculated",
        unit=None,
        state_class="measurement",
        device_class=None,
        device_type="HP",
        precision=2,
        entity_id="sensor.hp1_cop_calc",
        unique_id="hp1_cop_calc",
        template_str="{{ states('sensor.hp1_cop') | float(0) }}",
    )

    # Mock hass
    sensor.hass = Mock()

    # Mock async_write_ha_state
    sensor.async_write_ha_state = Mock()

    sensor._handle_coordinator_update()

    # Should render template and set state
    mock_template.async_render.assert_called_once()
    assert sensor._state == 3.5
    sensor.async_write_ha_state.assert_called_once()


@patch("homeassistant.helpers.template.Template")
@patch("homeassistant.helpers.template.TemplateError")
def test_lambda_template_sensor_handle_coordinator_update_template_error(
    mock_template_error, mock_template_class, mock_entry, mock_coordinator
):
    """Test LambdaTemplateSensor _handle_coordinator_update with template error."""
    # Mock template to raise TemplateError
    mock_template = Mock()
    mock_template.async_render.side_effect = mock_template_error("Template error")
    mock_template_class.return_value = mock_template

    sensor = LambdaTemplateSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_cop_calc",
        name="HP1 COP Calculated",
        unit=None,
        state_class="measurement",
        device_class=None,
        device_type="HP",
        precision=2,
        entity_id="sensor.hp1_cop_calc",
        unique_id="hp1_cop_calc",
        template_str="{{ states('sensor.hp1_cop') | float(0) }}",
    )

    # Mock hass
    sensor.hass = Mock()

    # Mock async_write_ha_state
    sensor.async_write_ha_state = Mock()

    sensor._handle_coordinator_update()

    # Should set state to None on error
    assert sensor._state is None
    sensor.async_write_ha_state.assert_called_once()


@patch("homeassistant.helpers.template.Template")
def test_lambda_template_sensor_handle_coordinator_update_with_precision(
    mock_template_class, mock_entry, mock_coordinator
):
    """Test LambdaTemplateSensor _handle_coordinator_update with precision."""
    # Mock template
    mock_template = Mock()
    mock_template.async_render.return_value = "3.567"
    mock_template_class.return_value = mock_template

    sensor = LambdaTemplateSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_cop_calc",
        name="HP1 COP Calculated",
        unit=None,
        state_class="measurement",
        device_class=None,
        device_type="HP",
        precision=2,
        entity_id="sensor.hp1_cop_calc",
        unique_id="hp1_cop_calc",
        template_str="{{ states('sensor.hp1_cop') | float(0) }}",
    )

    # Mock hass
    sensor.hass = Mock()

    # Mock async_write_ha_state
    sensor.async_write_ha_state = Mock()

    sensor._handle_coordinator_update()

    # Should apply precision
    assert sensor._state == 3.57
    sensor.async_write_ha_state.assert_called_once()


@patch("homeassistant.helpers.template.Template")
def test_lambda_template_sensor_handle_coordinator_update_unavailable(
    mock_template_class, mock_entry, mock_coordinator
):
    """Test LambdaTemplateSensor _handle_coordinator_update with unavailable state."""
    # Mock template
    mock_template = Mock()
    mock_template.async_render.return_value = "unavailable"
    mock_template_class.return_value = mock_template

    sensor = LambdaTemplateSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="hp1_cop_calc",
        name="HP1 COP Calculated",
        unit=None,
        state_class="measurement",
        device_class=None,
        device_type="HP",
        precision=2,
        entity_id="sensor.hp1_cop_calc",
        unique_id="hp1_cop_calc",
        template_str="{{ states('sensor.hp1_cop') | float(0) }}",
    )

    # Mock hass
    sensor.hass = Mock()

    # Mock async_write_ha_state
    sensor.async_write_ha_state = Mock()

    sensor._handle_coordinator_update()

    # Should keep unavailable state
    assert sensor._state == "unavailable"
    sensor.async_write_ha_state.assert_called_once()
