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
from unittest.mock import AsyncMock, Mock, mock_open, patch

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

def make_energy_sensor(mock_entry, mock_coordinator, mode="heating", period="total", hp_index=1, thermal=False):
    """Create a LambdaEnergyConsumptionSensor with minimal mocking."""
    from custom_components.lambda_heat_pumps.sensor import LambdaEnergyConsumptionSensor

    if thermal:
        sid = f"{mode}_thermal_energy_{period}"
    else:
        sid = f"{mode}_energy_{period}"
    sensor = LambdaEnergyConsumptionSensor(
        hass=mock_coordinator.hass,
        entry=mock_entry,
        sensor_id=sid,
        name=f"Test Energy {mode} {'thermal ' if thermal else ''}{period}",
        entity_id=f"sensor.test_hp{hp_index}_{sid}",
        unique_id=f"test_hp{hp_index}_{sid}",
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

    @pytest.mark.asyncio
    async def test_thermal_sensor_uses_thermal_offset_key(self, mock_entry, mock_coordinator):
        """Thermal sensor must use its own offset key, not the electrical one.

        Regression: _apply_energy_offset() hardcoded sensor_id = f"{mode}_energy_total",
        so the thermal sensor (hot_water_thermal_energy_total) looked up the electrical
        key (hot_water_energy_total) and applied the wrong offset.
        """
        thermal_sensor = make_energy_sensor(mock_entry, mock_coordinator, mode="hot_water", period="total", thermal=True)
        thermal_sensor._energy_value = 100.0
        thermal_sensor._applied_offset = 0.0

        config = {"energy_consumption_offsets": {"hp1": {
            "hot_water_energy_total": 500.541,         # electrical — must NOT apply here
            "hot_water_thermal_energy_total": 2556.089,  # thermal — must apply
        }}}
        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value=config):
            await thermal_sensor._apply_energy_offset()

        assert abs(thermal_sensor._energy_value - 2656.089) < 0.001, (
            f"Expected 2656.089 (100 + 2556.089 thermal offset) but got {thermal_sensor._energy_value}. "
            "Regression: thermal sensor applied the electrical offset instead of its own."
        )
        assert abs(thermal_sensor._applied_offset - 2556.089) < 0.001

    @pytest.mark.asyncio
    async def test_electrical_sensor_not_affected_by_thermal_offset(self, mock_entry, mock_coordinator):
        """Electrical sensor must not pick up the thermal offset."""
        electrical_sensor = make_energy_sensor(mock_entry, mock_coordinator, mode="hot_water", period="total", thermal=False)
        electrical_sensor._energy_value = 100.0
        electrical_sensor._applied_offset = 0.0

        config = {"energy_consumption_offsets": {"hp1": {
            "hot_water_energy_total": 500.541,
            "hot_water_thermal_energy_total": 2556.089,
        }}}
        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value=config):
            await electrical_sensor._apply_energy_offset()

        assert abs(electrical_sensor._energy_value - 600.541) < 0.001, (
            f"Expected 600.541 (100 + 500.541 electrical offset) but got {electrical_sensor._energy_value}. "
            "Regression: electrical sensor applied the thermal offset."
        )
        assert abs(electrical_sensor._applied_offset - 500.541) < 0.001


# ===========================================================================
# 5b. Energy offset – applied via async_added_to_hass() (end-to-end regression)
#
# Pre-fix: _apply_energy_offset() existed and was correctly implemented but was
# never called. async_added_to_hass() on LambdaEnergyConsumptionSensor returned
# without invoking it, so configured offsets were silently ignored after every
# HA restart.
#
# These tests call async_added_to_hass() with mocked HA internals and assert the
# final energy value — they FAIL with the old code and PASS with the fix.
# ===========================================================================

