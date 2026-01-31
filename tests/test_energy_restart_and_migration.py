"""Tests for energy sensor restart value preservation and migration (delta procedure)."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from custom_components.lambda_heat_pumps.sensor import LambdaEnergyConsumptionSensor
from custom_components.lambda_heat_pumps.const import DOMAIN
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

from tests.conftest import DummyLoop


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock()
    hass.states = MagicMock()
    hass.data = {DOMAIN: {}}
    hass.async_create_task = MagicMock()
    hass.config = MagicMock()
    hass.config.language = "en"
    hass.config.locale = __import__("types").SimpleNamespace(language="en")
    hass.loop = DummyLoop()
    return hass


@pytest.fixture
def mock_entry():
    """Mock ConfigEntry instance."""
    entry = Mock()
    entry.entry_id = "test_entry_id"
    entry.data = {"name": "eu08l", "host": "192.168.1.100", "port": 502}
    return entry


def _daily_sensor(hass, entry, entity_id="sensor.eu08l_hp1_heating_energy_daily"):
    """Create a daily energy consumption sensor."""
    return LambdaEnergyConsumptionSensor(
        hass=hass,
        entry=entry,
        sensor_id="heating_energy_daily",
        name="Heating Energy Daily",
        entity_id=entity_id,
        unique_id="eu08l_hp1_heating_energy_daily",
        unit="kWh",
        state_class="total",
        device_class=SensorDeviceClass.ENERGY,
        device_type="hp",
        hp_index=1,
        mode="heating",
        period="daily",
    )


def _total_sensor(hass, entry, entity_id="sensor.eu08l_hp1_heating_energy_total"):
    """Create a total energy consumption sensor."""
    return LambdaEnergyConsumptionSensor(
        hass=hass,
        entry=entry,
        sensor_id="heating_energy_total",
        name="Heating Energy Total",
        entity_id=entity_id,
        unique_id="eu08l_hp1_heating_energy_total",
        unit="kWh",
        state_class="total_increasing",
        device_class=SensorDeviceClass.ENERGY,
        device_type="hp",
        hp_index=1,
        mode="heating",
        period="total",
    )


# --- set_energy_value: Wert darf nicht verringert werden (Neustart-Werterhalt) ---


def test_set_energy_value_never_decreases_total(mock_hass, mock_entry):
    """Total-Sensor: set_energy_value verringert den Wert nicht (z. B. nach Neustart)."""
    sensor = _total_sensor(mock_hass, mock_entry)
    sensor.async_write_ha_state = MagicMock()
    with patch("custom_components.lambda_heat_pumps.sensor.async_get_entity_registry"):
        sensor.set_energy_value(220.84)
        assert sensor._energy_value == 220.84
        sensor.set_energy_value(220.25)  # niedrigerer Wert (z. B. veralteter Restore)
        assert sensor._energy_value == 220.84  # unverändert


def test_set_energy_value_never_decreases_daily(mock_hass, mock_entry):
    """Daily-Sensor: set_energy_value verringert _energy_value nicht (Neustart-Werterhalt)."""
    sensor = _daily_sensor(mock_hass, mock_entry)
    sensor._yesterday_value = 212.0
    sensor._energy_value = 212.44  # angezeigt 0.44
    sensor.async_write_ha_state = MagicMock()
    with patch("custom_components.lambda_heat_pumps.sensor.async_get_entity_registry"):
        sensor.set_energy_value(212.40)  # würde 0.40 anzeigen
        assert sensor._energy_value == 212.44  # bleibt 0.44


def test_set_energy_value_increases_normally(mock_hass, mock_entry):
    """set_energy_value erhöht den Wert wie gewohnt."""
    sensor = _total_sensor(mock_hass, mock_entry)
    sensor.async_write_ha_state = MagicMock()
    with patch("custom_components.lambda_heat_pumps.sensor.async_get_entity_registry"):
        sensor.set_energy_value(100.0)
        assert sensor._energy_value == 100.0
        sensor.set_energy_value(101.5)
        assert sensor._energy_value == 101.5


# --- restore_state: Migration (fehlendes energy_value → Total-Sensor) ---


@pytest.mark.asyncio
async def test_restore_daily_migration_no_energy_value_total_unavailable(mock_hass, mock_entry):
    """Daily: Fehlt energy_value (Migration), Total nicht verfügbar → rekonstruiert aus yesterday + displayed."""
    sensor = _daily_sensor(mock_hass, mock_entry)
    sensor.entity_id = "sensor.eu08l_hp1_heating_energy_daily"
    sensor.async_write_ha_state = MagicMock()
    mock_hass.states.get = Mock(return_value=None)  # Total-Sensor nicht verfügbar
    last_state = Mock(state="0.44", attributes={"yesterday_value": 212.29})  # kein energy_value

    await sensor.restore_state(last_state)

    assert sensor._yesterday_value == 212.29
    assert abs(sensor._energy_value - (212.29 + 0.44)) < 0.001
    assert sensor.native_value == pytest.approx(0.44, abs=0.01)


@pytest.mark.asyncio
async def test_restore_daily_migration_with_total_sensor(mock_hass, mock_entry):
    """Daily: Migration mit verfügbarem Total-Sensor setzt energy_value und yesterday_value aus Total."""
    sensor = _daily_sensor(mock_hass, mock_entry)
    sensor.entity_id = "sensor.eu08l_hp1_heating_energy_daily"
    sensor.async_write_ha_state = MagicMock()
    total_state = Mock()
    total_state.state = "212.73"
    total_state.attributes = {}
    mock_hass.states.get = Mock(side_effect=lambda eid: total_state if "total" in eid else None)
    last_state = Mock(state="0.44", attributes={"yesterday_value": 212.29})  # kein energy_value

    await sensor.restore_state(last_state)

    assert sensor._energy_value == 212.73
    assert sensor._yesterday_value == pytest.approx(212.73 - 0.44, abs=0.01)
    assert sensor.native_value == pytest.approx(0.44, abs=0.01)


# --- restore_state: Normaler Restore mit energy_value + current_daily_value ---


@pytest.mark.asyncio
async def test_restore_daily_preserves_displayed_value(mock_hass, mock_entry):
    """Daily: Mit energy_value und current_daily_value bleibt der Anzeigewert (0.44) erhalten."""
    sensor = _daily_sensor(mock_hass, mock_entry)
    sensor.async_write_ha_state = MagicMock()
    last_state = Mock(state="0.4")  # State evtl. mit 1 Dezimale
    last_state.attributes = {
        "yesterday_value": 212.33,
        "energy_value": 212.77,
        "current_daily_value": 0.44,
    }

    await sensor.restore_state(last_state)

    # current_daily_value (0.44) hat Vorrang; energy_value 212.77, yesterday 212.33 → 0.44
    assert sensor._yesterday_value == 212.33
    assert sensor._energy_value == 212.77
    assert sensor.native_value == pytest.approx(0.44, abs=0.01)


@pytest.mark.asyncio
async def test_restore_daily_state_overrides_rounded_attrs(mock_hass, mock_entry):
    """Daily: Wenn Attribut-Differenz 0.40 ergibt, State (0.44) rekonstruiert _energy_value."""
    sensor = _daily_sensor(mock_hass, mock_entry)
    sensor.async_write_ha_state = MagicMock()
    last_state = Mock(state="0.44")
    last_state.attributes = {
        "yesterday_value": 212.33,
        "energy_value": 212.73,  # 212.73 - 212.33 = 0.40
        "current_daily_value": 0.44,
    }

    await sensor.restore_state(last_state)

    # current_daily_value 0.44 → _energy_value = yesterday + 0.44
    assert sensor.native_value == pytest.approx(0.44, abs=0.01)
    assert sensor._energy_value == pytest.approx(212.33 + 0.44, abs=0.01)


# --- cycle_energy_persist: _apply_persisted_energy_state ---


def test_apply_persisted_energy_state(mock_hass, mock_entry):
    """_apply_persisted_energy_state übernimmt energy_value, yesterday_value, previous_*."""
    sensor = _daily_sensor(mock_hass, mock_entry)
    sensor._energy_value = 0.0
    sensor._yesterday_value = 0.0
    data = {
        "state": 0.44,
        "attributes": {
            "energy_value": 212.77,
            "yesterday_value": 212.33,
            "previous_monthly_value": 200.0,
            "previous_yearly_value": 180.0,
        },
    }

    sensor._apply_persisted_energy_state(data)

    assert sensor._energy_value == 212.77
    assert sensor._yesterday_value == 212.33
    assert sensor._previous_monthly_value == 200.0
    assert sensor._previous_yearly_value == 180.0
    assert sensor.native_value == pytest.approx(0.44, abs=0.01)


def test_apply_persisted_energy_state_empty_attrs(mock_hass, mock_entry):
    """_apply_persisted_energy_state mit leeren attributes ändert nichts an fehlenden Keys."""
    sensor = _daily_sensor(mock_hass, mock_entry)
    sensor._energy_value = 100.0
    sensor._yesterday_value = 99.0
    sensor._apply_persisted_energy_state({"state": 1.0, "attributes": {}})
    assert sensor._energy_value == 100.0
    assert sensor._yesterday_value == 99.0


# --- _get_energy_sensor_persisted_state_from_coordinator ---


def test_get_energy_sensor_persisted_state_from_coordinator_no_registry(mock_hass, mock_entry):
    """Wenn Entity-Registry keinen Eintrag liefert, gibt es keinen Persist-State."""
    sensor = _daily_sensor(mock_hass, mock_entry)
    with patch("custom_components.lambda_heat_pumps.sensor.async_get_entity_registry") as m:
        m.return_value.async_get.return_value = None
        assert sensor._get_energy_sensor_persisted_state_from_coordinator() is None


def test_get_energy_sensor_persisted_state_from_coordinator_no_coordinator(mock_hass, mock_entry):
    """Wenn kein Coordinator in hass.data, gibt es keinen Persist-State."""
    sensor = _daily_sensor(mock_hass, mock_entry)
    mock_hass.data[DOMAIN] = {"test_entry_id": {}}
    with patch("custom_components.lambda_heat_pumps.sensor.async_get_entity_registry") as m:
        reg = Mock()
        reg.async_get.return_value = Mock(config_entry_id="test_entry_id")
        m.return_value = reg
        assert sensor._get_energy_sensor_persisted_state_from_coordinator() is None


def test_get_energy_sensor_persisted_state_from_coordinator_returns_state(mock_hass, mock_entry):
    """Wenn Coordinator einen State aus cycle_energy_persist hat, wird er zurückgegeben."""
    sensor = _daily_sensor(mock_hass, mock_entry)
    persisted = {"state": 0.44, "attributes": {"energy_value": 212.77, "yesterday_value": 212.33}}
    coordinator = Mock()
    coordinator.get_energy_sensor_persisted_state = Mock(return_value=persisted)
    mock_hass.data[DOMAIN] = {"test_entry_id": {"coordinator": coordinator}}
    with patch("custom_components.lambda_heat_pumps.sensor.async_get_entity_registry") as m:
        reg = Mock()
        reg.async_get.return_value = Mock(config_entry_id="test_entry_id")
        m.return_value = reg
        result = sensor._get_energy_sensor_persisted_state_from_coordinator()
        assert result == persisted
        coordinator.get_energy_sensor_persisted_state.assert_called_once_with(sensor.entity_id)


# --- native_value Rundung (2 Dezimalstellen) ---


def test_native_value_rounded_to_two_decimals_daily(mock_hass, mock_entry):
    """Daily native_value wird auf 2 Dezimalstellen gerundet (vermeidet 0.39999… im Restore)."""
    sensor = _daily_sensor(mock_hass, mock_entry)
    sensor._energy_value = 212.73
    sensor._yesterday_value = 212.33
    # 212.73 - 212.33 = 0.40 (evtl. Float 0.39999...)
    val = sensor.native_value
    assert isinstance(val, float)
    assert round(val, 2) == 0.40
    assert val == round(val, 2)


def test_native_value_rounded_total(mock_hass, mock_entry):
    """Total native_value wird auf 2 Dezimalstellen gerundet."""
    sensor = _total_sensor(mock_hass, mock_entry)
    sensor._energy_value = 220.844444
    assert sensor.native_value == 220.84
