"""Tests für Sensor-Wechsel-Erkennung (Display-Tausch / Zählerreset-Szenario).

Geprüfte Funktionen:
- detect_sensor_change (utils.py)
- get_stored_sensor_id / get_stored_thermal_sensor_id (utils.py)
- store_sensor_id / store_thermal_sensor_id (utils.py)
- _handle_sensor_change (coordinator.py)
- _handle_thermal_sensor_change (coordinator.py)
- _detect_and_handle_sensor_changes (coordinator.py) – Vollablauf
"""

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from custom_components.lambda_heat_pumps.utils import (
    detect_sensor_change,
    get_stored_sensor_id,
    get_stored_thermal_sensor_id,
    store_sensor_id,
    store_thermal_sensor_id,
)


# ---------------------------------------------------------------------------
# detect_sensor_change – unit tests
# ---------------------------------------------------------------------------

class TestDetectSensorChange:
    def test_returns_false_when_no_stored_id(self):
        assert detect_sensor_change(None, "sensor.new") is False

    def test_returns_false_when_stored_is_empty_string(self):
        assert detect_sensor_change("", "sensor.new") is False

    def test_returns_false_when_ids_identical(self):
        assert detect_sensor_change("sensor.same", "sensor.same") is False

    def test_returns_true_when_ids_differ(self):
        assert detect_sensor_change("sensor.old", "sensor.new") is True

    def test_strips_whitespace(self):
        assert detect_sensor_change("  sensor.old  ", "sensor.old") is False

    def test_strips_quotes(self):
        assert detect_sensor_change('"sensor.old"', "sensor.old") is False

    def test_strips_single_quotes(self):
        assert detect_sensor_change("'sensor.old'", "sensor.old") is False

    def test_detects_change_after_display_swap(self):
        """Kernszenario: Modbus-Sensor → Template-Sensor nach Display-Tausch."""
        old = "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
        new = "sensor.hp1_compressor_power_corrected"
        assert detect_sensor_change(old, new) is True

    def test_detects_thermal_change_after_display_swap(self):
        old = "sensor.eu08l_hp1_compressor_thermal_energy_output_accumulated"
        new = "sensor.hp1_thermal_energy_corrected"
        assert detect_sensor_change(old, new) is True


# ---------------------------------------------------------------------------
# get/store sensor_id helpers
# ---------------------------------------------------------------------------

class TestSensorIdHelpers:
    def test_get_stored_sensor_id_found(self):
        data = {"sensor_ids": {"hp1": "sensor.old_elec"}}
        assert get_stored_sensor_id(data, 1) == "sensor.old_elec"

    def test_get_stored_sensor_id_missing_hp(self):
        data = {"sensor_ids": {"hp1": "sensor.old_elec"}}
        assert get_stored_sensor_id(data, 2) is None

    def test_get_stored_sensor_id_empty(self):
        assert get_stored_sensor_id({}, 1) is None

    def test_store_sensor_id_creates_section(self):
        data = {}
        store_sensor_id(data, 1, "sensor.new")
        assert data["sensor_ids"]["hp1"] == "sensor.new"

    def test_store_sensor_id_normalizes_quotes(self):
        data = {}
        store_sensor_id(data, 1, '"sensor.new"')
        assert data["sensor_ids"]["hp1"] == "sensor.new"

    def test_get_stored_thermal_sensor_id_found(self):
        data = {"thermal_sensor_ids": {"hp1": "sensor.old_therm"}}
        assert get_stored_thermal_sensor_id(data, 1) == "sensor.old_therm"

    def test_get_stored_thermal_sensor_id_missing(self):
        assert get_stored_thermal_sensor_id({}, 1) is None

    def test_store_thermal_sensor_id_creates_section(self):
        data = {}
        store_thermal_sensor_id(data, 1, "sensor.therm_new")
        assert data["thermal_sensor_ids"]["hp1"] == "sensor.therm_new"


# ---------------------------------------------------------------------------
# Coordinator._handle_sensor_change
# ---------------------------------------------------------------------------

def _make_coordinator(name="eu08l"):
    """Minimal Coordinator-ähnliches Objekt für isolierte Tests."""
    coord = SimpleNamespace()
    coord.entry = SimpleNamespace(data={"name": name})
    coord.hass = MagicMock()
    coord._last_energy_reading = {}
    coord._energy_first_value_seen = {}
    coord._persist_dirty = False
    coord._persist_counters = AsyncMock()
    # Binde die echten Methoden
    from custom_components.lambda_heat_pumps.coordinator import LambdaDataUpdateCoordinator
    coord._handle_sensor_change = LambdaDataUpdateCoordinator._handle_sensor_change.__get__(coord)
    coord._handle_thermal_sensor_change = LambdaDataUpdateCoordinator._handle_thermal_sensor_change.__get__(coord)
    coord._detect_and_handle_sensor_changes = LambdaDataUpdateCoordinator._detect_and_handle_sensor_changes.__get__(coord)
    return coord


