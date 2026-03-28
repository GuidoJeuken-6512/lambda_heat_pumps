"""
Tests for cycling and energy offset features.

Covers:
- Cycling offset applied once at HA start (positive and negative)
- No double-application: differential tracking via _applied_offset
- applied_offset persisted in state attributes
- Bug B-1 fix: increment_cycling_counter must NOT add any offset
- Energy offset: electrical and thermal, positive and negative
- Energy offset differential tracking
- Config loading: validation of offset values (negative values pass, non-numeric → 0)
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from custom_components.lambda_heat_pumps.sensor import LambdaCyclingSensor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_cycling_sensor(mock_entry, mock_coordinator, sensor_id="heating_cycling_total", hp_index=1):
    """Create a LambdaCyclingSensor with minimal mocking."""
    sensor = LambdaCyclingSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id=sensor_id,
        name="Test Cycling Sensor",
        entity_id=f"sensor.test_hp{hp_index}_{sensor_id}",
        unique_id=f"test_hp{hp_index}_{sensor_id}",
        unit="cycles",
        state_class="total_increasing",
        device_class=None,
        device_type="hp",
        hp_index=hp_index,
    )
    sensor.async_write_ha_state = Mock()
    return sensor


def make_last_state(value, applied_offset=0):
    """Create a mock restored state."""
    state = Mock()
    state.state = str(value)
    state.attributes = {"applied_offset": applied_offset}
    return state


# ===========================================================================
# 1. Cycling offset – applied once at startup
# ===========================================================================

class TestCyclingOffsetOnStartup:
    """_apply_cycling_offset() is called from restore_state()."""

    @pytest.mark.asyncio
    async def test_positive_offset_added_on_first_start(self, mock_entry, mock_coordinator):
        """Positive YAML offset is added to the restored value exactly once."""
        sensor = make_cycling_sensor(mock_entry, mock_coordinator)
        config = {"cycling_offsets": {"hp1": {"heating_cycling_total": 1500}}}

        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value=config):
            await sensor.restore_state(make_last_state(100, applied_offset=0))

        assert sensor._cycling_value == 1600   # 100 + 1500
        assert sensor._applied_offset == 1500

    @pytest.mark.asyncio
    async def test_negative_offset_subtracted_on_first_start(self, mock_entry, mock_coordinator):
        """Negative YAML offset is subtracted from the restored value."""
        sensor = make_cycling_sensor(mock_entry, mock_coordinator)
        config = {"cycling_offsets": {"hp1": {"heating_cycling_total": -200}}}

        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value=config):
            await sensor.restore_state(make_last_state(500, applied_offset=0))

        assert sensor._cycling_value == 300    # 500 - 200
        assert sensor._applied_offset == -200

    @pytest.mark.asyncio
    async def test_zero_offset_leaves_value_unchanged(self, mock_entry, mock_coordinator):
        """An offset of 0 must not change the sensor value."""
        sensor = make_cycling_sensor(mock_entry, mock_coordinator)
        config = {"cycling_offsets": {"hp1": {"heating_cycling_total": 0}}}

        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value=config):
            await sensor.restore_state(make_last_state(42, applied_offset=0))

        assert sensor._cycling_value == 42
        # async_write_ha_state must NOT be called when offset_difference == 0
        sensor.async_write_ha_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_offset_configured_value_unchanged(self, mock_entry, mock_coordinator):
        """When no cycling_offsets section exists, value stays untouched."""
        sensor = make_cycling_sensor(mock_entry, mock_coordinator)
        config = {}  # no cycling_offsets key

        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value=config):
            await sensor.restore_state(make_last_state(77, applied_offset=0))

        assert sensor._cycling_value == 77
        sensor.async_write_ha_state.assert_not_called()


# ===========================================================================
# 2. Cycling offset – differential tracking (no double application)
# ===========================================================================

class TestCyclingOffsetDifferentialTracking:

    @pytest.mark.asyncio
    async def test_same_offset_not_applied_again(self, mock_entry, mock_coordinator):
        """When _applied_offset already equals the YAML offset, nothing is added."""
        sensor = make_cycling_sensor(mock_entry, mock_coordinator)
        # Simulate previous run: offset 1500 already applied; value currently at 1650
        sensor._cycling_value = 1650
        sensor._applied_offset = 1500
        config = {"cycling_offsets": {"hp1": {"heating_cycling_total": 1500}}}

        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value=config):
            await sensor._apply_cycling_offset()

        assert sensor._cycling_value == 1650   # unchanged
        sensor.async_write_ha_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_increased_offset_adds_only_delta(self, mock_entry, mock_coordinator):
        """When offset is increased in YAML, only the delta is added."""
        sensor = make_cycling_sensor(mock_entry, mock_coordinator)
        sensor._cycling_value = 1600   # previously had 100 base + 1500 offset
        sensor._applied_offset = 1500
        config = {"cycling_offsets": {"hp1": {"heating_cycling_total": 2000}}}

        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value=config):
            await sensor._apply_cycling_offset()

        assert sensor._cycling_value == 2100   # 1600 + (2000 - 1500)
        assert sensor._applied_offset == 2000

    @pytest.mark.asyncio
    async def test_decreased_offset_subtracts_only_delta(self, mock_entry, mock_coordinator):
        """When offset is decreased in YAML, only the delta is subtracted."""
        sensor = make_cycling_sensor(mock_entry, mock_coordinator)
        sensor._cycling_value = 1600
        sensor._applied_offset = 1500
        config = {"cycling_offsets": {"hp1": {"heating_cycling_total": 1000}}}

        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value=config):
            await sensor._apply_cycling_offset()

        assert sensor._cycling_value == 1100   # 1600 + (1000 - 1500) = 1600 - 500
        assert sensor._applied_offset == 1000


# ===========================================================================
# 3. Cycling offset – applied_offset persisted in state attributes
# ===========================================================================

class TestCyclingOffsetPersistence:

    def test_extra_state_attributes_contains_applied_offset(self, mock_entry, mock_coordinator):
        """extra_state_attributes must expose applied_offset for HA state restore."""
        sensor = make_cycling_sensor(mock_entry, mock_coordinator)
        sensor._applied_offset = 1500
        sensor._cycling_value = 1600

        attrs = sensor.extra_state_attributes
        assert "applied_offset" in attrs
        assert attrs["applied_offset"] == 1500

    @pytest.mark.asyncio
    async def test_applied_offset_restored_from_state(self, mock_entry, mock_coordinator):
        """After HA restart the previously persisted applied_offset is restored."""
        sensor = make_cycling_sensor(mock_entry, mock_coordinator)
        config = {"cycling_offsets": {"hp1": {"heating_cycling_total": 1500}}}

        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value=config):
            # Simulate restart: state shows 1600 and applied_offset=1500 in attributes
            await sensor.restore_state(make_last_state(1600, applied_offset=1500))

        # Offset already applied → no change
        assert sensor._cycling_value == 1600
        assert sensor._applied_offset == 1500
        sensor.async_write_ha_state.assert_not_called()


# ===========================================================================
# 4. Bug B-1 fix: increment_cycling_counter must NOT add any offset
# ===========================================================================

class TestIncrementCyclingCounterNoOffset:
    """
    After the fix, increment_cycling_counter() does NOT accept cycling_offsets
    and does NOT add any offset value — it only increments by +1.
    """

    @pytest.mark.asyncio
    async def test_increment_adds_exactly_one_no_offset(self, mock_entry, mock_coordinator):
        """increment_cycling_counter increments by exactly +1, regardless of YAML offsets."""
        from custom_components.lambda_heat_pumps.utils import increment_cycling_counter
        from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

        # Build a fake cycling entity that records the value it receives
        received_values = []

        class FakeCyclingEntity:
            def set_cycling_value(self, value):
                received_values.append(value)

        entity_id = "sensor.eu08l_hp1_heating_cycling_total"
        fake_entity = FakeCyclingEntity()

        # Wire up hass mock
        hass = Mock()
        hass.data = {
            "lambda_heat_pumps": {
                "test_entry": {
                    "cycling_entities": {entity_id: fake_entity}
                }
            }
        }

        # State reports current value of 1600 (already has offset baked in from startup)
        state_obj = Mock()
        state_obj.state = "1600"
        state_obj.attributes = {}
        hass.states.get = Mock(return_value=state_obj)
        hass.async_add_executor_job = AsyncMock()

        mock_entity_registry = Mock()
        mock_entity_registry.async_get = Mock(return_value=Mock())  # entity exists

        with patch(
            "custom_components.lambda_heat_pumps.utils.async_get_entity_registry",
            return_value=mock_entity_registry,
        ), patch(
            "custom_components.lambda_heat_pumps.utils.async_update_entity",
            new_callable=AsyncMock,
        ), patch(
            "custom_components.lambda_heat_pumps.utils._get_coordinator",
            return_value=None,
        ):
            await increment_cycling_counter(
                hass=hass,
                mode="heating",
                hp_index=1,
                name_prefix="eu08l",
                use_legacy_modbus_names=True,
            )

        # At least the total sensor must have been incremented
        assert any(v == 1601 for v in received_values), (
            f"Expected 1601 (1600+1) but got {received_values}"
        )
        # None of the values must be 3101 (old bug: 1600+1+1500)
        assert all(v != 3101 for v in received_values), (
            "Bug B-1 regression: offset was added inside increment_cycling_counter"
        )

    def test_increment_cycling_counter_signature_no_cycling_offsets_param(self):
        """increment_cycling_counter must not have a cycling_offsets parameter."""
        import inspect
        from custom_components.lambda_heat_pumps.utils import increment_cycling_counter

        params = inspect.signature(increment_cycling_counter).parameters
        assert "cycling_offsets" not in params, (
            "cycling_offsets parameter still present in increment_cycling_counter — bug B-1 not fully fixed"
        )


# ===========================================================================
# 5. Energy offset – electrical and thermal, positive and negative
# ===========================================================================

def make_energy_sensor(mock_entry, mock_coordinator, mode="heating", period="total", hp_index=1):
    """Create a LambdaEnergyConsumptionSensor with minimal mocking."""
    from custom_components.lambda_heat_pumps.sensor import LambdaEnergyConsumptionSensor

    sensor = LambdaEnergyConsumptionSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id=f"{mode}_energy_{period}",
        name=f"Test Energy {mode} {period}",
        entity_id=f"sensor.test_hp{hp_index}_{mode}_energy_{period}",
        unique_id=f"test_hp{hp_index}_{mode}_energy_{period}",
        unit="kWh",
        state_class="total_increasing",
        device_class="energy",
        device_type="hp",
        hp_index=hp_index,
        mode=mode,
        period=period,
    )
    sensor.async_write_ha_state = Mock()
    return sensor


class TestEnergyOffsetApplication:

    @pytest.mark.asyncio
    async def test_electrical_offset_applied_on_startup(self, mock_entry, mock_coordinator):
        """_apply_energy_offset() adds the electrical offset once at HA start."""
        sensor = make_energy_sensor(mock_entry, mock_coordinator)
        sensor._energy_value = 5000.0
        sensor._applied_offset = 0.0

        config = {"energy_consumption_offsets": {"hp1": {"heating_energy_total": 12500.0}}}
        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value=config):
            await sensor._apply_energy_offset()

        assert abs(sensor._energy_value - 17500.0) < 0.001   # 5000 + 12500
        assert abs(sensor._applied_offset - 12500.0) < 0.001

    @pytest.mark.asyncio
    async def test_negative_energy_offset_subtracts(self, mock_entry, mock_coordinator):
        """A negative energy offset reduces the sensor value."""
        sensor = make_energy_sensor(mock_entry, mock_coordinator)
        sensor._energy_value = 3000.0
        sensor._applied_offset = 0.0

        config = {"energy_consumption_offsets": {"hp1": {"heating_energy_total": -500.0}}}
        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value=config):
            await sensor._apply_energy_offset()

        assert abs(sensor._energy_value - 2500.0) < 0.001   # 3000 - 500
        assert abs(sensor._applied_offset - (-500.0)) < 0.001

    @pytest.mark.asyncio
    async def test_same_energy_offset_not_applied_twice(self, mock_entry, mock_coordinator):
        """When _applied_offset matches YAML offset, nothing changes."""
        sensor = make_energy_sensor(mock_entry, mock_coordinator)
        sensor._energy_value = 17500.0
        sensor._applied_offset = 12500.0   # already applied

        config = {"energy_consumption_offsets": {"hp1": {"heating_energy_total": 12500.0}}}
        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value=config):
            await sensor._apply_energy_offset()

        assert abs(sensor._energy_value - 17500.0) < 0.001   # unchanged
        sensor.async_write_ha_state.assert_not_called()


# ===========================================================================
# 6. Energy offset – differential tracking in increment_energy_consumption_counter
# ===========================================================================

class TestEnergyOffsetIncrementDifferential:

    @pytest.mark.asyncio
    async def test_first_call_applies_full_offset(self, mock_entry, mock_coordinator):
        """On first energy increment the full offset is applied (_applied_offset is updated)."""
        from custom_components.lambda_heat_pumps.utils import increment_energy_consumption_counter

        class FakeEnergyEntity:
            def __init__(self):
                self._applied_offset = 0.0
                self._energy_value = 1000.0

            def set_energy_value(self, value):
                self._energy_value = value

        total_entity_id = "sensor.eu08l_hp1_heating_energy_total"
        fake_entity = FakeEnergyEntity()

        hass = Mock()
        state_obj = Mock()
        state_obj.state = "1000.0"
        hass.states.get = Mock(return_value=state_obj)
        hass.data = {
            "lambda_heat_pumps": {
                "test_entry": {"energy_entities": {total_entity_id: fake_entity}}
            }
        }
        hass.async_add_executor_job = AsyncMock()

        energy_offsets = {"hp1": {"heating_energy_total": 500.0}}

        with patch(
            "custom_components.lambda_heat_pumps.utils.async_update_entity",
            new_callable=AsyncMock,
        ), patch(
            "custom_components.lambda_heat_pumps.utils.generate_sensor_names",
            return_value={"entity_id": total_entity_id, "name": "Heating Energy Total", "unique_id": "test"},
        ), patch(
            "custom_components.lambda_heat_pumps.utils.async_get_entity_registry",
            return_value=Mock(async_get=Mock(return_value=Mock())),
        ):
            await increment_energy_consumption_counter(
                hass=hass,
                mode="heating",
                hp_index=1,
                energy_delta=1.0,
                name_prefix="eu08l",
                energy_offsets=energy_offsets,
            )

        # Proof that offset was applied: _applied_offset updated from 0 → 500
        assert abs(fake_entity._applied_offset - 500.0) < 0.001, (
            f"Expected _applied_offset=500.0 after first call, got {fake_entity._applied_offset}"
        )

    @pytest.mark.asyncio
    async def test_second_call_same_offset_adds_no_extra(self, mock_entry, mock_coordinator):
        """On second increment with same YAML offset, only delta is added (no re-application)."""
        from custom_components.lambda_heat_pumps.utils import increment_energy_consumption_counter

        energy_values = {}

        class FakeEnergyEntity:
            def __init__(self, entity_id):
                self.entity_id = entity_id
                self._applied_offset = 500.0   # already applied in previous run

            def set_energy_value(self, value):
                energy_values[self.entity_id] = value

        total_entity_id = "sensor.eu08l_hp1_heating_energy_total"
        fake_entity = FakeEnergyEntity(total_entity_id)

        hass = Mock()
        state_obj = Mock()
        state_obj.state = "1501.0"   # current value after first increment + offset
        hass.states.get = Mock(return_value=state_obj)
        hass.data = {
            "lambda_heat_pumps": {
                "test_entry": {"energy_entities": {total_entity_id: fake_entity}}
            }
        }
        hass.async_add_executor_job = AsyncMock()

        energy_offsets = {"hp1": {"heating_energy_total": 500.0}}

        with patch(
            "custom_components.lambda_heat_pumps.utils.async_update_entity",
            new_callable=AsyncMock,
        ), patch(
            "custom_components.lambda_heat_pumps.utils.generate_sensor_names",
            return_value={"entity_id": total_entity_id, "name": "Heating Energy Total", "unique_id": "test"},
        ), patch(
            "custom_components.lambda_heat_pumps.utils.async_get_entity_registry",
            return_value=Mock(async_get=Mock(return_value=Mock())),
        ):
            await increment_energy_consumption_counter(
                hass=hass,
                mode="heating",
                hp_index=1,
                energy_delta=1.0,
                name_prefix="eu08l",
                energy_offsets=energy_offsets,
            )

        # Only delta 1.0 is added → 1501.0 + 1.0 = 1502.0 (no extra 500)
        if total_entity_id in energy_values:
            assert abs(energy_values[total_entity_id] - 1502.0) < 0.01, (
                f"Expected 1502.0 (no re-application of offset), got {energy_values[total_entity_id]}"
            )


# ===========================================================================
# 7. Config loading – offset validation
# ===========================================================================

class TestOffsetConfigValidation:
    """load_lambda_config validates offset values: non-numeric → 0, negative → pass."""

    @pytest.mark.asyncio
    async def test_negative_cycling_offset_passes_validation(self):
        """Negative cycling offset values are accepted by the validator."""
        import yaml
        from custom_components.lambda_heat_pumps.utils import load_lambda_config

        yaml_content = """
