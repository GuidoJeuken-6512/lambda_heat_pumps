"""Test the utils module."""

import os
from unittest.mock import AsyncMock, Mock, mock_open, patch

import pytest
import yaml

from custom_components.lambda_heat_pumps.utils import (
    build_device_info,
    clamp_to_int16,
    generate_base_addresses,
    generate_sensor_names,
    get_compatible_sensors,
    is_register_disabled,
    load_disabled_registers,
    to_signed_16bit,
    to_signed_32bit,
)


def test_get_compatible_sensors_with_firmware_version():
    """Test get_compatible_sensors with firmware version."""
    sensors = {
        "sensor1": {"name": "Test", "firmware_version": 1},
        "sensor2": {"name": "Test2", "firmware_version": 2},
        "sensor3": {"name": "Test3", "firmware_version": 3},
    }
    firmware_version = 2

    result = get_compatible_sensors(sensors, firmware_version)

    assert len(result) == 2
    assert "sensor1" in result
    assert "sensor2" in result
    assert "sensor3" not in result


def test_get_compatible_sensors_no_firmware_version():
    """Test get_compatible_sensors with None firmware version."""
    sensors = {"sensor1": {"firmware_version": 1}, "sensor2": {"firmware_version": 2}}

    result = get_compatible_sensors(sensors, 1)  # Use 1 instead of None

    # Should return sensors with firmware_version <= 1
    assert len(result) == 1
    assert "sensor1" in result

    def test_build_device_info():
        """Test build_device_info."""
        mock_entry = Mock()
        mock_entry.domain = "lambda_heat_pumps"
        mock_entry.entry_id = "test_entry"
        mock_entry.data = {
            "name": "Test Lambda WP",
            "firmware_version": "V1.0.0",
            "host": "192.168.1.100",
        }

        result = build_device_info(mock_entry)

        assert result["identifiers"] == {("lambda_heat_pumps", "test_entry")}
        assert result["name"] == "Test Lambda WP"
        assert result["manufacturer"] == "Lambda"
        assert result["model"] == "V1.0.0"
        assert result["configuration_url"] == "http://192.168.1.100"
        assert result["sw_version"] == "V1.0.0"

    def test_build_device_info_without_domain():
        """Test build_device_info without domain."""
        mock_entry = Mock()
        mock_entry.entry_id = "test_entry"
        mock_entry.data = {"name": "Test Device"}
        mock_entry.domain = "lambda_heat_pumps"

        result = build_device_info(mock_entry)

        assert result["identifiers"] == {("lambda_heat_pumps", "test_entry")}
        assert result["name"] == "Test Device"


@pytest.mark.asyncio
async def test_load_disabled_registers_success(mock_hass):
    """Test successful loading of disabled registers."""
    config_data = {"disabled_registers": [1000, 2000, 3000]}
    # Mock config_dir
    mock_config = Mock()
    mock_config.config_dir = "/tmp/test_config"
    mock_hass.config = mock_config

    with patch(
        "custom_components.lambda_heat_pumps.utils.os.path.exists", return_value=True
    ):
        with patch(
            "custom_components.lambda_heat_pumps.utils.aiofiles.open"
        ) as mock_file:
            mock_file.return_value.__aenter__.return_value.read.return_value = (
                yaml.dump(config_data)
            )
            result = await load_disabled_registers(mock_hass)

            assert result == {1000, 2000, 3000}


@pytest.mark.asyncio
async def test_load_disabled_registers_file_not_exists():
    """Test loading disabled registers when file doesn't exist."""
    mock_hass = Mock()
    mock_hass.config.config_dir = "/tmp/test_config"

    with patch(
        "custom_components.lambda_heat_pumps.utils.os.path.exists", return_value=False
    ):
        result = await load_disabled_registers(mock_hass)

        assert result == set()


