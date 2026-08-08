"""Test the Energy Consumption functionality."""

import inspect
import pytest
from unittest.mock import Mock, AsyncMock, patch
from types import SimpleNamespace
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.lambda_heat_pumps.utils import (
    convert_energy_to_kwh,
    calculate_energy_delta,
    generate_energy_sensor_names,
    generate_sensor_names,
    increment_energy_consumption_counter,
    get_energy_consumption_sensor_template,
    validate_energy_consumption_config,
)
from custom_components.lambda_heat_pumps.const import (
    ENERGY_CONSUMPTION_SENSOR_TEMPLATES,
    ENERGY_CONSUMPTION_MODES,
    ENERGY_CONSUMPTION_PERIODS,
    MAX_ENERGY_DELTA_WH,
)
from tests.conftest import DummyLoop


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
        """Test normal energy delta calculation (below the default max_delta)."""
        current = 100.5
        last = 99.2
        expected = 1.3

        result = calculate_energy_delta(current, last)
        assert result == expected

    def test_overflow_detection(self):
        """Test overflow detection when current < last."""
        current = 10.0
        last = 95.2
        expected = 10.0  # Should return current value on overflow
        
        result = calculate_energy_delta(current, last)
        assert result == expected

    def test_max_delta_exceeded_returns_none(self):
        """Implausible delta must be discarded (None), not clamped."""
        current = 200.0
        last = 95.2
        max_delta = 50.0

        result = calculate_energy_delta(current, last, max_delta)
        assert result is None

    def test_default_max_delta_sourced_from_const(self):
        """The default max_delta must come from MAX_ENERGY_DELTA_WH (const_base.py),
        not a second hardcoded literal - single source of truth (5000 Wh = 5.0 kWh)."""
        assert MAX_ENERGY_DELTA_WH == 5000

        default_max_delta = inspect.signature(calculate_energy_delta).parameters["max_delta"].default
        assert default_max_delta == MAX_ENERGY_DELTA_WH / 1000

        # Just below the threshold -> normal delta
        current = 100.0 + default_max_delta - 0.1
        result = calculate_energy_delta(current, 100.0)
        assert result == pytest.approx(default_max_delta - 0.1)

        # Just above the threshold -> implausible, discarded
        current = 100.0 + default_max_delta + 0.1
        result = calculate_energy_delta(current, 100.0)
        assert result is None

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
        
        assert names["name"] == "Heating Energy Total"
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
        
        assert names["name"] == "Hot_Water Energy Daily"
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
        
        assert names["name"] == "Cooling Energy Total"
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
        hass.config = Mock()
        hass.config.language = "en"
        hass.config.locale = SimpleNamespace(language="en")
        hass.loop = DummyLoop()
        return hass

    @pytest.fixture
    def mock_entity_registry(self):
        """Mock entity registry."""
        registry = Mock()
        registry.async_get.return_value = Mock()  # Entity exists
        # unique_id-Lookup soll hier "nicht gefunden" simulieren, damit auf die
        # text-rekonstruierte entity_id zurueckgefallen wird (siehe generate_sensor_names
        # in den Tests unten, die energy_entities exakt darueber schluesseln).
        registry.async_get_entity_id.return_value = None
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
        """Test increment with valid entity (Entity in hass.data → set_energy_value wird aufgerufen)."""
        mock_hass.states.get.return_value = mock_state

        # Energy-Entities registrieren, damit Coordinator sie findet (kein Fallback async_set)
        energy_entities = {}
        for period in ["total", "daily", "monthly", "yearly", "2h", "4h"]:
            names = generate_sensor_names(
                "hp1", f"Heating Energy {period.title()}", f"heating_energy_{period}",
                "eu08l", True,
            )
            mock_ent = Mock()
            mock_ent._energy_value = 100.5
            mock_ent.set_energy_value = Mock()
            energy_entities[names["unique_id"]] = mock_ent
        mock_hass.data["lambda_heat_pumps"] = {"test_entry_id": {"energy_entities": energy_entities}}

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

        # Entity wurde per set_energy_value aktualisiert (kein async_set-Fallback)
        assert any(ent.set_energy_value.called for ent in energy_entities.values())

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
        """Test increment with energy offsets (Entity in hass.data → set_energy_value)."""
        mock_hass.states.get.return_value = mock_state

        energy_entities = {}
        for period in ["total", "daily", "monthly", "yearly", "2h", "4h"]:
            names = generate_sensor_names(
                "hp1", f"Heating Energy {period.title()}", f"heating_energy_{period}",
                "eu08l", True,
            )
            mock_ent = Mock()
            mock_ent._energy_value = 100.5
            mock_ent._applied_offset = 0.0
            mock_ent.set_energy_value = Mock()
            energy_entities[names["unique_id"]] = mock_ent
        mock_hass.data["lambda_heat_pumps"] = {"test_entry_id": {"energy_entities": energy_entities}}

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

        # Entity wurde per set_energy_value aktualisiert (Offset nur für Total)
        assert any(ent.set_energy_value.called for ent in energy_entities.values())


