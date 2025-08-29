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


# Tests für Cycling-Sensoren
def test_lambda_cycling_sensor_init(mock_entry, mock_coordinator):
    """Test LambdaCyclingSensor initialization."""
    from custom_components.lambda_heat_pumps.sensor import LambdaCyclingSensor
    
    sensor = LambdaCyclingSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_total",
        name="Heating Cycling Total",
        entity_id="sensor.test_heating_cycling_total",
        unique_id="test_heating_cycling_total",
        unit="cycles",
        state_class="total_increasing",
        device_class=None,
        device_type="hp",
        hp_index=1,
    )
    
    assert sensor._sensor_id == "heating_cycling_total"
    assert sensor._name == "Heating Cycling Total"
    assert sensor.entity_id == "sensor.test_heating_cycling_total"
    assert sensor._unique_id == "test_heating_cycling_total"
    assert sensor._unit == "cycles"
    assert sensor._hp_index == 1
    assert sensor._cycling_value == 0
    assert sensor._yesterday_value == 0
    assert sensor._last_2h_value == 0
    assert sensor._last_4h_value == 0


def test_lambda_cycling_sensor_set_cycling_value(mock_entry, mock_coordinator):
    """Test LambdaCyclingSensor set_cycling_value method."""
    from custom_components.lambda_heat_pumps.sensor import LambdaCyclingSensor
    
    sensor = LambdaCyclingSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_total",
        name="Heating Cycling Total",
        entity_id="sensor.test_heating_cycling_total",
        unique_id="test_heating_cycling_total",
        unit="cycles",
        state_class="total_increasing",
        device_class=None,
        device_type="hp",
        hp_index=1,
    )
    
    # Mock async_write_ha_state
    sensor.async_write_ha_state = Mock()
    
    # Test setting cycling value
    sensor.set_cycling_value(42)
    assert sensor._cycling_value == 42
    sensor.async_write_ha_state.assert_called_once()


def test_lambda_cycling_sensor_update_yesterday_value(mock_entry, mock_coordinator):
    """Test LambdaCyclingSensor update_yesterday_value method."""
    from custom_components.lambda_heat_pumps.sensor import LambdaCyclingSensor
    
    sensor = LambdaCyclingSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_total",
        name="Heating Cycling Total",
        entity_id="sensor.test_heating_cycling_total",
        unique_id="test_heating_cycling_total",
        unit="cycles",
        state_class="total_increasing",
        device_class=None,
        device_type="hp",
        hp_index=1,
    )
    
    # Set initial cycling value
    sensor._cycling_value = 100
    
    # Test yesterday update
    sensor.update_yesterday_value()
    assert sensor._yesterday_value == 100


def test_lambda_cycling_sensor_update_2h_value(mock_entry, mock_coordinator):
    """Test LambdaCyclingSensor update_2h_value method."""
    from custom_components.lambda_heat_pumps.sensor import LambdaCyclingSensor
    
    sensor = LambdaCyclingSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_total",
        name="Heating Cycling Total",
        entity_id="sensor.test_heating_cycling_total",
        unique_id="test_heating_cycling_total",
        unit="cycles",
        state_class="total_increasing",
        device_class=None,
        device_type="hp",
        hp_index=1,
    )
    
    # Set initial cycling value
    sensor._cycling_value = 50
    
    # Test 2h update
    sensor.update_2h_value()
    assert sensor._last_2h_value == 50


def test_lambda_cycling_sensor_update_4h_value(mock_entry, mock_coordinator):
    """Test LambdaCyclingSensor update_4h_value method."""
    from custom_components.lambda_heat_pumps.sensor import LambdaCyclingSensor
    
    sensor = LambdaCyclingSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_total",
        name="Heating Cycling Total",
        entity_id="sensor.test_heating_cycling_total",
        unique_id="test_heating_cycling_total",
        unit="cycles",
        state_class="total_increasing",
        device_class=None,
        device_type="hp",
        hp_index=1,
    )
    
    # Set initial cycling value
    sensor._cycling_value = 75
    
    # Test 4h update
    sensor.update_4h_value()
    assert sensor._last_4h_value == 75