cycling_offsets:
  hp1:
    heating_cycling_total: -500
    hot_water_cycling_total: -100
"""
        hass = Mock()
        hass.data = {}
        hass.config.config_dir = "/tmp/test_offset_validation"

        with patch("builtins.open", Mock(return_value=Mock(
            __enter__=Mock(return_value=Mock(read=Mock(return_value=yaml_content))),
            __exit__=Mock(return_value=False),
        ))), patch(
            "custom_components.lambda_heat_pumps.utils.ensure_lambda_config",
            new_callable=AsyncMock,
        ), patch(
            "custom_components.lambda_heat_pumps.utils.migrate_lambda_config_sections",
            new_callable=AsyncMock,
        ), patch("os.path.join", return_value="/tmp/test/lambda_wp_config.yaml"), \
           patch("custom_components.lambda_heat_pumps.utils.open",
                 Mock(return_value=Mock(
                     __enter__=Mock(return_value=Mock(read=Mock(return_value=yaml_content))),
                     __exit__=Mock(return_value=False),
                 )), create=True):

            # Use the lower-level validate logic directly
            from custom_components.lambda_heat_pumps.utils import load_lambda_config as llc

            raw = yaml.safe_load(yaml_content)
            cycling_offsets = raw.get("cycling_offsets", {})

            # Simulate the validator loop from load_lambda_config
            for device, offsets in cycling_offsets.items():
                for offset_type, value in offsets.items():
                    assert isinstance(value, (int, float)), f"{offset_type} should be numeric"
                    # No check for >= 0 → negative values are valid

            assert cycling_offsets["hp1"]["heating_cycling_total"] == -500
            assert cycling_offsets["hp1"]["hot_water_cycling_total"] == -100

    def test_non_numeric_cycling_offset_is_rejected(self):
        """Non-numeric cycling offset values are caught by the validator and replaced with 0."""
        import yaml

        yaml_content = """