class TestIncrementEnergyConsumptionCounterUniqueIdLookupIssue107:
    """Regression tests for Issue #107: increment_energy_consumption_counter() must
    resolve its target entity via unique_id in the entity registry instead of
    trusting the text-reconstructed entity_id from generate_sensor_names(). Before
    this fix, any mismatch between the two (e.g. a device name with a special
    character, or a manually renamed entity) caused the increment to be silently
    skipped.
    """

    @pytest.fixture
    def mock_hass(self):
        hass = Mock(spec=HomeAssistant)
        hass.states = Mock()
        hass.data = {"lambda_heat_pumps": {}}
        hass.config = Mock()
        hass.config.language = "en"
        hass.config.locale = SimpleNamespace(language="en")
        hass.loop = DummyLoop()
        return hass

    @pytest.mark.asyncio
    async def test_uses_registry_resolved_entity_id_not_reconstructed_text(self, mock_hass):
        """The real, registered entity_id may differ from the text generate_sensor_names()
        would construct (e.g. because it was created before a naming change, or the user
        renamed it). The registry-resolved entity_id must win.
        """
        # generate_sensor_names() would construct this from name_prefix/device_prefix/sensor_id...
        reconstructed_entity_id = "sensor.eu08l_hp1_heating_energy_total"
        # ...but the entity actually registered under that unique_id has a different id.
        # unique_id never changes though - energy_entities is keyed by it (see sensor.py),
        # so the in-memory entity lookup is immune to this mismatch by construction.
        real_entity_id = "sensor.custom_renamed_heating_energy_total"
        stable_unique_id = "eu08l_hp1_heating_energy_total"

        state_obj = Mock()
        state_obj.state = "100.5"
        state_obj.attributes = {}
        mock_hass.states.get = Mock(return_value=state_obj)

        fake_entity = Mock()
        fake_entity._energy_value = 100.5
        fake_entity.set_energy_value = Mock()
        mock_hass.data["lambda_heat_pumps"] = {
            "test_entry_id": {"energy_entities": {stable_unique_id: fake_entity}}
        }

        mock_registry = Mock()
        mock_registry.async_get = Mock(return_value=Mock())

        def fake_async_get_entity_id(domain, platform, unique_id):
            # Only the "total" sensor's unique_id resolves; others fall back (kept simple).
            if unique_id.endswith("heating_energy_total"):
                return real_entity_id
            return None

        mock_registry.async_get_entity_id = Mock(side_effect=fake_async_get_entity_id)

        with patch(
            "custom_components.lambda_heat_pumps.utils.async_get_entity_registry",
            return_value=mock_registry,
        ), patch(
            "custom_components.lambda_heat_pumps.utils.async_update_entity",
            new_callable=AsyncMock,
        ):
            await increment_energy_consumption_counter(
                hass=mock_hass,
                mode="heating",
                hp_index=1,
                energy_delta=5.0,
                name_prefix="eu08l",
                use_legacy_modbus_names=True,
                energy_offsets=None,
            )

        fake_entity.set_energy_value.assert_called_once()
        assert abs(fake_entity.set_energy_value.call_args[0][0] - 105.5) < 0.001, (
            "Expected the entity found via unique_id (100.5 + 5.0 delta) to be updated, "
            "not silently skipped because its entity_id doesn't match the reconstructed text."
        )

    @pytest.mark.asyncio
    async def test_falls_back_to_reconstructed_entity_id_when_not_yet_in_registry(self, mock_hass):
        """Self-healing fallback: if the unique_id lookup finds nothing (e.g. first
        cycle right after startup), the previous text-based construction is used.
        """
        reconstructed_entity_id = "sensor.eu08l_hp1_heating_energy_total"
        stable_unique_id = "eu08l_hp1_heating_energy_total"

        state_obj = Mock()
        state_obj.state = "100.5"
        state_obj.attributes = {}
        mock_hass.states.get = Mock(return_value=state_obj)

        fake_entity = Mock()
        fake_entity._energy_value = 100.5
        fake_entity.set_energy_value = Mock()
        mock_hass.data["lambda_heat_pumps"] = {
            "test_entry_id": {"energy_entities": {stable_unique_id: fake_entity}}
        }

        mock_registry = Mock()
        mock_registry.async_get = Mock(return_value=Mock())
        mock_registry.async_get_entity_id = Mock(return_value=None)  # not in registry yet

        with patch(
            "custom_components.lambda_heat_pumps.utils.async_get_entity_registry",
            return_value=mock_registry,
        ), patch(
            "custom_components.lambda_heat_pumps.utils.async_update_entity",
            new_callable=AsyncMock,
        ):
            await increment_energy_consumption_counter(
                hass=mock_hass,
                mode="heating",
                hp_index=1,
                energy_delta=5.0,
                name_prefix="eu08l",
                use_legacy_modbus_names=True,
                energy_offsets=None,
            )

        fake_entity.set_energy_value.assert_called_once()
        assert abs(fake_entity.set_energy_value.call_args[0][0] - 105.5) < 0.001


class TestEnergyConsumptionConstants:
    """Test energy consumption constants."""

    def test_energy_consumption_modes(self):
        """Test energy consumption modes are defined."""
        expected_modes = ["cooling", "defrost", "heating", "hot_water", "stby"]
        assert sorted(ENERGY_CONSUMPTION_MODES) == expected_modes

    def test_energy_consumption_periods(self):
        """Test energy consumption periods are defined."""
        expected_periods = ["daily", "hourly", "monthly", "total", "yearly"]
        assert sorted(ENERGY_CONSUMPTION_PERIODS) == expected_periods

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
                # Test template retrieval — some mode/period combinations have no template
                template = get_energy_consumption_sensor_template(mode, period)
                if template is None:
                    # e.g. stby/hourly, cooling/hourly — skip combinations without a template
                    continue

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

                # Template name should match the mode and period
                # Handle special case for STBY mode
                mode_display = mode.replace('_', ' ').upper() if mode == 'stby' else mode.replace('_', ' ').title()
                expected_name = f"{mode_display} Energy {period.title()}"
                assert template["name"] == expected_name