def test_lambda_cycling_sensor_handle_yesterday_update(mock_entry, mock_coordinator):
    """Test LambdaCyclingSensor _handle_yesterday_update method."""
    from custom_components.lambda_heat_pumps.sensor import LambdaCyclingSensor
    
    sensor = LambdaCyclingSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_total",
        name="Heating Cycling Total",
        entity_id="sensor.test_heating_cycling_total",
        unique_id="test_heating_cycling_total",
        unit="cycles",
        state_class="total_increasing",
        device_class=None,
        device_type="hp",
        hp_index=1,
    )
    
    # Mock update_yesterday_value
    sensor.update_yesterday_value = Mock()
    
    # Test with correct entry_id
    sensor._handle_yesterday_update("test_entry")
    sensor.update_yesterday_value.assert_called_once()
    
    # Test with wrong entry_id
    sensor.update_yesterday_value.reset_mock()
    sensor._handle_yesterday_update("wrong_entry")
    sensor.update_yesterday_value.assert_not_called()


def test_lambda_cycling_sensor_handle_2h_update(mock_entry, mock_coordinator):
    """Test LambdaCyclingSensor _handle_2h_update method."""
    from custom_components.lambda_heat_pumps.sensor import LambdaCyclingSensor
    
    sensor = LambdaCyclingSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_total",
        name="Heating Cycling Total",
        entity_id="sensor.test_heating_cycling_total",
        unique_id="test_heating_cycling_total",
        unit="cycles",
        state_class="total_increasing",
        device_class=None,
        device_type="hp",
        hp_index=1,
    )
    
    # Mock update_2h_value
    sensor.update_2h_value = Mock()
    
    # Test with correct entry_id
    sensor._handle_2h_update("test_entry")
    sensor.update_2h_value.assert_called_once()
    
    # Test with wrong entry_id
    sensor.update_2h_value.reset_mock()
    sensor._handle_2h_update("wrong_entry")
    sensor.update_2h_value.assert_not_called()


def test_lambda_cycling_sensor_handle_4h_update(mock_entry, mock_coordinator):
    """Test LambdaCyclingSensor _handle_4h_update method."""
    from custom_components.lambda_heat_pumps.sensor import LambdaCyclingSensor
    
    sensor = LambdaCyclingSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_total",
        name="Heating Cycling Total",
        entity_id="sensor.test_heating_cycling_total",
        unique_id="test_heating_cycling_total",
        unit="cycles",
        state_class="total_increasing",
        device_class=None,
        device_type="hp",
        hp_index=1,
    )
    
    # Mock update_4h_value
    sensor.update_4h_value = Mock()
    
    # Test with correct entry_id
    sensor._handle_4h_update("test_entry")
    sensor.update_4h_value.assert_called_once()
    
    # Test with wrong entry_id
    sensor.update_4h_value.reset_mock()
    sensor._handle_4h_update("wrong_entry")
    sensor.update_4h_value.assert_not_called()


def test_lambda_2h4h_sensor_init(mock_entry, mock_coordinator):
    """Test Lambda2h4hSensor initialization."""
    from custom_components.lambda_heat_pumps.sensor import Lambda2h4hSensor
    
    sensor = Lambda2h4hSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_last_2h",
        name="Heating Cycling Last 2h",
        entity_id="sensor.test_heating_cycling_last_2h",
        unique_id="test_heating_cycling_last_2h",
        unit="cycles",
        state_class="total",
        device_class=None,
        device_type="hp",
        hp_index=1,
        mode="heating",
    )
    
    assert sensor._sensor_id == "heating_cycling_last_2h"
    assert sensor._name == "Heating Cycling Last 2h"
    assert sensor.entity_id == "sensor.test_heating_cycling_last_2h"
    assert sensor._unique_id == "test_heating_cycling_last_2h"
    assert sensor._unit == "cycles"
    assert sensor._hp_index == 1
    assert sensor._mode == "heating"
    assert sensor._stored_value == 0