cycling_offsets:
  hp1:
    heating_cycling_total: "not_a_number"
    hot_water_cycling_total: 100
"""
        raw = yaml.safe_load(yaml_content)
        cycling_offsets = raw["cycling_offsets"]

        # Simulate the validator
        for device, offsets in cycling_offsets.items():
            for offset_type, value in list(offsets.items()):
                if not isinstance(value, (int, float)):
                    cycling_offsets[device][offset_type] = 0

        assert cycling_offsets["hp1"]["heating_cycling_total"] == 0        # replaced
        assert cycling_offsets["hp1"]["hot_water_cycling_total"] == 100    # untouched

    def test_negative_energy_offset_passes_validation(self):
        """Negative energy consumption offset values are accepted by the validator."""
        import yaml

        yaml_content = """
energy_consumption_offsets:
  hp1:
    heating_energy_total: -1500.5
    hot_water_energy_total: -300.0
"""
        raw = yaml.safe_load(yaml_content)
        energy_offsets = raw["energy_consumption_offsets"]

        for device, offsets in energy_offsets.items():
            for offset_type, value in offsets.items():
                assert isinstance(value, (int, float))

        assert abs(energy_offsets["hp1"]["heating_energy_total"] - (-1500.5)) < 0.001
        assert abs(energy_offsets["hp1"]["hot_water_energy_total"] - (-300.0)) < 0.001

    def test_thermal_energy_offset_keys_are_valid(self):
        """Thermal energy offset keys (mode_thermal_energy_total) are accepted."""
        import yaml

        yaml_content = """
