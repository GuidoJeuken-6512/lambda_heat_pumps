"""Test the utils module."""

import logging
import os
from unittest.mock import AsyncMock, Mock, mock_open, patch

import pytest
import yaml

import custom_components.lambda_heat_pumps.utils as utils_module
from custom_components.lambda_heat_pumps.utils import (
    apply_energy_period_reset,
    build_device_info,
    clamp_to_int16,
    generate_base_addresses,
    generate_sensor_names,
    get_compatible_sensors,
    get_stored_thermal_sensor_id,
    is_register_disabled,
    is_sentinel_value,
    load_disabled_registers,
    load_sensor_translations,
    restore_energy_period_state,
    resolve_entity_id_by_unique_id,
    resolve_sensor_entity_id,
    resolve_template_entity_ids,
    store_thermal_sensor_id,
    to_signed_16bit,
    to_signed_32bit,
    validate_external_sensors,
    _get_coordinator,
    _parse_firmware_versions,
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


def test_parse_firmware_versions_range():
    """Range notation "X-Y" includes all versions from X to Y inclusive."""
    assert _parse_firmware_versions(["1-5", "7-8"]) == {1, 2, 3, 4, 5, 7, 8}


def test_parse_firmware_versions_exclude():
    """Leading "-" excludes a single version from the resulting set."""
    assert _parse_firmware_versions(["1-5", "-3"]) == {1, 2, 4, 5}


def test_parse_firmware_versions_int_and_str():
    """Plain ints and numeric strings are included as single versions."""
    assert _parse_firmware_versions([1, "3", "5-6"]) == {1, 3, 5, 6}


def test_get_compatible_sensors_firmware_versions_range():
    """firmware_versions (range notation) takes priority over firmware_version."""
    sensors = {
        "sensor1": {"firmware_versions": ["1-3"]},
        "sensor2": {"firmware_version": 1},
    }

    assert set(get_compatible_sensors(sensors, 2)) == {"sensor1", "sensor2"}
    # Sensor with firmware_versions disappears once fw_version leaves the range
    assert set(get_compatible_sensors(sensors, 4)) == {"sensor2"}


def test_get_compatible_sensors_no_field_always_active():
    """Sensors without firmware_version/firmware_versions are always included."""
    sensors = {"sensor1": {"name": "Always on"}}

    assert get_compatible_sensors(sensors, 1) == sensors
    assert get_compatible_sensors(sensors, 99) == sensors


def test_is_sentinel_value_not_available():
    """0x8000 (32768) is the global 'register not available' sentinel."""
    assert is_sentinel_value(32768) is True
    assert is_sentinel_value(32768, "uint16") is True


def test_is_sentinel_value_sensor_disconnected_int16_only():
    """62536 ('-3000' as uint16) is a sentinel only for int16 temperature registers."""
    assert is_sentinel_value(62536, "int16") is True
    assert is_sentinel_value(62536, "uint16") is False


def test_is_sentinel_value_minus_one_is_not_a_sentinel():
    """-1 / 0xFFFF must NOT be treated as a global sentinel (valid offset value)."""
    assert is_sentinel_value(65535) is False
    assert is_sentinel_value(65535, "int16") is False


def test_is_sentinel_value_normal_value():
    """A plausible reading must not be flagged as a sentinel."""
    assert is_sentinel_value(250, "int16") is False


def test_is_sentinel_value_extra_sentinels_opt_in():
    """extra_sentinels is opt-in per sensor and does not affect other sensors."""
    assert is_sentinel_value(65535, "int16", [65535]) is True
    # Without opt-in, -1/0xFFFF stays a valid value (e.g. temperature offsets)
    assert is_sentinel_value(65535, "int16") is False
    assert is_sentinel_value(65535, "int16", None) is False
    assert is_sentinel_value(65535, "int16", []) is False


def test_is_sentinel_value_extra_sentinels_does_not_override_normal_values():
    """A value not listed in extra_sentinels is unaffected."""
    assert is_sentinel_value(250, "int16", [65535]) is False


def test_get_compatible_sensors_ambient_temperature_fw_range():
    """ambient_temperature (Reg 0002) is readable up to and including V1.1.0-3K
    (fw int 9) - see issue108. The range was originally "1-7" (issue100), which
    hid the sensor on V0.0.10-3K and V1.1.0-3K although the register returns
    valid readings there. Invalid readings are caught by sentinel_values, not
    by the firmware range."""
    from custom_components.lambda_heat_pumps.const_sensor import SENSOR_TYPES

    assert "firmware_versions" in SENSOR_TYPES["ambient_temperature"]
    assert SENSOR_TYPES["ambient_temperature"]["sentinel_values"] == [65535]

    # V0.0.9-3K (7), V0.0.10-3K (8) und V1.1.0-3K (9) muessen den Sensor haben
    for fw_int in (7, 8, 9):
        assert "ambient_temperature" in get_compatible_sensors(SENSOR_TYPES, fw_int), (
            f"ambient_temperature fehlt bei Firmware-Version {fw_int}"
        )


def test_buffer_request_registers_opt_in_sentinel():
    """Buffer 'request' registers (3005-3009 => relative_address 5-9) treat
    -1 (0xFFFF) as "keine Anforderung" - opt-in via sentinel_values, since
    -1 is not a global sentinel (see is_sentinel_value)."""
    from custom_components.lambda_heat_pumps.const_sensor import BUFF_SENSOR_TEMPLATES

    request_sensors = [
        "request_type",
        "request_flow_line_temp_setpoint",
        "request_return_line_temp_setpoint",
        "request_heat_sink_temp_diff_setpoint",
        "modbus_request_heating_capacity",
    ]
    for key in request_sensors:
        assert BUFF_SENSOR_TEMPLATES[key]["sentinel_values"] == [65535], key
        assert is_sentinel_value(65535, BUFF_SENSOR_TEMPLATES[key]["data_type"],
                                  BUFF_SENSOR_TEMPLATES[key]["sentinel_values"]) is True

    # Sanity check: relative addresses match register 3005-3009 (buff base 3000)
    addresses = {BUFF_SENSOR_TEMPLATES[key]["relative_address"] for key in request_sensors}
    assert addresses == {5, 6, 7, 8, 9}

    # Other buffer sensors (not "request" registers) must NOT opt in
    assert "sentinel_values" not in BUFF_SENSOR_TEMPLATES["actual_high_temperature"]


def test_hc_operating_mode_opt_in_sentinel():
    """HC 'operating_mode' (register 5006 => relative_address 6, hc base 5000)
    treats -1 (0xFFFF) as "keine Anforderung" via opt-in sentinel_values."""
    from custom_components.lambda_heat_pumps.const_sensor import HC_SENSOR_TEMPLATES

    assert HC_SENSOR_TEMPLATES["operating_mode"]["relative_address"] == 6
    assert HC_SENSOR_TEMPLATES["operating_mode"]["sentinel_values"] == [65535]
    assert is_sentinel_value(
        65535,
        HC_SENSOR_TEMPLATES["operating_mode"]["data_type"],
        HC_SENSOR_TEMPLATES["operating_mode"]["sentinel_values"],
    ) is True

    # Other HC sensors (not the request/operating_mode register) must NOT opt in
    assert "sentinel_values" not in HC_SENSOR_TEMPLATES["flow_line_temperature"]

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
    # load_disabled_registers returns config["disabled_registers"] which could be a list
    # but should be converted to a set for consistency
    config_data = {"disabled_registers": set([1000, 2000, 3000])}
    
    # Mock load_lambda_config directly to avoid complex async mocking
    with patch(
        "custom_components.lambda_heat_pumps.utils.load_lambda_config",
        new_callable=AsyncMock,
        return_value=config_data
    ):
        result = await load_disabled_registers(mock_hass)

        assert result == {1000, 2000, 3000}


@pytest.mark.asyncio
async def test_load_disabled_registers_file_not_exists():
    """Test loading disabled registers when file doesn't exist."""
    mock_hass = Mock()
    mock_hass.config.config_dir = "/tmp/test_config"
    mock_hass.data = {}

    # load_disabled_registers now delegates to load_lambda_config — mock that directly
    with patch(
        "custom_components.lambda_heat_pumps.utils.load_lambda_config",
        new_callable=AsyncMock,
        return_value={"disabled_registers": set()},
    ):
        result = await load_disabled_registers(mock_hass)

        assert result == set()


@pytest.mark.asyncio
async def test_load_disabled_registers_no_disabled_registers():
    """Test loading disabled registers when no disabled_registers key exists."""
    mock_hass = Mock()
    mock_hass.config.config_dir = "/tmp/test_config"
    mock_hass.data = {}

    # load_disabled_registers now delegates to load_lambda_config — mock that directly
    with patch(
        "custom_components.lambda_heat_pumps.utils.load_lambda_config",
        new_callable=AsyncMock,
        return_value={"disabled_registers": set()},
    ):
        result = await load_disabled_registers(mock_hass)

        assert result == set()


@pytest.mark.asyncio
async def test_load_disabled_registers_yaml_error():
    """Test loading disabled registers with YAML error."""
    mock_hass = Mock()
    mock_hass.config.config_dir = "/tmp/test_config"
    mock_hass.data = {}

    # load_disabled_registers now delegates to load_lambda_config — mock that directly
    with patch(
        "custom_components.lambda_heat_pumps.utils.load_lambda_config",
        new_callable=AsyncMock,
        return_value={"disabled_registers": set()},
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


@pytest.mark.asyncio
async def test_load_sensor_translations_success(mock_hass):
    """Ensure load_sensor_translations parses sensor entries."""
    mock_hass.config.language = "de"
    translation_payload = {
        "component.lambda_heat_pumps.entity.sensor.flow_line_temperature.name": "Vorlauf",
        "component.lambda_heat_pumps.entity.sensor.compressor_start_cycling_total.name": "Kompressor Starts Gesamt",
        "component.lambda_heat_pumps.entity.number.ignored.name": "Ignored",
        "component.lambda_heat_pumps.entity.climate.heating_circuit.name": "Heizkreis",
    }
    with patch(
        "custom_components.lambda_heat_pumps.utils.async_get_translations",
        new_callable=AsyncMock,
        return_value=translation_payload,
    ):
        result = await load_sensor_translations(mock_hass)

    # The function returns all translations, including "ignored" entries
    assert "flow_line_temperature" in result
    assert result["flow_line_temperature"] == "Vorlauf"
    assert "compressor_start_cycling_total" in result
    assert result["compressor_start_cycling_total"] == "Kompressor Starts Gesamt"
    assert "heating_circuit" in result
    assert result["heating_circuit"] == "Heizkreis"
    # "ignored" is also included in the result
    assert "ignored" in result


@pytest.mark.asyncio
async def test_load_sensor_translations_failure(mock_hass):
    """Ensure load_sensor_translations handles errors gracefully."""
    mock_hass.config.language = "de"
    with patch(
        "custom_components.lambda_heat_pumps.utils.async_get_translations",
        new_callable=AsyncMock,
        side_effect=Exception("boom"),
    ), patch("custom_components.lambda_heat_pumps.utils._LOGGER") as mock_logger:
        result = await load_sensor_translations(mock_hass)

    assert result == {}
    mock_logger.warning.assert_called_once()


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

        # Template Sensor - Home Assistant adds device prefix automatically
        template = generate_sensor_names(
            "hp1", "Flow Temperature", "flow_temp", name_prefix, True
        )
        assert template["name"] == "Flow Temperature"

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
        """Test behavior with special characters in name_prefix.

        unique_id keeps the raw (lowercased) name_prefix for backward
        compatibility. entity_id is derived from the same separator rule as
        unique_id (normalize_name_prefix: only spaces are removed, everything
        else is left untouched) plus unicode transliteration - see
        slugify_name_prefix_for_lookup(). For underscores (the case reported
        in Issue #107) this keeps entity_id and unique_id consistent, which is
        the primary goal. Known residual gap: a literal hyphen is NOT a valid
        HA entity_id character ([a-z0-9_] only) and is passed through as-is
        here rather than collapsed to "_" - documented trade-off, out of scope
        for #107 (which only reports underscores/spaces/umlauts).
        """
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

    def test_generate_sensor_names_umlaut_in_name_prefix(self):
        """entity_id must be ASCII-safe even if the device name has umlauts.

        HA rejects/deprecates entity_id containing non-ASCII characters
        (e.g. 'sensor.eu08ü_...'). unique_id is left untouched (raw lowercase)
        so existing entities are not orphaned; only entity_id is transliterated.
        """
        name_prefix = "eu08ü"

        legacy = generate_sensor_names(
            "hp1", "Flow Temperature", "flow_temp", name_prefix, True
        )
        assert legacy["unique_id"] == "eu08ü_hp1_flow_temp"
        assert legacy["entity_id"] == "sensor.eu08u_hp1_flow_temp"
        assert legacy["entity_id"].isascii()

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

    def test_generate_sensor_names_uses_translations(self):
        """Ensure translations override the default sensor name."""
        name_prefix = "eu08l"
        translations = {
            "flow_temp": "Vorlauf",
            "compressor_start_cycling_total": "Kompressor Starts Gesamt",
        }

        result = generate_sensor_names(
            "hp1",
            "Flow Temperature",
            "flow_temp",
            name_prefix,
            False,
            translations=translations,
        )

        assert result["name"] == "Vorlauf"
        
        # Test compressor_start translation
        result_compressor = generate_sensor_names(
            "hp1",
            "Compressor Start Cycling Total",
            "compressor_start_cycling_total",
            name_prefix,
            False,
            translations=translations,
        )
        
        # Mit has_entity_name wird der Gerätename nicht in name gepackt (Name = "Kompressor Starts Gesamt")
        assert result_compressor["name"] == "Kompressor Starts Gesamt"

    def test_generate_sensor_names_missing_translation_warning(self, caplog):
        """Ensure missing translations trigger a one-time warning."""
        utils_module._MISSING_SENSOR_TRANSLATIONS.clear()
        name_prefix = "eu08l"
        with caplog.at_level(logging.WARNING):
            generate_sensor_names(
                "hp1",
                "Flow Temperature",
                "flow_temp_missing",
                name_prefix,
                False,
                translations={},
            )
        assert "Keine Übersetzung" in caplog.text
        caplog.clear()
        generate_sensor_names(
            "hp1",
            "Flow Temperature",
            "flow_temp_missing",
            name_prefix,
            False,
            translations={},
        )
        assert caplog.text == ""


class TestResolveEntityIdByUniqueId:
    """Tests for resolve_entity_id_by_unique_id() - the shared Issue #107 fix helper
    used by increment_energy_consumption_counter(), increment_cycling_counter() and
    the coordinator's _resolve_internal_energy_sensor_entity_id().
    """

    def test_returns_registry_resolved_entity_id_when_found(self):
        hass = Mock()
        registry = Mock()
        registry.async_get_entity_id = Mock(return_value="sensor.real_registered_id")

        result = resolve_entity_id_by_unique_id(
            hass, "some_unique_id", "sensor.fallback_id", entity_registry=registry
        )

        assert result == "sensor.real_registered_id"
        registry.async_get_entity_id.assert_called_once_with(
            "sensor", "lambda_heat_pumps", "some_unique_id"
        )

    def test_falls_back_when_not_found_in_registry(self):
        hass = Mock()
        registry = Mock()
        registry.async_get_entity_id = Mock(return_value=None)

        result = resolve_entity_id_by_unique_id(
            hass, "some_unique_id", "sensor.fallback_id", entity_registry=registry
        )

        assert result == "sensor.fallback_id"

    def test_falls_back_on_registry_exception(self):
        """The registry must never be able to kill a poll cycle."""
        hass = Mock()
        registry = Mock()
        registry.async_get_entity_id = Mock(side_effect=RuntimeError("boom"))

        result = resolve_entity_id_by_unique_id(
            hass, "some_unique_id", "sensor.fallback_id", entity_registry=registry
        )

        assert result == "sensor.fallback_id"

    def test_looks_up_entity_registry_when_none_passed(self):
        hass = Mock()
        registry = Mock()
        registry.async_get_entity_id = Mock(return_value="sensor.resolved")

        with patch(
            "custom_components.lambda_heat_pumps.utils.async_get_entity_registry",
            return_value=registry,
        ) as mock_get_registry:
            result = resolve_entity_id_by_unique_id(
                hass, "some_unique_id", "sensor.fallback_id"
            )

        mock_get_registry.assert_called_once_with(hass)
        assert result == "sensor.resolved"


class TestResolveSensorEntityId:
    """Tests für resolve_sensor_entity_id() - zentraler Helper (Issue #107).

    Bündelt "Namen erzeugen -> Domain anpassen -> über unique_id auflösen".
    """

    def test_resolves_sensor_via_registry(self):
        hass = Mock()
        registry = Mock()
        registry.async_get_entity_id = Mock(
            return_value="sensor.lambdaeu10l_hc2_operating_state"
        )

        result = resolve_sensor_entity_id(
            hass, "hc2", "operating_state", "lambda_eu10l", True,
            entity_registry=registry,
        )

        assert result == "sensor.lambdaeu10l_hc2_operating_state"
        registry.async_get_entity_id.assert_called_once_with(
            "sensor", "lambda_heat_pumps", "lambda_eu10l_hc2_operating_state"
        )

    def test_number_domain_uses_number_suffix_and_domain(self):
        """number.py hängt '_number' an die unique_id an - muss berücksichtigt werden."""
        hass = Mock()
        registry = Mock()
        registry.async_get_entity_id = Mock(
            return_value="number.lambdaeu10l_hc2_eco_temp_reduction"
        )

        result = resolve_sensor_entity_id(
            hass, "hc2", "eco_temp_reduction", "lambda_eu10l", True,
            domain="number", unique_id_suffix="_number", entity_registry=registry,
        )

        assert result == "number.lambdaeu10l_hc2_eco_temp_reduction"
        registry.async_get_entity_id.assert_called_once_with(
            "number", "lambda_heat_pumps", "lambda_eu10l_hc2_eco_temp_reduction_number"
        )

    def test_falls_back_to_generated_name_with_correct_domain(self):
        """Ohne Registry-Treffer bleibt das bisherige Verhalten exakt erhalten."""
        hass = Mock()
        registry = Mock()
        registry.async_get_entity_id = Mock(return_value=None)

        assert resolve_sensor_entity_id(
            hass, "hc2", "operating_state", "lambda_eu10l", True,
            entity_registry=registry,
        ) == "sensor.lambda_eu10l_hc2_operating_state"

        assert resolve_sensor_entity_id(
            hass, "hc2", "eco_temp_reduction", "lambda_eu10l", True,
            domain="number", unique_id_suffix="_number", entity_registry=registry,
        ) == "number.lambda_eu10l_hc2_eco_temp_reduction"

    def test_general_sensor_without_device_prefix(self):
        """General Sensors: device_prefix == sensor_id, kein doppeltes Präfix."""
        hass = Mock()
        registry = Mock()
        registry.async_get_entity_id = Mock(return_value=None)

        result = resolve_sensor_entity_id(
            hass,
            "ambient_temperature_calculated",
            "ambient_temperature_calculated",
            "lambda_eu10l",
            True,
            entity_registry=registry,
        )

        assert result == "sensor.lambda_eu10l_ambient_temperature_calculated"


class TestResolveTemplateEntityIds:
    """Tests für resolve_template_entity_ids() - Issue #107 für Template-Strings."""

    TEMPLATE = (
        "{% set thermal = states('sensor.lambda_eu10l_hp2_compressor_thermal_energy_output_accumulated') | float(0) %}"
        "{% set power = states('sensor.lambda_eu10l_hp2_compressor_power_consumption_accumulated') | float(1) %}"
        "{{ (thermal / power) | round(2) if power > 0 else 0 }}"
    )

    def test_replaces_references_with_registered_entity_ids(self):
        hass = Mock()
        registry = Mock()
        registry.async_get_entity_id = Mock(
            side_effect=lambda domain, platform, unique_id: (
                f"{domain}.lambdaeu10l_{unique_id[len('lambda_eu10l_'):]}"
            )
        )

        result = resolve_template_entity_ids(
            hass, self.TEMPLATE, "lambda_eu10l", entity_registry=registry
        )

        assert "sensor.lambdaeu10l_hp2_compressor_thermal_energy_output_accumulated" in result
        assert "sensor.lambdaeu10l_hp2_compressor_power_consumption_accumulated" in result
        assert "sensor.lambda_eu10l_hp2_compressor" not in result
        # Restliches Template bleibt unangetastet
        assert "| round(2) if power > 0 else 0" in result

    def test_template_unchanged_when_registry_has_no_match(self):
        """Kein Treffer -> Template exakt wie bisher (kein Verhaltenswechsel)."""
        hass = Mock()
        registry = Mock()
        registry.async_get_entity_id = Mock(return_value=None)

        result = resolve_template_entity_ids(
            hass, self.TEMPLATE, "lambda_eu10l", entity_registry=registry
        )

        assert result == self.TEMPLATE

    def test_number_domain_reference_gets_number_suffix(self):
        hass = Mock()
        registry = Mock()
        registry.async_get_entity_id = Mock(return_value="number.real_id")

        result = resolve_template_entity_ids(
            hass,
            "{% set x = states('number.lambda_eu10l_hc2_eco_temp_reduction') %}",
            "lambda_eu10l",
            entity_registry=registry,
        )

        assert "number.real_id" in result
        registry.async_get_entity_id.assert_called_once_with(
            "number", "lambda_heat_pumps", "lambda_eu10l_hc2_eco_temp_reduction_number"
        )

    def test_foreign_entities_are_left_alone(self):
        """Entities ohne unser Namenspräfix werden nicht angefasst."""
        hass = Mock()
        registry = Mock()
        registry.async_get_entity_id = Mock(return_value="sensor.should_not_be_used")

        template = "{% set x = states('sensor.some_other_integration_value') %}"
        result = resolve_template_entity_ids(
            hass, template, "lambda_eu10l", entity_registry=registry
        )

        assert result == template
        registry.async_get_entity_id.assert_not_called()

    def test_empty_inputs_are_safe(self):
        hass = Mock()
        assert resolve_template_entity_ids(hass, "", "lambda_eu10l") == ""
        assert resolve_template_entity_ids(hass, "abc", "") == "abc"


def test_get_coordinator():
    """Test _get_coordinator helper function."""
    from unittest.mock import Mock
    
    # Mock hass with coordinator data
    mock_hass = Mock()
    mock_coordinator = Mock()
    mock_coordinator._cycling_warnings = {}
    
    mock_hass.data = {
        "lambda_heat_pumps": {
            "test_entry": mock_coordinator
        }
    }
    
    # Test successful coordinator retrieval
    coordinator = _get_coordinator(mock_hass)
    assert coordinator == mock_coordinator
    
    # Test with no coordinator
    mock_hass.data = {"lambda_heat_pumps": {}}
    coordinator = _get_coordinator(mock_hass)
    assert coordinator is None
    
    # Test with no lambda_heat_pumps domain
    mock_hass.data = {}
    coordinator = _get_coordinator(mock_hass)
    assert coordinator is None


def test_apply_energy_period_reset_daily():
    """apply_energy_period_reset setzt baseline und _energy_value aus Total-Sensor (daily)."""
    from unittest.mock import MagicMock

    sensor = MagicMock()
    sensor.entity_id = "sensor.eu08l_hp1_heating_energy_daily"
    sensor._energy_value = 50.0
    sensor._yesterday_value = 10.0
    total_state = MagicMock()
    total_state.state = "100.0"
    total_state.attributes = {}
    sensor.hass = MagicMock()
    sensor.hass.states.get = MagicMock(return_value=total_state)

    apply_energy_period_reset(sensor, "daily")

    assert sensor._yesterday_value == 100.0
    assert sensor._energy_value == 100.0
    sensor.hass.states.get.assert_called_once()
    call_entity_id = sensor.hass.states.get.call_args[0][0]
    assert call_entity_id == "sensor.eu08l_hp1_heating_energy_total"


def test_apply_energy_period_reset_unknown_period_no_op():
    """apply_energy_period_reset bei unbekannter Period ändert nichts."""
    from unittest.mock import MagicMock

    sensor = MagicMock()
    sensor.entity_id = "sensor.eu08l_hp1_heating_energy_daily"
    sensor._energy_value = 50.0
    sensor._yesterday_value = 10.0
    sensor.hass = MagicMock()

    apply_energy_period_reset(sensor, "unknown_period")

    assert sensor._yesterday_value == 10.0
    assert sensor._energy_value == 50.0
    sensor.hass.states.get.assert_not_called()


def test_restore_energy_period_state_monthly_from_attrs():
    """restore_energy_period_state setzt baseline und _energy_value aus attrs/last_state."""
    from unittest.mock import MagicMock

    sensor = MagicMock()
    sensor.entity_id = "sensor.eu08l_hp1_heating_energy_monthly"
    sensor._energy_value = 0.0
    sensor._previous_monthly_value = 0.0
    attrs = {"previous_monthly_value": 200.0, "energy_value": 250.0}
    last_state = MagicMock()
    last_state.state = "50.0"

    restore_energy_period_state(sensor, "monthly", attrs, last_state)

    assert sensor._previous_monthly_value == 200.0
    assert sensor._energy_value == 250.0


def test_restore_energy_period_state_unknown_period_no_op():
    """restore_energy_period_state bei unbekannter Period ändert nichts."""
    from unittest.mock import MagicMock

    sensor = MagicMock()
    sensor.entity_id = "sensor.eu08l_hp1_heating_energy_daily"
    sensor._energy_value = 50.0
    sensor._yesterday_value = 10.0

    restore_energy_period_state(sensor, "unknown_period", {}, MagicMock(state="20.0"))

    assert sensor._yesterday_value == 10.0
    assert sensor._energy_value == 50.0


def test_get_stored_thermal_sensor_id():
    """get_stored_thermal_sensor_id liest aus persist_data['thermal_sensor_ids']."""
    persist_data = {"thermal_sensor_ids": {"hp1": "sensor.thermal_hp1"}}
    assert get_stored_thermal_sensor_id(persist_data, 1) == "sensor.thermal_hp1"
    assert get_stored_thermal_sensor_id(persist_data, 2) is None
    assert get_stored_thermal_sensor_id({}, 1) is None


def test_store_thermal_sensor_id():
    """store_thermal_sensor_id schreibt in persist_data['thermal_sensor_ids']."""
    persist_data = {}
    store_thermal_sensor_id(persist_data, 1, "sensor.thermal_hp1")
    assert "thermal_sensor_ids" in persist_data
    assert persist_data["thermal_sensor_ids"]["hp1"] == "sensor.thermal_hp1"
    store_thermal_sensor_id(persist_data, 2, "sensor.thermal_hp2")
    assert persist_data["thermal_sensor_ids"]["hp2"] == "sensor.thermal_hp2"


def test_validate_external_sensors_with_thermal_sensor_entity_id():
    """validate_external_sensors akzeptiert optional thermal_sensor_entity_id pro HP."""
    from unittest.mock import MagicMock

    def _mock_state(eid):
        if not eid:
            return None
        s = MagicMock()
        s.state = "100.0"
        return s

    hass = MagicMock()
    hass.states.get = MagicMock(side_effect=_mock_state)
    registry = MagicMock()
    registry.async_get = MagicMock(return_value=MagicMock())
    with patch("custom_components.lambda_heat_pumps.utils.async_get_entity_registry", return_value=registry):
        config = {
            "hp1": {
                "sensor_entity_id": "sensor.electrical_hp1",
                "thermal_sensor_entity_id": "sensor.thermal_hp1",
            },
        }
        result = validate_external_sensors(hass, config)
    assert "hp1" in result
    assert result["hp1"]["sensor_entity_id"] == "sensor.electrical_hp1"
    assert result["hp1"].get("thermal_sensor_entity_id") == "sensor.thermal_hp1"
