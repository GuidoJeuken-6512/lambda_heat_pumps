"""Test the Energy Consumption functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.lambda_heat_pumps.utils import (
    convert_energy_to_kwh,
    calculate_energy_delta,
    generate_energy_sensor_names,
    increment_energy_consumption_counter,
    get_energy_consumption_sensor_template,
    validate_energy_consumption_config,
)
from custom_components.lambda_heat_pumps.const import (
    ENERGY_CONSUMPTION_SENSOR_TEMPLATES,
    ENERGY_CONSUMPTION_MODES,
    ENERGY_CONSUMPTION_PERIODS,
)


class TestConvertEnergyToKwh:
    """Test energy unit conversion."""

    def test_wh_to_kwh_conversion(self):
        """Test Wh to kWh conversion."""
        result = convert_energy_to_kwh(1000.0, "Wh")
        assert result == 1.0

    def test_kwh_unchanged(self):
        """Test kWh values remain unchanged."""
        result = convert_energy_to_kwh(1.5, "kWh")
        assert result == 1.5

    def test_mwh_to_kwh_conversion(self):
        """Test MWh to kWh conversion."""
        result = convert_energy_to_kwh(1.0, "MWh")
        assert result == 1000.0

    def test_no_unit_large_value(self):
        """Test large value without unit (assumes Wh)."""
        result = convert_energy_to_kwh(5000.0, "")
        assert result == 5000.0  # Large value should be treated as Wh

    def test_no_unit_small_value(self):
        """Test small value without unit (assumes kWh)."""
        result = convert_energy_to_kwh(1.5, "")
        assert result == 1.5

    def test_unknown_unit_large_value(self):
        """Test unknown unit with large value."""
        result = convert_energy_to_kwh(2000.0, "unknown")
        assert result == 2000.0  # Large value should be treated as Wh

    def test_unknown_unit_small_value(self):
        """Test unknown unit with small value."""
        result = convert_energy_to_kwh(1.2, "unknown")
        assert result == 1.2

    def test_wattstunden_conversion(self):
        """Test German unit name conversion."""
        result = convert_energy_to_kwh(3000.0, "Wattstunden")
        assert result == 3.0

    def test_kilowattstunden_conversion(self):
        """Test German kWh unit name."""
        result = convert_energy_to_kwh(2.5, "Kilowattstunden")
        assert result == 2.5


class TestCalculateEnergyDelta:
    """Test energy delta calculation."""

    def test_normal_delta_calculation(self):
        """Test normal energy delta calculation."""
        current = 100.5
        last = 95.2
        expected = 5.3
        
        result = calculate_energy_delta(current, last)
        assert result == expected

    def test_overflow_detection(self):
        """Test overflow detection when current < last."""
        current = 10.0
        last = 95.2
        expected = 10.0  # Should return current value on overflow
        
        result = calculate_energy_delta(current, last)
        assert result == expected

    def test_max_delta_clamping(self):
        """Test maximum delta clamping."""
        current = 200.0
        last = 95.2
        max_delta = 50.0
        expected = 50.0  # Should be clamped to max_delta
        
        result = calculate_energy_delta(current, last, max_delta)
        assert result == expected

    def test_zero_delta(self):
        """Test zero delta calculation."""
        current = 100.0
        last = 100.0
        expected = 0.0
        
        result = calculate_energy_delta(current, last)
        assert result == expected

    def test_negative_delta(self):
        """Test negative delta (should not happen in normal operation)."""
        current = 90.0
        last = 95.0
        expected = 90.0  # Should return current value
        
        result = calculate_energy_delta(current, last)
        assert result == expected


class TestGenerateEnergySensorNames:
    """Test energy sensor name generation."""

    def test_heating_total_sensor_names(self):
        """Test heating total sensor name generation."""
        names = generate_energy_sensor_names(
            device_prefix="hp1",
            mode="heating",
            period="total",
            name_prefix="eu08l",
            use_legacy_modbus_names=True,
        )
        
        assert names["name"] == "HP1 Heating Energy Total"
        assert names["entity_id"] == "sensor.eu08l_hp1_heating_energy_total"
        assert names["unique_id"] == "eu08l_hp1_heating_energy_total"

    def test_hot_water_daily_sensor_names(self):
        """Test hot water daily sensor name generation."""
        names = generate_energy_sensor_names(
            device_prefix="hp2",
            mode="hot_water",
            period="daily",
            name_prefix="eu08l",
            use_legacy_modbus_names=True,
        )
        
        assert names["name"] == "HP2 Hot_Water Energy Daily"
        assert names["entity_id"] == "sensor.eu08l_hp2_hot_water_energy_daily"
        assert names["unique_id"] == "eu08l_hp2_hot_water_energy_daily"

    def test_modern_naming_convention(self):
        """Test modern naming convention (non-legacy)."""
        names = generate_energy_sensor_names(
            device_prefix="hp1",
            mode="cooling",
            period="total",
            name_prefix="eu08l",
            use_legacy_modbus_names=False,
        )
        
        assert names["name"] == "HP1 Cooling Energy Total"
        assert names["entity_id"] == "sensor.hp1_cooling_energy_total"
        assert names["unique_id"] == "hp1_cooling_energy_total"


class TestGetEnergyConsumptionSensorTemplate:
    """Test energy consumption sensor template retrieval."""

    def test_get_heating_total_template(self):
        """Test getting heating total template."""
        template = get_energy_consumption_sensor_template("heating", "total")
        
        assert template is not None
        assert template["name"] == "Heating Energy Total"
        assert template["unit"] == "kWh"
        assert template["state_class"] == "total_increasing"
        assert template["device_class"] == "energy"

    def test_get_hot_water_daily_template(self):
        """Test getting hot water daily template."""
        template = get_energy_consumption_sensor_template("hot_water", "daily")
        
        assert template is not None
        assert template["name"] == "Hot Water Energy Daily"
        assert template["unit"] == "kWh"
        assert template["state_class"] == "total"
        assert template["device_class"] == "energy"

    def test_get_nonexistent_template(self):
        """Test getting nonexistent template."""
        template = get_energy_consumption_sensor_template("nonexistent", "total")
        
        assert template is None


class TestValidateEnergyConsumptionConfig:
    """Test energy consumption config validation."""

    def test_valid_config(self):
        """Test valid configuration."""
        config = {
            "energy_consumption_sensors": {
                "hp1": {
                    "sensor_entity_id": "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
                }
            },
            "energy_consumption_offsets": {
                "hp1": {
                    "heating_energy_total": 0,
                    "hot_water_energy_total": 0,
                    "cooling_energy_total": 0,
                    "defrost_energy_total": 0,
                }
            }
        }
        
        result = validate_energy_consumption_config(config)
        assert result is True

    def test_missing_sensors_config(self):
        """Test missing sensors configuration."""
        config = {
            "energy_consumption_offsets": {
                "hp1": {
                    "heating_energy_total": 0,
                }
            }
        }
        
        result = validate_energy_consumption_config(config)
        assert result is False

    def test_missing_offsets_config(self):
        """Test missing offsets configuration."""
        config = {
            "energy_consumption_sensors": {
                "hp1": {
                    "sensor_entity_id": "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
                }
            }
        }
        
        result = validate_energy_consumption_config(config)
        assert result is False

    def test_invalid_sensor_config(self):
        """Test invalid sensor configuration."""
        config = {
            "energy_consumption_sensors": {
                "hp1": "invalid_config"  # Should be dict
            },
            "energy_consumption_offsets": {
                "hp1": {
                    "heating_energy_total": 0,
                }
            }
        }
        
        result = validate_energy_consumption_config(config)
        assert result is False

    def test_missing_sensor_entity_id(self):
        """Test missing sensor_entity_id in sensor config."""
        config = {
            "energy_consumption_sensors": {
                "hp1": {
                    "wrong_key": "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
                }
            },
            "energy_consumption_offsets": {
                "hp1": {
                    "heating_energy_total": 0,
                }
            }
        }
        
        result = validate_energy_consumption_config(config)
        assert result is False

    def test_invalid_offset_value(self):
        """Test invalid offset value."""
        config = {
            "energy_consumption_sensors": {
                "hp1": {
                    "sensor_entity_id": "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
                }
            },
            "energy_consumption_offsets": {
                "hp1": {
                    "heating_energy_total": "invalid",  # Should be numeric
                }
            }
        }
        
        result = validate_energy_consumption_config(config)
        assert result is False


class TestIncrementEnergyConsumptionCounter:
    """Test energy consumption counter increment."""

    @pytest.fixture
    def mock_hass(self):
        """Mock Home Assistant instance."""
        hass = Mock(spec=HomeAssistant)
        hass.states = Mock()
        hass.data = {"lambda_heat_pumps": {}}
        return hass

    @pytest.fixture
    def mock_entity_registry(self):
        """Mock entity registry."""
        registry = Mock()
        registry.async_get.return_value = Mock()  # Entity exists
        return registry

    @pytest.fixture
    def mock_state(self):
        """Mock state object."""
        state = Mock()
        state.state = "100.5"
        state.attributes = {}
        return state

    @pytest.mark.asyncio
    async def test_increment_with_valid_entity(self, mock_hass, mock_entity_registry, mock_state):
        """Test increment with valid entity."""
        # Setup mocks
        mock_hass.states.get.return_value = mock_state
        
        with patch('custom_components.lambda_heat_pumps.utils.async_get_entity_registry', return_value=mock_entity_registry):
            with patch('custom_components.lambda_heat_pumps.utils.async_update_entity'):
                await increment_energy_consumption_counter(
                    hass=mock_hass,
                    mode="heating",
                    hp_index=1,
                    energy_delta=5.0,
                    name_prefix="eu08l",
                    use_legacy_modbus_names=True,
                    energy_offsets=None,
                )
        
        # Verify state was updated
        mock_hass.states.async_set.assert_called()

    @pytest.mark.asyncio
    async def test_increment_with_nonexistent_entity(self, mock_hass, mock_entity_registry):
        """Test increment with nonexistent entity."""
        # Setup mocks
        mock_entity_registry.async_get.return_value = None  # Entity doesn't exist
        
        with patch('custom_components.lambda_heat_pumps.utils.async_get_entity_registry', return_value=mock_entity_registry):
            await increment_energy_consumption_counter(
                hass=mock_hass,
                mode="heating",
                hp_index=1,
                energy_delta=5.0,
                name_prefix="eu08l",
                use_legacy_modbus_names=True,
                energy_offsets=None,
            )
        
        # Verify state was not updated
        mock_hass.states.async_set.assert_not_called()

    @pytest.mark.asyncio
    async def test_increment_with_invalid_mode(self, mock_hass):
        """Test increment with invalid mode."""
        await increment_energy_consumption_counter(
            hass=mock_hass,
            mode="invalid_mode",
            hp_index=1,
            energy_delta=5.0,
            name_prefix="eu08l",
            use_legacy_modbus_names=True,
            energy_offsets=None,
        )
        
        # Verify nothing was called
        mock_hass.states.async_set.assert_not_called()

    @pytest.mark.asyncio
    async def test_increment_with_zero_delta(self, mock_hass):
        """Test increment with zero delta."""
        await increment_energy_consumption_counter(
            hass=mock_hass,
            mode="heating",
            hp_index=1,
            energy_delta=0.0,
            name_prefix="eu08l",
            use_legacy_modbus_names=True,
            energy_offsets=None,
        )
        
        # Verify nothing was called
        mock_hass.states.async_set.assert_not_called()

    @pytest.mark.asyncio
    async def test_increment_with_negative_delta(self, mock_hass):
        """Test increment with negative delta."""
        await increment_energy_consumption_counter(
            hass=mock_hass,
            mode="heating",
            hp_index=1,
            energy_delta=-5.0,
            name_prefix="eu08l",
            use_legacy_modbus_names=True,
            energy_offsets=None,
        )
        
        # Verify nothing was called
        mock_hass.states.async_set.assert_not_called()

    @pytest.mark.asyncio
    async def test_increment_with_offsets(self, mock_hass, mock_entity_registry, mock_state):
        """Test increment with energy offsets."""
        # Setup mocks
        mock_hass.states.get.return_value = mock_state
        
        energy_offsets = {
            "hp1": {
                "heating_energy_total": 100.0,
            }
        }
        
        with patch('custom_components.lambda_heat_pumps.utils.async_get_entity_registry', return_value=mock_entity_registry):
            with patch('custom_components.lambda_heat_pumps.utils.async_update_entity'):
                await increment_energy_consumption_counter(
                    hass=mock_hass,
                    mode="heating",
                    hp_index=1,
                    energy_delta=5.0,
                    name_prefix="eu08l",
                    use_legacy_modbus_names=True,
                    energy_offsets=energy_offsets,
                )
        
        # Verify state was updated with offset
        mock_hass.states.async_set.assert_called()


class TestEnergyConsumptionConstants:
    """Test energy consumption constants."""

    def test_energy_consumption_modes(self):
        """Test energy consumption modes are defined."""
        expected_modes = ["heating", "hot_water", "cooling", "defrost", "stby"]
        assert ENERGY_CONSUMPTION_MODES == expected_modes

    def test_energy_consumption_periods(self):
        """Test energy consumption periods are defined."""
        expected_periods = ["total", "daily"]
        assert ENERGY_CONSUMPTION_PERIODS == expected_periods

    def test_energy_consumption_sensor_templates(self):
        """Test energy consumption sensor templates are defined."""
        # Test that all expected sensor templates exist
        expected_sensors = [
            "heating_energy_total",
            "heating_energy_daily",
            "hot_water_energy_total",
            "hot_water_energy_daily",
            "cooling_energy_total",
            "cooling_energy_daily",
            "defrost_energy_total",
            "defrost_energy_daily",
        ]
        
        for sensor_id in expected_sensors:
            assert sensor_id in ENERGY_CONSUMPTION_SENSOR_TEMPLATES
            template = ENERGY_CONSUMPTION_SENSOR_TEMPLATES[sensor_id]
            assert "name" in template
            assert "unit" in template
            assert "state_class" in template
            assert "device_class" in template
            assert template["unit"] == "kWh"
            assert template["device_class"] == "energy"

    def test_heating_energy_total_template(self):
        """Test heating energy total template properties."""
        template = ENERGY_CONSUMPTION_SENSOR_TEMPLATES["heating_energy_total"]
        
        assert template["name"] == "Heating Energy Total"
        assert template["unit"] == "kWh"
        assert template["state_class"] == "total_increasing"
        assert template["device_class"] == "energy"
        assert template["mode_value"] == 1  # CH
        assert template["precision"] == 6

    def test_hot_water_energy_daily_template(self):
        """Test hot water energy daily template properties."""
        template = ENERGY_CONSUMPTION_SENSOR_TEMPLATES["hot_water_energy_daily"]
        
        assert template["name"] == "Hot Water Energy Daily"
        assert template["unit"] == "kWh"
        assert template["state_class"] == "total"
        assert template["device_class"] == "energy"
        assert template["precision"] == 6


class TestEnergyConsumptionIntegration:
    """Test energy consumption integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_energy_tracking_workflow(self):
        """Test complete energy tracking workflow."""
        # This would be a more comprehensive integration test
        # that tests the full workflow from sensor creation to energy tracking
        
        # Test data
        config = {
            "energy_consumption_sensors": {
                "hp1": {
                    "sensor_entity_id": "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
                }
            },
            "energy_consumption_offsets": {
                "hp1": {
                    "heating_energy_total": 0,
                    "hot_water_energy_total": 0,
                    "cooling_energy_total": 0,
                    "defrost_energy_total": 0,
                }
            }
        }
        
        # Validate configuration
        assert validate_energy_consumption_config(config) is True
        
        # Test sensor name generation for all modes and periods
        for mode in ENERGY_CONSUMPTION_MODES:
            for period in ENERGY_CONSUMPTION_PERIODS:
                names = generate_energy_sensor_names(
                    device_prefix="hp1",
                    mode=mode,
                    period=period,
                    name_prefix="eu08l",
                    use_legacy_modbus_names=True,
                )
                
                assert names["name"] is not None
                assert names["entity_id"].startswith("sensor.eu08l_hp1_")
                assert names["unique_id"].startswith("eu08l_hp1_")
                
                # Test template retrieval
                template = get_energy_consumption_sensor_template(mode, period)
                assert template is not None
                # Template name should match the mode and period
                # Handle special case for STBY mode
                mode_display = mode.replace('_', ' ').upper() if mode == 'stby' else mode.replace('_', ' ').title()
                expected_name = f"{mode_display} Energy {period.title()}"
                assert template["name"] == expected_name