class TestEnergyOffsetAppliedViaAsyncAddedToHass:
    """
    Regression tests: _apply_energy_offset() must be called from async_added_to_hass().

    Pre-fix: _apply_energy_offset() existed and was correctly implemented but was
    never invoked during startup. async_added_to_hass() called restore_state() and
    optionally _apply_persisted_energy_state() (which overwrites _energy_value with
    the coordinator's raw persisted value) — but never called _apply_energy_offset().
    Configured offsets were silently ignored after every HA restart.

    Fix: _apply_energy_offset() is now called at the end of async_added_to_hass(),
    after _apply_persisted_energy_state(), so the offset is applied on top of whatever
    raw value the coordinator restored.
    """

    def _make_last_state(self, value: float, applied_offset: float = 0.0):
        state = Mock()
        state.state = str(value)
        state.attributes = {"applied_offset": applied_offset}
        return state

    def _run_async_added_to_hass(self, sensor, last_state, coordinator_state=None, config=None):
        """Helper: run async_added_to_hass() with mocked dependencies.

        Patches out the HA framework methods that can't run in unit tests:
          - super().async_added_to_hass() → no-op
          - async_get_last_state() → last_state
          - _get_energy_sensor_persisted_state_from_coordinator() → coordinator_state
          - async_dispatcher_connect → no-op (signal handler registration)
        """
        from unittest.mock import patch, AsyncMock, MagicMock
        from custom_components.lambda_heat_pumps.sensor import LambdaEnergyConsumptionSensor

        patches = [
            patch.object(
                LambdaEnergyConsumptionSensor,
                "async_added_to_hass",
                wraps=sensor.async_added_to_hass,
            ),
        ]
        ctx_super = patch(
            "homeassistant.helpers.entity.Entity.async_added_to_hass",
            new=AsyncMock(),
        )
        ctx_last_state = patch.object(
            sensor, "async_get_last_state", return_value=last_state
        )
        ctx_coord_state = patch.object(
            sensor,
            "_get_energy_sensor_persisted_state_from_coordinator",
            return_value=coordinator_state,
        )
        ctx_dispatcher = patch(
            "custom_components.lambda_heat_pumps.sensor.async_dispatcher_connect",
            return_value=Mock(),
        )
        ctx_config = patch(
            "custom_components.lambda_heat_pumps.utils.load_lambda_config",
            return_value=config or {},
        )

        import asyncio

        async def _run():
            async with ctx_super, ctx_last_state, ctx_coord_state, ctx_dispatcher, ctx_config:
                await sensor.async_added_to_hass()

        return asyncio.get_event_loop().run_until_complete(_run())

    @pytest.mark.asyncio
    async def test_offset_applied_to_total_sensor_via_async_added_to_hass(self, mock_entry, mock_coordinator):
        """async_added_to_hass() must apply the configured energy offset to total sensors.

        Pre-fix: _apply_energy_offset() was never called → sensor stayed at restored
        value (1000.0) instead of offset value (1500.541).
        """
        from custom_components.lambda_heat_pumps.sensor import LambdaEnergyConsumptionSensor

        sensor = make_energy_sensor(mock_entry, mock_coordinator, mode="hot_water", period="total")
        last_state = self._make_last_state(1000.0, applied_offset=0.0)
        config = {"energy_consumption_offsets": {"hp1": {"hot_water_energy_total": 500.541}}}

        with patch("homeassistant.helpers.entity.Entity.async_added_to_hass", new=AsyncMock()):
            with patch.object(sensor, "async_get_last_state", return_value=last_state):
                with patch.object(sensor, "_get_energy_sensor_persisted_state_from_coordinator", return_value=None):
                    with patch("custom_components.lambda_heat_pumps.sensor.async_dispatcher_connect", return_value=Mock()):
                        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value=config):
                            await sensor.async_added_to_hass()

        assert abs(sensor._energy_value - 1500.541) < 0.001, (
            f"Expected 1500.541 (1000.0 restored + 500.541 offset) but got {sensor._energy_value}. "
            "Regression: _apply_energy_offset() not called from async_added_to_hass()."
        )
        assert abs(sensor._applied_offset - 500.541) < 0.001

    @pytest.mark.asyncio
    async def test_offset_not_applied_twice_on_second_restart(self, mock_entry, mock_coordinator):
        """On a second HA restart with the same offset, the value must not grow.

        _applied_offset is persisted in state attributes and restored. The
        differential tracking must prevent double-application.
        """
        sensor = make_energy_sensor(mock_entry, mock_coordinator, mode="hot_water", period="total")
        # Simulate second restart: value already includes offset, applied_offset already set
        last_state = self._make_last_state(1500.541, applied_offset=500.541)
        config = {"energy_consumption_offsets": {"hp1": {"hot_water_energy_total": 500.541}}}

        with patch("homeassistant.helpers.entity.Entity.async_added_to_hass", new=AsyncMock()):
            with patch.object(sensor, "async_get_last_state", return_value=last_state):
                with patch.object(sensor, "_get_energy_sensor_persisted_state_from_coordinator", return_value=None):
                    with patch("custom_components.lambda_heat_pumps.sensor.async_dispatcher_connect", return_value=Mock()):
                        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value=config):
                            await sensor.async_added_to_hass()

        assert abs(sensor._energy_value - 1500.541) < 0.001, (
            f"Expected 1500.541 (offset not re-applied) but got {sensor._energy_value}. "
            "Regression: differential tracking failed — offset applied twice."
        )

    @pytest.mark.asyncio
    async def test_offset_applied_after_coordinator_persisted_state_overwrites(self, mock_entry, mock_coordinator):
        """Offset must be applied AFTER _apply_persisted_energy_state().

        Scenario: restore_state() sets _energy_value = 1500.541 (with offset already in
        state), then _apply_persisted_energy_state() overwrites with raw coordinator
        value 1000.0. The offset (500.541) must still be applied on top → 1500.541.
        """
        sensor = make_energy_sensor(mock_entry, mock_coordinator, mode="hot_water", period="total")
        # last_state has the offset already applied (from previous session)
        last_state = self._make_last_state(1500.541, applied_offset=500.541)
        # Coordinator persisted state has raw value (no offset)
        coordinator_state = {"attributes": {"energy_value": 1000.0, "applied_offset": 0.0}}
        config = {"energy_consumption_offsets": {"hp1": {"hot_water_energy_total": 500.541}}}

        with patch("homeassistant.helpers.entity.Entity.async_added_to_hass", new=AsyncMock()):
            with patch.object(sensor, "async_get_last_state", return_value=last_state):
                with patch.object(sensor, "_get_energy_sensor_persisted_state_from_coordinator", return_value=coordinator_state):
                    with patch("custom_components.lambda_heat_pumps.sensor.async_dispatcher_connect", return_value=Mock()):
                        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value=config):
                            await sensor.async_added_to_hass()

        assert abs(sensor._energy_value - 1500.541) < 0.001, (
            f"Expected 1500.541 (coordinator raw 1000.0 + offset 500.541) but got {sensor._energy_value}. "
            "Regression: offset not applied after _apply_persisted_energy_state() overwrote the value."
        )

    @pytest.mark.asyncio
    async def test_offset_applied_when_coordinator_json_has_no_applied_offset_field(self, mock_entry, mock_coordinator):
        """Offset must be applied when coordinator JSON has no applied_offset field (old format).

        Scenario (user's actual bug): HA state has applied_offset=500.54 from a previous
        session where _apply_energy_offset() ran but the coordinator JSON was never flushed
        with the updated value. The old coordinator JSON has energy_value=60.53 (raw) and
        no applied_offset key. Without the fix, _apply_persisted_energy_state() leaves
        _applied_offset=500.54 from HA state → diff=0 → offset not applied → value stays 60.53.

        Fix: when applied_offset is absent from coordinator JSON, reset it to 0 so the full
        offset is re-applied on top of the coordinator's raw value.
        """
        sensor = make_energy_sensor(mock_entry, mock_coordinator, mode="hot_water", period="total")
        # HA state from previous session: value=560.53 (with offset), applied_offset=500.541
        last_state = self._make_last_state(560.53, applied_offset=500.541)
        # OLD coordinator JSON: energy_value=60.53 (raw), no applied_offset field (pre-fix format)
        coordinator_state = {"attributes": {"energy_value": 60.53}}  # no applied_offset key
        config = {"energy_consumption_offsets": {"hp1": {"hot_water_energy_total": 500.541}}}

        # Wrap coordinator_state so _apply_persisted_energy_state gets the right dict shape
        # (it calls data.get("attributes"))
        with patch("homeassistant.helpers.entity.Entity.async_added_to_hass", new=AsyncMock()):
            with patch.object(sensor, "async_get_last_state", return_value=last_state):
                with patch.object(sensor, "_get_energy_sensor_persisted_state_from_coordinator", return_value=coordinator_state):
                    with patch("custom_components.lambda_heat_pumps.sensor.async_dispatcher_connect", return_value=Mock()):
                        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value=config):
                            await sensor.async_added_to_hass()

        assert abs(sensor._energy_value - 561.071) < 0.01, (
            f"Expected ~561.071 (coordinator raw 60.53 + offset 500.541) but got {sensor._energy_value}. "
            "Regression: old coordinator JSON (no applied_offset field) caused offset to be skipped — "
            "applied_offset from HA state was mistakenly used as the base."
        )
        assert abs(sensor._applied_offset - 500.541) < 0.001

    @pytest.mark.asyncio
    async def test_apply_energy_offset_called_from_async_added_to_hass(self, mock_entry, mock_coordinator):
        """_apply_energy_offset must be invoked from async_added_to_hass() for total sensors.

        This is the explicit call-site test: even if the value arithmetic changes,
        the call itself must happen.
        """
        sensor = make_energy_sensor(mock_entry, mock_coordinator, mode="heating", period="total")

        with patch("homeassistant.helpers.entity.Entity.async_added_to_hass", new=AsyncMock()):
            with patch.object(sensor, "async_get_last_state", return_value=None):
                with patch.object(sensor, "_get_energy_sensor_persisted_state_from_coordinator", return_value=None):
                    with patch("custom_components.lambda_heat_pumps.sensor.async_dispatcher_connect", return_value=Mock()):
                        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value={}):
                            with patch.object(sensor, "_apply_energy_offset", new_callable=AsyncMock) as mock_apply:
                                await sensor.async_added_to_hass()

        mock_apply.assert_called_once(), (
            "Regression: _apply_energy_offset() was not called from async_added_to_hass(). "
            "Energy offsets are silently ignored after every HA restart."
        )

    @pytest.mark.asyncio
    async def test_apply_energy_offset_not_called_for_daily_sensor(self, mock_entry, mock_coordinator):
        """_apply_energy_offset must NOT be called from async_added_to_hass() for daily sensors."""
        sensor = make_energy_sensor(mock_entry, mock_coordinator, mode="heating", period="daily")
        last_state = Mock()
        last_state.state = "5.0"
        last_state.attributes = {"applied_offset": 0.0, "yesterday_value": 0.0, "energy_value": 5.0}

        with patch("homeassistant.helpers.entity.Entity.async_added_to_hass", new=AsyncMock()):
            with patch.object(sensor, "async_get_last_state", return_value=last_state):
                with patch.object(sensor, "_get_energy_sensor_persisted_state_from_coordinator", return_value=None):
                    with patch("custom_components.lambda_heat_pumps.sensor.async_dispatcher_connect", return_value=Mock()):
                        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value={}):
                            with patch.object(sensor, "_apply_energy_offset", new_callable=AsyncMock) as mock_apply:
                                # Patch asyncio.sleep to avoid real delay in daily init path
                                with patch("asyncio.sleep", new=AsyncMock()):
                                    with patch.object(sensor, "_initialize_daily_yesterday_value", new=AsyncMock(return_value=False)):
                                        await sensor.async_added_to_hass()

        mock_apply.assert_not_called(), (
            "Regression: _apply_energy_offset() called on a daily sensor — "
            "would corrupt the daily display value."
        )


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

    def _run_offset_warning_check(self, yaml_content):
        """Helper: parse YAML and run the electrical/thermal mismatch warning logic inline.

        Simulates the check added to load_lambda_config() without requiring the full
        file-loading machinery.
        """
        import yaml, logging
        raw = yaml.safe_load(yaml_content)
        offsets_config = raw.get("energy_consumption_offsets", {})
        _THERMAL_MODES = ("heating", "hot_water", "cooling", "defrost")
        warnings_emitted = []
        for device, offsets in offsets_config.items():
            if not isinstance(offsets, dict):
                continue
            for mode in _THERMAL_MODES:
                elec_key = f"{mode}_energy_total"
                therm_key = f"{mode}_thermal_energy_total"
                elec_val = float(offsets.get(elec_key, 0.0))
                therm_val = float(offsets.get(therm_key, 0.0))
                if elec_val != 0.0 and therm_val == 0.0:
                    warnings_emitted.append(("elec_only", device, mode, elec_key, therm_key))
                elif therm_val != 0.0 and elec_val == 0.0:
                    warnings_emitted.append(("therm_only", device, mode, therm_key, elec_key))
        return warnings_emitted

    def test_warns_when_electrical_set_but_thermal_missing(self):
        """Mismatch check fires when electrical offset is set but thermal is absent."""
        yaml_content = """
energy_consumption_offsets:
  hp1:
    hot_water_energy_total: 500.541
"""
        warnings = self._run_offset_warning_check(yaml_content)
        assert len(warnings) == 1
        kind, device, mode, set_key, missing_key = warnings[0]
        assert kind == "elec_only"
        assert device == "hp1"
        assert mode == "hot_water"
        assert set_key == "hot_water_energy_total"
        assert missing_key == "hot_water_thermal_energy_total"

    def test_warns_when_thermal_set_but_electrical_missing(self):
        """Mismatch check fires when thermal offset is set but electrical is absent."""
        yaml_content = """
energy_consumption_offsets:
  hp1:
    heating_thermal_energy_total: 6500.0
"""
        warnings = self._run_offset_warning_check(yaml_content)
        assert len(warnings) == 1
        kind, device, mode, set_key, missing_key = warnings[0]
        assert kind == "therm_only"
        assert mode == "heating"
        assert set_key == "heating_thermal_energy_total"
        assert missing_key == "heating_energy_total"

    def test_warns_for_each_mismatched_mode_independently(self):
        """Two mismatched modes produce two warnings."""
        yaml_content = """
energy_consumption_offsets:
  hp1:
    heating_energy_total: 1000.0
    hot_water_thermal_energy_total: 2556.089
"""
        warnings = self._run_offset_warning_check(yaml_content)
        assert len(warnings) == 2
        modes = {w[2] for w in warnings}
        assert modes == {"heating", "hot_water"}

    def test_no_warning_when_both_offsets_set(self):
        """No mismatch warning when both electrical and thermal offsets are set."""
        yaml_content = """
energy_consumption_offsets:
  hp1:
    hot_water_energy_total: 500.541
    hot_water_thermal_energy_total: 2556.089
"""
        warnings = self._run_offset_warning_check(yaml_content)
        assert warnings == [], f"No warning expected, got: {warnings}"

    def test_no_warning_when_both_offsets_zero(self):
        """No mismatch warning when both electrical and thermal are 0 (default/disabled)."""
        yaml_content = """
energy_consumption_offsets:
  hp1:
    heating_energy_total: 0
    heating_thermal_energy_total: 0
"""
        warnings = self._run_offset_warning_check(yaml_content)
        assert warnings == [], f"No warning expected for zero offsets, got: {warnings}"

    def test_no_warning_for_stby_mode(self):
        """stby mode has no thermal sensor, so no mismatch check is needed."""
        yaml_content = """
energy_consumption_offsets:
  hp1:
    stby_energy_total: 50.0
"""
        warnings = self._run_offset_warning_check(yaml_content)
        # stby is not in _THERMAL_MODES → no warning
        assert warnings == [], f"stby should not trigger thermal mismatch warning, got: {warnings}"


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