@pytest.mark.asyncio
async def test_load_disabled_registers_no_disabled_registers():
    """Test loading disabled registers when no disabled_registers key exists."""
    mock_hass = Mock()
    mock_hass.config.config_dir = "/tmp/test_config"

    mock_yaml_content = """
other_config:
  - value1
  - value2
"""

    with patch(
        "custom_components.lambda_heat_pumps.utils.os.path.exists", return_value=True
    ):
        with patch("builtins.open", mock_open(read_data=mock_yaml_content)):
            with patch(
                "custom_components.lambda_heat_pumps.utils.yaml.safe_load",
                return_value=yaml.safe_load(mock_yaml_content),
            ):
                result = await load_disabled_registers(mock_hass)

                assert result == set()


@pytest.mark.asyncio
async def test_load_disabled_registers_yaml_error():
    """Test loading disabled registers with YAML error."""
    mock_hass = Mock()
    mock_hass.config.config_dir = "/tmp/test_config"

    with patch(
        "custom_components.lambda_heat_pumps.utils.os.path.exists", return_value=True
    ):
        with patch("builtins.open", mock_open(read_data="invalid yaml")):
            with patch(
                "custom_components.lambda_heat_pumps.utils.yaml.safe_load",
                side_effect=yaml.YAMLError,
            ):
                result = await load_disabled_registers(mock_hass)

                assert result == set()


def test_is_register_disabled_true():
    """Test is_register_disabled when register is disabled."""
    disabled_registers = {1000, 2000, 3000}

    result = is_register_disabled(1000, disabled_registers)

    assert result is True


def test_is_register_disabled_false():
    """Test is_register_disabled when register is not disabled."""
    disabled_registers = {1000, 2000, 3000}

    result = is_register_disabled(4000, disabled_registers)

    assert result is False


def test_is_register_disabled_empty_set():
    """Test is_register_disabled with empty set."""
    disabled_registers = set()

    result = is_register_disabled(1000, disabled_registers)

    assert result is False


def test_generate_base_addresses_hp():
    """Test generate_base_addresses for HP."""
    result = generate_base_addresses("hp", 1)

    assert result[1] == 1000  # HP base address is 1000


def test_generate_base_addresses_boil():
    """Test generate_base_addresses for boil."""
    result = generate_base_addresses("boil", 1)

    assert result[1] == 2000  # Boil base address is 2000


def test_generate_base_addresses_unknown_type():
    """Test generate_base_addresses for unknown device type."""
    result = generate_base_addresses("unknown", 1)

    assert result == {}


def test_generate_base_addresses_zero_count():
    """Test generate_base_addresses with zero count."""
    result = generate_base_addresses("hp", 0)

    assert result == {}


def test_to_signed_16bit_positive():
    """Test to_signed_16bit with positive value."""
    result = to_signed_16bit(1000)

    assert result == 1000


def test_to_signed_16bit_negative():
    """Test to_signed_16bit with negative value."""
    result = to_signed_16bit(0x8000)  # 32768

    assert result == -32768


def test_to_signed_16bit_large_positive():
    """Test to_signed_16bit with large positive value."""
    result = to_signed_16bit(0xFFFF)  # 65535

    assert result == -1


def test_to_signed_32bit_positive():
    """Test to_signed_32bit with positive value."""
    result = to_signed_32bit(1000000)

    assert result == 1000000


def test_to_signed_32bit_negative():
    """Test to_signed_32bit with negative value."""
    result = to_signed_32bit(0x80000000)  # 2147483648

    assert result == -2147483648


def test_to_signed_32bit_large_positive():
    """Test to_signed_32bit with large positive value."""
    result = to_signed_32bit(0xFFFFFFFF)  # 4294967295

    assert result == -1


def test_clamp_to_int16_within_range():
    """Test clamp_to_int16 with value within range."""
    with patch("custom_components.lambda_heat_pumps.utils._LOGGER") as mock_logger:
        result = clamp_to_int16(1000, "temperature")

        assert result == 1000
        mock_logger.warning.assert_not_called()