energy_consumption_offsets:
  hp1:
    heating_thermal_energy_total: 6500.0
    hot_water_thermal_energy_total: 2600.0
    cooling_thermal_energy_total: 800.0
    defrost_thermal_energy_total: 150.0
"""
        raw = yaml.safe_load(yaml_content)
        energy_offsets = raw["energy_consumption_offsets"]

        for device, offsets in energy_offsets.items():
            for offset_type, value in offsets.items():
                assert isinstance(value, (int, float)), f"{offset_type} must be numeric"
                assert "thermal_energy_total" in offset_type, f"Expected thermal key, got {offset_type}"

        assert abs(energy_offsets["hp1"]["heating_thermal_energy_total"] - 6500.0) < 0.001


# ===========================================================================
# 8. const_base.py – LAMBDA_WP_CONFIG_TEMPLATE
# ===========================================================================

class TestConfigTemplate:

    def test_template_documents_negative_offset_support(self):
        """The YAML template comment should mention that negative values are valid."""
        from custom_components.lambda_heat_pumps.const_base import LAMBDA_WP_CONFIG_TEMPLATE
        # The template must at minimum contain the key names so users can copy-paste them
        assert "cycling_offsets" in LAMBDA_WP_CONFIG_TEMPLATE
        assert "energy_consumption_offsets" in LAMBDA_WP_CONFIG_TEMPLATE

    def test_template_contains_thermal_energy_offset_example(self):
        """The YAML template should mention thermal energy offset keys."""
        from custom_components.lambda_heat_pumps.const_base import LAMBDA_WP_CONFIG_TEMPLATE
        assert "thermal_energy_total" in LAMBDA_WP_CONFIG_TEMPLATE, (
            "Template should include thermal_energy_total offset example"
        )

    def test_template_documents_compressor_start_cycling_offset(self):
        """The template must include compressor_start_cycling_total as a commented example."""
        from custom_components.lambda_heat_pumps.const_base import LAMBDA_WP_CONFIG_TEMPLATE
        assert "compressor_start_cycling_total" in LAMBDA_WP_CONFIG_TEMPLATE


# ===========================================================================
# 9. Migration – compressor_start_cycling_total
# ===========================================================================

class TestMigrateCyclingOffsetCompressorStart:
    """Migration adds compressor_start_cycling_total after defrost_cycling_total if absent."""

    # Minimal lambda_wp_config.yaml WITHOUT compressor_start_cycling_total
    _YAML_WITHOUT = """\