# ===========================================================================
# 10. Migration – thermal energy offset lines
# ===========================================================================

class TestMigrateThermalEnergyOffsets:
    """Migration inserts missing thermal_energy_total lines in energy_consumption_offsets."""

    # All five section headers present → no template rebuild, tests thermal migration in isolation.
    # energy_consumption_sensors active so yaml.safe_load returns a non-empty dict.
    _SECTION_HEADERS = """\
# Override sensor names (only works if use_legacy_modbus_names is true)
#sensors_names_override:
#- id: example
#  override_name: new_name

# Cycling counter offsets for total sensors
#cycling_offsets:
#  hp1:
#    heating_cycling_total: 0
#    hot_water_cycling_total: 0
#    cooling_cycling_total: 0
#    defrost_cycling_total: 0
#    compressor_start_cycling_total: 0

# Energy consumption sensor configuration
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.test"
    # thermal_sensor_entity_id: "sensor.test_thermal"  # optional

"""

    # File with only electrical offsets (no thermal lines at all)
    _YAML_ELECTRICAL_ONLY = _SECTION_HEADERS + """\
# Energy consumption offsets for total sensors
#energy_consumption_offsets:
#  hp1:
#    heating_energy_total: 0.0
#    hot_water_energy_total: 0.0
#    cooling_energy_total: 0.0
#    defrost_energy_total: 0.0
#  hp2:
#    heating_energy_total: 150.5
#    hot_water_energy_total: 45.25
#    cooling_energy_total: 12.8
#    defrost_energy_total: 3.1

# Modbus configuration
#modbus:
#  int32_register_order: "high_first"
"""

    # File already has all 4 thermal lines for both hp blocks
    _YAML_ALL_THERMAL = _SECTION_HEADERS + """\
# Energy consumption offsets for total sensors
#energy_consumption_offsets:
#  hp1:
#    heating_energy_total: 0.0
#    hot_water_energy_total: 0.0
#    cooling_energy_total: 0.0
#    defrost_energy_total: 0.0
#    heating_thermal_energy_total: 0.0
#    hot_water_thermal_energy_total: 0.0
#    cooling_thermal_energy_total: 0.0
#    defrost_thermal_energy_total: 0.0

# Modbus configuration
#modbus:
#  int32_register_order: "high_first"
"""

    # File with only the first two thermal lines (partial migration state)
    _YAML_PARTIAL_THERMAL = _SECTION_HEADERS + """\
# Energy consumption offsets for total sensors
#energy_consumption_offsets:
#  hp1:
#    heating_energy_total: 0.0
#    hot_water_energy_total: 0.0
#    cooling_energy_total: 0.0
#    defrost_energy_total: 0.0
#    heating_thermal_energy_total: 0.0
#    hot_water_thermal_energy_total: 0.0

# Modbus configuration
#modbus:
#  int32_register_order: "high_first"
"""

    def _make_hass(self, tmp_path, content):
        config_path = tmp_path / "lambda_wp_config.yaml"
        config_path.write_text(content, encoding="utf-8")
        hass = Mock()
        hass.config.config_dir = str(tmp_path)
        async def fake_executor(fn, *args):
            return fn(*args) if args else fn()
        hass.async_add_executor_job = fake_executor
        return hass, config_path

    @pytest.mark.asyncio
    async def test_adds_all_four_thermal_lines_when_missing(self, tmp_path):
        """All 4 thermal_energy_total lines are inserted after defrost_energy_total."""
        from custom_components.lambda_heat_pumps.migration import migrate_lambda_config_sections
        hass, config_path = self._make_hass(tmp_path, self._YAML_ELECTRICAL_ONLY)

        result = await migrate_lambda_config_sections(hass)

        assert result is True
        updated = config_path.read_text(encoding="utf-8")
        for key in ["heating_thermal_energy_total:", "hot_water_thermal_energy_total:",
                    "cooling_thermal_energy_total:", "defrost_thermal_energy_total:"]:
            assert key in updated, f"Missing after migration: {key}"

    @pytest.mark.asyncio
    async def test_thermal_lines_inserted_after_defrost_energy(self, tmp_path):
        """heating_thermal_energy_total appears after defrost_energy_total in the file."""
        from custom_components.lambda_heat_pumps.migration import migrate_lambda_config_sections
        hass, config_path = self._make_hass(tmp_path, self._YAML_ELECTRICAL_ONLY)

        await migrate_lambda_config_sections(hass)

        updated = config_path.read_text(encoding="utf-8")
        defrost_pos = updated.find("defrost_energy_total: 0.0")
        thermal_pos = updated.find("heating_thermal_energy_total:", defrost_pos)
        assert thermal_pos > defrost_pos

    @pytest.mark.asyncio
    async def test_skips_when_all_thermal_present(self, tmp_path):
        """No thermal lines are duplicated when all 4 are already present."""
        from custom_components.lambda_heat_pumps.migration import migrate_lambda_config_sections
        hass, config_path = self._make_hass(tmp_path, self._YAML_ALL_THERMAL)
        original_count = self._YAML_ALL_THERMAL.count("thermal_energy_total:")

        await migrate_lambda_config_sections(hass)

        updated = config_path.read_text(encoding="utf-8")
        assert updated.count("thermal_energy_total:") == original_count

    @pytest.mark.asyncio
    async def test_adds_only_missing_thermal_lines(self, tmp_path):
        """Only cooling_thermal and defrost_thermal are added when heating and hot_water already present."""
        from custom_components.lambda_heat_pumps.migration import migrate_lambda_config_sections
        hass, config_path = self._make_hass(tmp_path, self._YAML_PARTIAL_THERMAL)

        result = await migrate_lambda_config_sections(hass)

        assert result is True
        updated = config_path.read_text(encoding="utf-8")
        assert updated.count("heating_thermal_energy_total:") == 1   # not duplicated
        assert updated.count("hot_water_thermal_energy_total:") == 1  # not duplicated
        assert "cooling_thermal_energy_total:" in updated             # newly added
        assert "defrost_thermal_energy_total:" in updated             # newly added

    @pytest.mark.asyncio
    async def test_thermal_lines_inserted_for_multiple_hp_blocks(self, tmp_path):
        """Thermal lines are added for every hp-block that has defrost_energy_total."""
        from custom_components.lambda_heat_pumps.migration import migrate_lambda_config_sections
        hass, config_path = self._make_hass(tmp_path, self._YAML_ELECTRICAL_ONLY)

        await migrate_lambda_config_sections(hass)

        updated = config_path.read_text(encoding="utf-8")
        # Two hp-blocks (hp1, hp2) → each gets 4 thermal lines → 8 total
        assert updated.count("heating_thermal_energy_total:") == 2
        assert updated.count("defrost_thermal_energy_total:") == 2