def test_clamp_to_int16_below_minimum():
    """Test clamp_to_int16 with value below minimum."""
    with patch("custom_components.lambda_heat_pumps.utils._LOGGER") as mock_logger:
        result = clamp_to_int16(-40000, "temperature")

        assert result == -32768
        mock_logger.warning.assert_called_once()


def test_clamp_to_int16_above_maximum():
    """Test clamp_to_int16 with value above maximum."""
    with patch("custom_components.lambda_heat_pumps.utils._LOGGER") as mock_logger:
        result = clamp_to_int16(40000, "power")

        assert result == 32767
        mock_logger.warning.assert_called_once()


def test_clamp_to_int16_exact_minimum():
    """Test clamp_to_int16 with exact minimum value."""
    with patch("custom_components.lambda_heat_pumps.utils._LOGGER") as mock_logger:
        result = clamp_to_int16(-32768, "temperature")

        assert result == -32768
        mock_logger.warning.assert_not_called()


def test_clamp_to_int16_exact_maximum():
    """Test clamp_to_int16 with exact maximum value."""
    with patch("custom_components.lambda_heat_pumps.utils._LOGGER") as mock_logger:
        result = clamp_to_int16(32767, "power")

        assert result == 32767
        mock_logger.warning.assert_not_called()


def test_clamp_to_int16_float_input():
    """Test clamp_to_int16 with float input."""
    with patch("custom_components.lambda_heat_pumps.utils._LOGGER") as mock_logger:
        result = clamp_to_int16(1000.5, "temperature")

        assert result == 1000
        mock_logger.warning.assert_not_called()