def test_lambda_2h4h_sensor_set_stored_value(mock_entry, mock_coordinator):
    """Test Lambda2h4hSensor set_stored_value method."""
    from custom_components.lambda_heat_pumps.sensor import Lambda2h4hSensor
    
    sensor = Lambda2h4hSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_last_2h",
        name="Heating Cycling Last 2h",
        entity_id="sensor.test_heating_cycling_last_2h",
        unique_id="test_heating_cycling_last_2h",
        unit="cycles",
        state_class="total",
        device_class=None,
        device_type="hp",
        hp_index=1,
        mode="heating",
    )
    
    # Mock async_write_ha_state
    sensor.async_write_ha_state = Mock()
    
    # Test setting stored value
    sensor.set_stored_value(25)
    assert sensor._stored_value == 25
    sensor.async_write_ha_state.assert_called_once()


def test_lambda_2h4h_sensor_handle_2h_update(mock_entry, mock_coordinator):
    """Test Lambda2h4hSensor _handle_2h_update method."""
    from custom_components.lambda_heat_pumps.sensor import Lambda2h4hSensor
    
    sensor = Lambda2h4hSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_last_2h",
        name="Heating Cycling Last 2h",
        entity_id="sensor.test_heating_cycling_last_2h",
        unique_id="test_heating_cycling_last_2h",
        unit="cycles",
        state_class="total",
        device_class=None,
        device_type="hp",
        hp_index=1,
        mode="heating",
    )
    
    # Mock set_stored_value
    sensor.set_stored_value = Mock()
    
    # Mock hass.states.get to return a valid state
    mock_state = Mock()
    mock_state.state = "100"
    mock_coordinator.hass.states.get.return_value = mock_state
    
    # Test with correct entry_id and 2h sensor
    sensor._handle_2h_update("test_entry")
    sensor.set_stored_value.assert_called_once_with(100)
    
    # Test with wrong entry_id
    sensor.set_stored_value.reset_mock()
    sensor._handle_2h_update("wrong_entry")
    sensor.set_stored_value.assert_not_called()


def test_lambda_2h4h_sensor_handle_4h_update(mock_entry, mock_coordinator):
    """Test Lambda2h4hSensor _handle_4h_update method."""
    from custom_components.lambda_heat_pumps.sensor import Lambda2h4hSensor
    
    sensor = Lambda2h4hSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_last_4h",
        name="Heating Cycling Last 4h",
        entity_id="sensor.test_heating_cycling_last_4h",
        unique_id="test_heating_cycling_last_4h",
        unit="cycles",
        state_class="total",
        device_class=None,
        device_type="hp",
        hp_index=1,
        mode="heating",
    )
    
    # Mock set_stored_value
    sensor.set_stored_value = Mock()
    
    # Mock hass.states.get to return a valid state
    mock_state = Mock()
    mock_state.state = "200"
    mock_coordinator.hass.states.get.return_value = mock_state
    
    # Test with correct entry_id and 4h sensor
    sensor._handle_4h_update("test_entry")
    sensor.set_stored_value.assert_called_once_with(200)
    
    # Test with wrong entry_id
    sensor.set_stored_value.reset_mock()
    sensor._handle_4h_update("wrong_entry")
    sensor.set_stored_value.assert_not_called()


def test_lambda_2h4h_sensor_extra_state_attributes(mock_entry, mock_coordinator):
    """Test Lambda2h4hSensor extra_state_attributes property."""
    from custom_components.lambda_heat_pumps.sensor import Lambda2h4hSensor
    
    # Test 2h sensor
    sensor_2h = Lambda2h4hSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_last_2h",
        name="Heating Cycling Last 2h",
        entity_id="sensor.test_heating_cycling_last_2h",
        unique_id="test_heating_cycling_last_2h",
        unit="cycles",
        state_class="total",
        device_class=None,
        device_type="hp",
        hp_index=1,
        mode="heating",
    )
    
    attrs_2h = sensor_2h.extra_state_attributes
    assert attrs_2h["hp_index"] == 1
    assert attrs_2h["sensor_type"] == "cycling_last_2h"
    
    # Test 4h sensor
    sensor_4h = Lambda2h4hSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id="heating_cycling_last_4h",
        name="Heating Cycling Last 4h",
        entity_id="sensor.test_heating_cycling_last_4h",
        unique_id="test_heating_cycling_last_4h",
        unit="cycles",
        state_class="total",
        device_class=None,
        device_type="hp",
        hp_index=1,
        mode="heating",
    )
    
    attrs_4h = sensor_4h.extra_state_attributes
    assert attrs_4h["hp_index"] == 1
    assert attrs_4h["sensor_type"] == "cycling_last_4h"