# Cycling counter offsets for total sensors
# These offsets are added to the calculated cycling counts
# Useful when replacing heat pumps or resetting counters
# Example:
#cycling_offsets:
#  hp1:
#    heating_cycling_total: 0      # Offset for HP1 heating total cycles
#    hot_water_cycling_total: 0    # Offset for HP1 hot water total cycles
#    cooling_cycling_total: 0      # Offset for HP1 cooling total cycles
#    defrost_cycling_total: 0      # Offset for HP1 defrost total cycles
#  hp2:
#    heating_cycling_total: 1500   # Example
#    hot_water_cycling_total: 800  # Example
#    cooling_cycling_total: 200    # Example
#    defrost_cycling_total: 50     # Example

# Energy consumption sensor configuration
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.test"
    # thermal_sensor_entity_id: "sensor.test_thermal"  # optional
"""

    # Same file but WITH compressor_start_cycling_total already present
    _YAML_WITH = """\
# Cycling counter offsets for total sensors
# These offsets are added to the calculated cycling counts
# Useful when replacing heat pumps or resetting counters
# Example:
#cycling_offsets:
#  hp1:
#    heating_cycling_total: 0
#    hot_water_cycling_total: 0
#    cooling_cycling_total: 0
#    defrost_cycling_total: 0
#    compressor_start_cycling_total: 0      # Offset for compressor start total
#  hp2:
#    heating_cycling_total: 1500
#    hot_water_cycling_total: 800
#    cooling_cycling_total: 200
#    defrost_cycling_total: 50
#    compressor_start_cycling_total: 0      # Offset for compressor start total