class TestHandleSensorChange:
    @pytest.mark.asyncio
    async def test_custom_sensor_activates_zero_value_protection(self):
        """Wechsel zu externem Template-Sensor → last_energy_reading = None."""
        coord = _make_coordinator()
        coord.hass.states.get.return_value = None

        await coord._handle_sensor_change(1, "sensor.hp1_compressor_power_corrected")

        assert coord._last_energy_reading["hp1"] is None
        assert coord._energy_first_value_seen["hp1"] is False
        coord._persist_counters.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_default_sensor_with_positive_db_value_sets_reference(self):
        """Rückkehr zum Modbus-Default-Sensor mit bekanntem DB-Wert → Referenzwert gesetzt."""
        coord = _make_coordinator()
        db_state = MagicMock()
        db_state.state = "45230.0"
        coord.hass.states.get.return_value = db_state

        default_id = "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
        await coord._handle_sensor_change(1, default_id)

        assert coord._last_energy_reading["hp1"] == pytest.approx(45230.0)
        assert coord._energy_first_value_seen["hp1"] is True

    @pytest.mark.asyncio
    async def test_default_sensor_with_zero_db_value_activates_protection(self):
        """Default-Sensor, aber DB-Wert = 0 → Zero-Value Protection."""
        coord = _make_coordinator()
        db_state = MagicMock()
        db_state.state = "0"
        coord.hass.states.get.return_value = db_state

        default_id = "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
        await coord._handle_sensor_change(1, default_id)

        assert coord._last_energy_reading["hp1"] is None

    @pytest.mark.asyncio
    async def test_default_sensor_unavailable_activates_protection(self):
        """Default-Sensor mit 'unavailable' State → Zero-Value Protection."""
        coord = _make_coordinator()
        db_state = MagicMock()
        db_state.state = "unavailable"
        coord.hass.states.get.return_value = db_state

        default_id = "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
        await coord._handle_sensor_change(1, default_id)

        assert coord._last_energy_reading["hp1"] is None

    @pytest.mark.asyncio
    async def test_default_sensor_no_state_activates_protection(self):
        coord = _make_coordinator()
        coord.hass.states.get.return_value = None

        default_id = "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
        await coord._handle_sensor_change(1, default_id)

        assert coord._last_energy_reading["hp1"] is None


# ---------------------------------------------------------------------------
# Coordinator._handle_thermal_sensor_change
# ---------------------------------------------------------------------------

class TestHandleThermalSensorChange:
    def _make_coord(self):
        coord = _make_coordinator()
        coord._last_thermal_energy_reading = {}
        coord._thermal_energy_first_value_seen = {}
        return coord

    @pytest.mark.asyncio
    async def test_custom_thermal_sensor_activates_zero_value_protection(self):
        """Template-Thermik-Sensor → last_thermal_energy_reading = None."""
        coord = self._make_coord()
        coord.hass.states.get.return_value = None

        await coord._handle_thermal_sensor_change(1, "sensor.hp1_thermal_energy_corrected")

        assert coord._last_thermal_energy_reading["hp1"] is None
        assert coord._thermal_energy_first_value_seen["hp1"] is False

    @pytest.mark.asyncio
    async def test_default_thermal_sensor_with_db_value_sets_reference(self):
        coord = self._make_coord()
        db_state = MagicMock()
        db_state.state = "128500.0"
        coord.hass.states.get.return_value = db_state

        default_id = "sensor.eu08l_hp1_compressor_thermal_energy_output_accumulated"
        await coord._handle_thermal_sensor_change(1, default_id)

        assert coord._last_thermal_energy_reading["hp1"] == pytest.approx(128500.0)
        assert coord._thermal_energy_first_value_seen["hp1"] is True

    @pytest.mark.asyncio
    async def test_default_thermal_sensor_zero_db_activates_protection(self):
        coord = self._make_coord()
        db_state = MagicMock()
        db_state.state = "0"
        coord.hass.states.get.return_value = db_state

        default_id = "sensor.eu08l_hp1_compressor_thermal_energy_output_accumulated"
        await coord._handle_thermal_sensor_change(1, default_id)

        assert coord._last_thermal_energy_reading["hp1"] is None


# ---------------------------------------------------------------------------
# _detect_and_handle_sensor_changes – Vollablauf (Kernszenario Anleitung)
# ---------------------------------------------------------------------------