# Tests für Template-Sensoren (2h/4h Berechnungen)
def test_template_sensor_2h_calculation(mock_entry, mock_coordinator):
    """Test Template-Sensor für 2h-Berechnung."""
    from custom_components.lambda_heat_pumps.sensor import LambdaTemplateSensor
    
    # Mock hass.states.get to return values for total and last_2h sensors
    def mock_states_get(entity_id):
        mock_state = Mock()
        if "total" in entity_id:
            mock_state.state = "150"  # Total value
        elif "last_2h" in entity_id:
            mock_state.state = "100"  # Last 2h value
        else:
            mock_state.state = "0"
        return mock_state
    
    mock_coordinator.hass.states.get.side_effect = mock_states_get
    
    # Create template sensor for 2h calculation
    sensor = LambdaTemplateSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="heating_cycling_2h",
        name="Heating Cycling 2h",
        unit="cycles",
        state_class="total",
        device_class=None,
        device_type="hp",
        template_str="{{% set total = states('sensor.test_heating_cycling_total') | float(0) %}}{{% set last_2h = states('sensor.test_heating_cycling_last_2h') | float(0) %}}{{{{ ((total - last_2h) | round(0)) | int }}}}",
        entity_id="sensor.test_heating_cycling_2h",
        unique_id="test_heating_cycling_2h",
    )
    
    # Test the calculation
    sensor.handle_coordinator_update()
    
    # Should calculate 150 - 100 = 50
    assert sensor._state == 50


def test_template_sensor_4h_calculation(mock_entry, mock_coordinator):
    """Test Template-Sensor für 4h-Berechnung."""
    from custom_components.lambda_heat_pumps.sensor import LambdaTemplateSensor
    
    # Mock hass.states.get to return values for total and last_4h sensors
    def mock_states_get(entity_id):
        mock_state = Mock()
        if "total" in entity_id:
            mock_state.state = "200"  # Total value
        elif "last_4h" in entity_id:
            mock_state.state = "120"  # Last 4h value
        else:
            mock_state.state = "0"
        return mock_state
    
    mock_coordinator.hass.states.get.side_effect = mock_states_get
    
    # Create template sensor for 4h calculation
    sensor = LambdaTemplateSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="heating_cycling_4h",
        name="Heating Cycling 4h",
        unit="cycles",
        state_class="total",
        device_class=None,
        device_type="hp",
        template_str="{{% set total = states('sensor.test_heating_cycling_total') | float(0) %}}{{% set last_4h = states('sensor.test_heating_cycling_last_4h') | float(0) %}}{{{{ ((total - last_4h) | round(0)) | int }}}}",
        entity_id="sensor.test_heating_cycling_4h",
        unique_id="test_heating_cycling_4h",
    )
    
    # Test the calculation
    sensor.handle_coordinator_update()
    
    # Should calculate 200 - 120 = 80
    assert sensor._state == 80


def test_template_sensor_2h_calculation_with_zero_values(mock_entry, mock_coordinator):
    """Test Template-Sensor für 2h-Berechnung mit Null-Werten."""
    from custom_components.lambda_heat_pumps.sensor import LambdaTemplateSensor
    
    # Mock hass.states.get to return zero values
    def mock_states_get(entity_id):
        mock_state = Mock()
        mock_state.state = "0"
        return mock_state
    
    mock_coordinator.hass.states.get.side_effect = mock_states_get
    
    # Create template sensor for 2h calculation
    sensor = LambdaTemplateSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="heating_cycling_2h",
        name="Heating Cycling 2h",
        unit="cycles",
        state_class="total",
        device_class=None,
        device_type="hp",
        template_str="{{% set total = states('sensor.test_heating_cycling_total') | float(0) %}}{{% set last_2h = states('sensor.test_heating_cycling_last_2h') | float(0) %}}{{{{ ((total - last_2h) | round(0)) | int }}}}",
        entity_id="sensor.test_heating_cycling_2h",
        unique_id="test_heating_cycling_2h",
    )
    
    # Test the calculation
    sensor.handle_coordinator_update()
    
    # Should calculate 0 - 0 = 0
    assert sensor._state == 0