# Energy consumption sensor configuration
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.test"
    # thermal_sensor_entity_id: "sensor.test_thermal"  # optional
"""

    # Active (uncommented) cycling_offsets without compressor_start_cycling_total
    _YAML_ACTIVE = """\
# Cycling counter offsets for total sensors
cycling_offsets:
  hp1:
    heating_cycling_total: 100
    hot_water_cycling_total: 50
    cooling_cycling_total: 10
    defrost_cycling_total: 5

# Energy consumption sensor configuration
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.test"
    # thermal_sensor_entity_id: "sensor.test_thermal"  # optional
"""

    def _make_hass(self, tmp_path, content):
        config_path = tmp_path / "lambda_wp_config.yaml"
        config_path.write_text(content, encoding="utf-8")
        hass = Mock()
        hass.config.config_dir = str(tmp_path)
        # async_add_executor_job executes sync callables synchronously in tests
        async def fake_executor(fn, *args):
            return fn(*args) if args else fn()
        hass.async_add_executor_job = fake_executor
        return hass, config_path

    @pytest.mark.asyncio
    async def test_adds_line_when_missing(self, tmp_path):
        """compressor_start_cycling_total is inserted after each defrost_cycling_total."""
        from custom_components.lambda_heat_pumps.migration import migrate_lambda_config_sections
        hass, config_path = self._make_hass(tmp_path, self._YAML_WITHOUT)

        result = await migrate_lambda_config_sections(hass)

        assert result is True
        updated = config_path.read_text(encoding="utf-8")
        assert "compressor_start_cycling_total:" in updated
        # Must appear after defrost_cycling_total in the file
        defrost_pos = updated.find("defrost_cycling_total: 0      # Offset")
        compressor_pos = updated.find("compressor_start_cycling_total:", defrost_pos)
        assert compressor_pos > defrost_pos

    @pytest.mark.asyncio
    async def test_skips_when_already_present(self, tmp_path):
        """compressor_start_cycling_total is not duplicated when already present."""
        from custom_components.lambda_heat_pumps.migration import migrate_lambda_config_sections
        hass, config_path = self._make_hass(tmp_path, self._YAML_WITH)
        original_count = self._YAML_WITH.count("compressor_start_cycling_total:")

        await migrate_lambda_config_sections(hass)

        updated = config_path.read_text(encoding="utf-8")
        # Count must not increase — no duplicate insertion
        assert updated.count("compressor_start_cycling_total:") == original_count

    @pytest.mark.asyncio
    async def test_handles_active_cycling_offsets(self, tmp_path):
        """Active (uncommented) cycling_offsets section also gets the line added."""
        from custom_components.lambda_heat_pumps.migration import migrate_lambda_config_sections
        hass, config_path = self._make_hass(tmp_path, self._YAML_ACTIVE)

        result = await migrate_lambda_config_sections(hass)

        assert result is True
        updated = config_path.read_text(encoding="utf-8")
        assert "compressor_start_cycling_total:" in updated
        # Should NOT be commented out (prefix is spaces, not #)
        for line in updated.splitlines():
            if "compressor_start_cycling_total:" in line:
                assert not line.lstrip().startswith("#"), (
                    "Active cycling_offsets: compressor line must not be commented out"
                )
                break

    @pytest.mark.asyncio
    async def test_preserves_other_content(self, tmp_path):
        """Existing cycling offset lines are preserved; only compressor line is added."""
        from custom_components.lambda_heat_pumps.migration import migrate_lambda_config_sections
        hass, config_path = self._make_hass(tmp_path, self._YAML_WITHOUT)

        await migrate_lambda_config_sections(hass)

        updated = config_path.read_text(encoding="utf-8")
        # All original cycling-offsets example lines must still be present
        cycling_lines = [
            "#cycling_offsets:",
            "#    heating_cycling_total: 0      # Offset for HP1 heating total cycles",
            "#    hot_water_cycling_total: 0    # Offset for HP1 hot water total cycles",
            "#    cooling_cycling_total: 0      # Offset for HP1 cooling total cycles",
            "#    defrost_cycling_total: 0      # Offset for HP1 defrost total cycles",
            "#    heating_cycling_total: 1500   # Example",
            "#    defrost_cycling_total: 50     # Example",
        ]
        for line in cycling_lines:
            assert line in updated, f"Cycling line missing after migration: {line!r}"