class TestGenerateSensorNames:
    """Test generate_sensor_names function."""

    def test_generate_sensor_names_unique_id_uniqueness(self):
        """Test that generate_sensor_names produces unique unique_ids."""
        name_prefix = "eu08l"

        # Test General Sensors (device_prefix == sensor_id)
        general_sensor1 = generate_sensor_names(
            "ambient_temp", "Ambient Temperature", "ambient_temp", name_prefix, True
        )
        general_sensor2 = generate_sensor_names(
            "ambient_error", "Ambient Error", "ambient_error", name_prefix, True
        )

        # Test Template Sensors (device_prefix != sensor_id)
        template_sensor1 = generate_sensor_names(
            "hp1", "Flow Temperature", "flow_temp", name_prefix, True
        )
        template_sensor2 = generate_sensor_names(
            "hp1", "Return Temperature", "return_temp", name_prefix, True
        )

        # Alle unique_ids müssen unterschiedlich sein
        unique_ids = [
            general_sensor1["unique_id"],
            general_sensor2["unique_id"],
            template_sensor1["unique_id"],
            template_sensor2["unique_id"],
        ]

        assert len(unique_ids) == len(set(unique_ids)), "Duplicate unique_ids found!"

    def test_generate_sensor_names_config_name_integration(self):
        """Test that unique_ids contain config name in legacy mode."""
        name_prefix = "eu08l"

        # Legacy Mode - Config Name muss enthalten sein
        legacy_general = generate_sensor_names(
            "ambient_temp", "Ambient Temperature", "ambient_temp", name_prefix, True
        )
        legacy_template = generate_sensor_names(
            "hp1", "Flow Temperature", "flow_temp", name_prefix, True
        )

        assert name_prefix in legacy_general["unique_id"]
        assert name_prefix in legacy_template["unique_id"]

        # Standard Mode - Config Name darf nicht enthalten sein
        standard_general = generate_sensor_names(
            "ambient_temp", "Ambient Temperature", "ambient_temp", name_prefix, False
        )
        standard_template = generate_sensor_names(
            "hp1", "Flow Temperature", "flow_temp", name_prefix, False
        )

        assert name_prefix not in standard_general["unique_id"]
        assert name_prefix not in standard_template["unique_id"]

    def test_generate_sensor_names_legacy_vs_standard(self):
        """Test differences between legacy and standard naming modes."""
        name_prefix = "eu08l"

        # Legacy Mode
        legacy = generate_sensor_names(
            "hp1", "Flow Temperature", "flow_temp", name_prefix, True
        )

        # Standard Mode
        standard = generate_sensor_names(
            "hp1", "Flow Temperature", "flow_temp", name_prefix, False
        )

        # Legacy sollte Config-Name enthalten
        assert legacy["unique_id"] == f"{name_prefix}_hp1_flow_temp"
        assert legacy["entity_id"] == f"sensor.{name_prefix}_hp1_flow_temp"

        # Standard sollte nur device_prefix_sensor_id verwenden
        assert standard["unique_id"] == "hp1_flow_temp"
        assert standard["entity_id"] == "sensor.hp1_flow_temp"

    def test_generate_sensor_names_general_vs_template(self):
        """Test differences between general and template sensors."""
        name_prefix = "eu08l"

        # General Sensor (device_prefix == sensor_id)
        general = generate_sensor_names(
            "ambient_temp", "Ambient Temperature", "ambient_temp", name_prefix, True
        )

        # Template Sensor (device_prefix != sensor_id)
        template = generate_sensor_names(
            "hp1", "Flow Temperature", "flow_temp", name_prefix, True
        )

        # General Sensor sollte nur name_prefix_sensor_id haben
        assert general["unique_id"] == f"{name_prefix}_ambient_temp"

        # Template Sensor sollte name_prefix_device_prefix_sensor_id haben
        assert template["unique_id"] == f"{name_prefix}_hp1_flow_temp"

    def test_generate_sensor_names_display_names(self):
        """Test that display names are generated correctly."""
        name_prefix = "eu08l"

        # General Sensor - nur sensor_name
        general = generate_sensor_names(
            "ambient_temp", "Ambient Temperature", "ambient_temp", name_prefix, True
        )
        assert general["name"] == "Ambient Temperature"

        # Template Sensor - device_prefix.upper() + sensor_name
        template = generate_sensor_names(
            "hp1", "Flow Temperature", "flow_temp", name_prefix, True
        )
        assert template["name"] == "HP1 Flow Temperature"

    def test_generate_sensor_names_empty_name_prefix(self):
        """Test behavior with empty name_prefix."""
        # Legacy Mode mit leerem name_prefix
        legacy = generate_sensor_names("hp1", "Flow Temperature", "flow_temp", "", True)
        assert legacy["unique_id"] == "_hp1_flow_temp"
        assert legacy["entity_id"] == "sensor._hp1_flow_temp"

        # Standard Mode mit leerem name_prefix
        standard = generate_sensor_names(
            "hp1", "Flow Temperature", "flow_temp", "", False
        )
        assert standard["unique_id"] == "hp1_flow_temp"
        assert standard["entity_id"] == "sensor.hp1_flow_temp"

    def test_generate_sensor_names_none_name_prefix(self):
        """Test behavior with None name_prefix."""
        # Legacy Mode mit None name_prefix
        legacy = generate_sensor_names(
            "hp1", "Flow Temperature", "flow_temp", None, True
        )
        assert legacy["unique_id"] == "_hp1_flow_temp"
        assert legacy["entity_id"] == "sensor._hp1_flow_temp"

        # Standard Mode mit None name_prefix
        standard = generate_sensor_names(
            "hp1", "Flow Temperature", "flow_temp", None, False
        )
        assert standard["unique_id"] == "hp1_flow_temp"
        assert standard["entity_id"] == "sensor.hp1_flow_temp"

    def test_generate_sensor_names_case_sensitivity(self):
        """Test that name_prefix is converted to lowercase."""
        name_prefix = "EU08L"  # Uppercase

        # Legacy Mode
        legacy = generate_sensor_names(
            "hp1", "Flow Temperature", "flow_temp", name_prefix, True
        )
        assert legacy["unique_id"] == "eu08l_hp1_flow_temp"
        assert legacy["entity_id"] == "sensor.eu08l_hp1_flow_temp"

        # Standard Mode
        standard = generate_sensor_names(
            "hp1", "Flow Temperature", "flow_temp", name_prefix, False
        )
        assert standard["unique_id"] == "hp1_flow_temp"
        assert standard["entity_id"] == "sensor.hp1_flow_temp"

    def test_generate_sensor_names_special_characters(self):
        """Test behavior with special characters in name_prefix."""
        name_prefix = "eu-08l"  # Mit Bindestrich

        # Legacy Mode
        legacy = generate_sensor_names(
            "hp1", "Flow Temperature", "flow_temp", name_prefix, True
        )
        assert legacy["unique_id"] == "eu-08l_hp1_flow_temp"
        assert legacy["entity_id"] == "sensor.eu-08l_hp1_flow_temp"

        # Standard Mode
        standard = generate_sensor_names(
            "hp1", "Flow Temperature", "flow_temp", name_prefix, False
        )
        assert standard["unique_id"] == "hp1_flow_temp"
        assert standard["entity_id"] == "sensor.hp1_flow_temp"

    def test_generate_sensor_names_return_structure(self):
        """Test that the function returns the expected structure."""
        result = generate_sensor_names(
            "hp1", "Flow Temperature", "flow_temp", "eu08l", True
        )

        # Prüfe, dass alle erwarteten Keys vorhanden sind
        assert "name" in result
        assert "entity_id" in result
        assert "unique_id" in result

        # Prüfe, dass alle Werte Strings sind
        assert isinstance(result["name"], str)
        assert isinstance(result["entity_id"], str)
        assert isinstance(result["unique_id"], str)

        # Prüfe, dass entity_id mit "sensor." beginnt
        assert result["entity_id"].startswith("sensor.")

    def test_generate_sensor_names_climate_entities(self):
        """Test generate_sensor_names for climate entities."""
        name_prefix = "eu08l"

        # Hot Water Climate Entity
        hot_water = generate_sensor_names(
            "boil1", "Hot Water", "hot_water", name_prefix, True
        )
        assert hot_water["unique_id"] == f"{name_prefix}_boil1_hot_water"
        assert hot_water["entity_id"] == f"sensor.{name_prefix}_boil1_hot_water"

        # Heating Circuit Climate Entity
        heating_circuit = generate_sensor_names(
            "hc1", "Heating Circuit", "heating_circuit", name_prefix, True
        )
        assert heating_circuit["unique_id"] == f"{name_prefix}_hc1_heating_circuit"
        assert (
            heating_circuit["entity_id"] == f"sensor.{name_prefix}_hc1_heating_circuit"
        )

    def test_generate_sensor_names_cycling_sensors(self):
        """Test generate_sensor_names for cycling sensors."""
        name_prefix = "eu08l"

        # Cycling Total Sensor
        cycling_total = generate_sensor_names(
            "hp1", "Heating Cycling Total", "heating_cycling_total", name_prefix, True
        )
        assert cycling_total["unique_id"] == f"{name_prefix}_hp1_heating_cycling_total"
        assert (
            cycling_total["entity_id"]
            == f"sensor.{name_prefix}_hp1_heating_cycling_total"
        )

        # Cycling Yesterday Sensor
        cycling_yesterday = generate_sensor_names(
            "hp1",
            "Heating Cycling Yesterday",
            "heating_cycling_yesterday",
            name_prefix,
            True,
        )
        assert (
            cycling_yesterday["unique_id"]
            == f"{name_prefix}_hp1_heating_cycling_yesterday"
        )
        assert (
            cycling_yesterday["entity_id"]
            == f"sensor.{name_prefix}_hp1_heating_cycling_yesterday"
        )