def test_template_sensor_4h_calculation_with_unavailable_states(mock_entry, mock_coordinator):
    """Test Template-Sensor für 4h-Berechnung mit unavailable States."""
    from custom_components.lambda_heat_pumps.sensor import LambdaTemplateSensor
    
    # Mock hass.states.get to return unavailable states
    def mock_states_get(entity_id):
        mock_state = Mock()
        mock_state.state = "unavailable"
        return mock_state
    
    mock_coordinator.hass.states.get.side_effect = mock_states_get
    
    # Create template sensor for 4h calculation
    sensor = LambdaTemplateSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="heating_cycling_4h",
        name="Heating Cycling 4h",
        unit="cycles",
        state_class="total",
        device_class=None,
        device_type="hp",
        template_str="{{% set total = states('sensor.test_heating_cycling_total') | float(0) %}}{{% set last_4h = states('sensor.test_heating_cycling_last_4h') | float(0) %}}{{{{ ((total - last_4h) | round(0)) | int }}}}",
        entity_id="sensor.test_heating_cycling_4h",
        unique_id="test_heating_cycling_4h",
    )
    
    # Test the calculation
    sensor.handle_coordinator_update()
    
    # Should handle unavailable states gracefully and return 0
    assert sensor._state == 0


def test_template_sensor_2h_calculation_with_float_values(mock_entry, mock_coordinator):
    """Test Template-Sensor für 2h-Berechnung mit Float-Werten."""
    from custom_components.lambda_heat_pumps.sensor import LambdaTemplateSensor
    
    # Mock hass.states.get to return float values
    def mock_states_get(entity_id):
        mock_state = Mock()
        if "total" in entity_id:
            mock_state.state = "150.7"  # Total value with decimal
        elif "last_2h" in entity_id:
            mock_state.state = "100.3"  # Last 2h value with decimal
        else:
            mock_state.state = "0"
        return mock_state
    
    mock_coordinator.hass.states.get.side_effect = mock_states_get
    
    # Create template sensor for 2h calculation
    sensor = LambdaTemplateSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="heating_cycling_2h",
        name="Heating Cycling 2h",
        unit="cycles",
        state_class="total",
        device_class=None,
        device_type="hp",
        template_str="{{% set total = states('sensor.test_heating_cycling_total') | float(0) %}}{{% set last_2h = states('sensor.test_heating_cycling_last_2h') | float(0) %}}{{{{ ((total - last_2h) | round(0)) | int }}}}",
        entity_id="sensor.test_heating_cycling_2h",
        unique_id="test_heating_cycling_2h",
    )
    
    # Test the calculation
    sensor.handle_coordinator_update()
    
    # Should calculate 150.7 - 100.3 = 50.4, rounded to 50
    assert sensor._state == 50


def test_template_sensor_4h_calculation_with_negative_result(mock_entry, mock_coordinator):
    """Test Template-Sensor für 4h-Berechnung mit negativem Ergebnis."""
    from custom_components.lambda_heat_pumps.sensor import LambdaTemplateSensor
    
    # Mock hass.states.get to return values where last_4h > total (shouldn't happen in practice)
    def mock_states_get(entity_id):
        mock_state = Mock()
        if "total" in entity_id:
            mock_state.state = "100"  # Total value
        elif "last_4h" in entity_id:
            mock_state.state = "150"  # Last 4h value (higher than total)
        else:
            mock_state.state = "0"
        return mock_state
    
    mock_coordinator.hass.states.get.side_effect = mock_states_get
    
    # Create template sensor for 4h calculation
    sensor = LambdaTemplateSensor(
        coordinator=mock_coordinator,
        entry=mock_entry,
        sensor_id="heating_cycling_4h",
        name="Heating Cycling 4h",
        unit="cycles",
        state_class="total",
        device_class=None,
        device_type="hp",
        template_str="{{% set total = states('sensor.test_heating_cycling_total') | float(0) %}}{{% set last_4h = states('sensor.test_heating_cycling_last_4h') | float(0) %}}{{{{ ((total - last_4h) | round(0)) | int }}}}",
        entity_id="sensor.test_heating_cycling_4h",
        unique_id="test_heating_cycling_4h",
    )
    
    # Test the calculation
    sensor.handle_coordinator_update()
    
    # Should calculate 100 - 150 = -50
    assert sensor._state == -50