class TestDetectAndHandleSensorChanges:
    def _make_coord_full(self):
        coord = _make_coordinator()
        coord._last_thermal_energy_reading = {}
        coord._thermal_energy_first_value_seen = {}
        coord._energy_sensor_configs = {}
        coord._sensor_ids = {}
        coord._thermal_sensor_ids = {}
        coord._persist_dirty = False

        # _persist_counters ist bereits AsyncMock, aber wir wollen ihn im Vollablauf
        # nicht wirklich ausführen – reuse bestehenden Mock
        return coord

    @pytest.mark.asyncio
    async def test_no_stored_ids_no_change_detected(self):
        """Erster Start (keine persistierten IDs) → kein Sensor-Wechsel, IDs gespeichert."""
        coord = self._make_coord_full()
        coord._energy_sensor_configs = {
            "hp1": {"sensor_entity_id": "sensor.eu08l_hp1_compressor_power_consumption_accumulated"}
        }
        coord.hass.states.get.return_value = None

        await coord._detect_and_handle_sensor_changes()

        # Keine Änderung → last_energy_reading unberührt
        assert coord._last_energy_reading == {}
        # sensor_ids wurden gespeichert
        assert coord._sensor_ids.get("hp1") == "sensor.eu08l_hp1_compressor_power_consumption_accumulated"

    @pytest.mark.asyncio
    async def test_custom_sensor_change_detected_zeroes_reading(self):
        """Kernszenario: Wechsel von Modbus zu Template-Sensor nach Display-Tausch.

        Gespeicherter Sensor = alter Modbus-Sensor.
        Neuer Sensor in Config = Template-Sensor (sensor.hp1_compressor_power_corrected).
        Erwartung: last_energy_reading[hp1] = None (Zero-Value Protection).
        """
        coord = self._make_coord_full()
        coord._sensor_ids = {
            "hp1": "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
        }
        coord._thermal_sensor_ids = {
            "hp1": "sensor.eu08l_hp1_compressor_thermal_energy_output_accumulated"
        }
        coord._energy_sensor_configs = {
            "hp1": {
                "sensor_entity_id": "sensor.hp1_compressor_power_corrected",
                "thermal_sensor_entity_id": "sensor.hp1_thermal_energy_corrected",
            }
        }
        coord.hass.states.get.return_value = None

        await coord._detect_and_handle_sensor_changes()

        assert coord._last_energy_reading.get("hp1") is None
        assert coord._energy_first_value_seen.get("hp1") is False
        # Neuer sensor_id wurde gespeichert
        assert coord._sensor_ids["hp1"] == "sensor.hp1_compressor_power_corrected"

    @pytest.mark.asyncio
    async def test_thermal_custom_sensor_change_detected(self):
        """Wechsel nur des Thermik-Sensors → last_thermal_energy_reading = None."""
        coord = self._make_coord_full()
        coord._sensor_ids = {
            "hp1": "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
        }
        coord._thermal_sensor_ids = {
            "hp1": "sensor.eu08l_hp1_compressor_thermal_energy_output_accumulated"
        }
        coord._energy_sensor_configs = {
            "hp1": {
                "sensor_entity_id": "sensor.eu08l_hp1_compressor_power_consumption_accumulated",
                "thermal_sensor_entity_id": "sensor.hp1_thermal_energy_corrected",
            }
        }
        coord.hass.states.get.return_value = None

        await coord._detect_and_handle_sensor_changes()

        # Elektrisch unverändert
        assert "hp1" not in coord._last_energy_reading
        # Thermik zurückgesetzt
        assert coord._last_thermal_energy_reading.get("hp1") is None
        assert coord._thermal_energy_first_value_seen.get("hp1") is False
        assert coord._thermal_sensor_ids["hp1"] == "sensor.hp1_thermal_energy_corrected"

    @pytest.mark.asyncio
    async def test_no_change_when_same_sensor(self):
        """Keine Änderung wenn selber Sensor konfiguriert wie gespeichert."""
        coord = self._make_coord_full()
        same_id = "sensor.hp1_compressor_power_corrected"
        coord._sensor_ids = {"hp1": same_id}
        coord._thermal_sensor_ids = {
            "hp1": "sensor.eu08l_hp1_compressor_thermal_energy_output_accumulated"
        }
        coord._energy_sensor_configs = {
            "hp1": {"sensor_entity_id": same_id}
        }
        coord.hass.states.get.return_value = None

        await coord._detect_and_handle_sensor_changes()

        # kein Reset
        assert "hp1" not in coord._last_energy_reading

    @pytest.mark.asyncio
    async def test_invalid_hp_key_skipped_gracefully(self):
        """Ungültiger hp_key in _sensor_ids wird übersprungen ohne Exception."""
        coord = self._make_coord_full()
        coord._sensor_ids = {"invalid_key": "sensor.something"}
        coord._energy_sensor_configs = {}

        await coord._detect_and_handle_sensor_changes()
        # Kein Absturz, kein Eintrag in last_energy_reading
        assert coord._last_energy_reading == {}
