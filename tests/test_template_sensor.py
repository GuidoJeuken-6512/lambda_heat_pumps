"""Tests für template_sensor.py - insbesondere die Issue-#107-Regression:

template_sensor.py rekonstruierte die entity_ids seiner Quell-Entities
(Außentemperatur, Heizkurven-Stützpunkte, operating_state, eco_temp_reduction,
sowie generische Template-Referenzen wie beim COP-Template) aus dem Gerätenamen,
statt sie über die stabile unique_id in der Entity Registry aufzulösen. Bei einer
zweiten Wärmepumpe/einem zweiten Heizkreis mit abweichender entity_id (oder einer
vom Nutzer umbenannten Entity) fanden diese Lookups ihre Ziel-Entities nie -
Symptom: berechneter COP dauerhaft 0.0, Heizkurve rechnet mit den eingebauten
Default-Stützpunkten statt den konfigurierten, ECO-Absenkung greift nie.

Live in einer Docker-Testinstanz verifiziert (V2.8.3), hier als automatisierter
Regressionsschutz nachgezogen.
"""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from custom_components.lambda_heat_pumps.template_sensor import (
    LambdaHeatingCurveCalcSensor,
    async_setup_entry,
)
from tests.conftest import DummyLoop


# ---------------------------------------------------------------------------
# LambdaHeatingCurveCalcSensor - direkte Konstruktion + async_added_to_hass
# ---------------------------------------------------------------------------


def _make_heating_curve_sensor(hass, entry, name="Lambda_EU10L", legacy=True):
    coordinator = Mock()
    return LambdaHeatingCurveCalcSensor(
        coordinator=coordinator,
        entry=entry,
        sensor_id="hc2_heating_curve_flow_line_temperature_calc",
        name="Heizkurve Vorlauf ber.",
        unit="°C",
        state_class="measurement",
        device_class=None,
        device_type="hc",
        precision=1,
        entity_id="sensor.lambdaeu10l_hc2_heating_curve_flow_line_temperature_calc",
        unique_id="lambda_eu10l_hc2_heating_curve_flow_line_temperature_calc",
        ambient_sensor="sensor.lambda_eu10l_ambient_temperature_calculated",
        number_entities={
            "heating_curve_cold_outside_temp": "number.lambda_eu10l_hc2_heating_curve_cold_outside_temp",
            "heating_curve_mid_outside_temp": "number.lambda_eu10l_hc2_heating_curve_mid_outside_temp",
            "heating_curve_warm_outside_temp": "number.lambda_eu10l_hc2_heating_curve_warm_outside_temp",
        },
        temp_points={"cold": -22.0, "mid": 0.0, "warm": 22.0},
        defaults={
            "heating_curve_cold_outside_temp": 48.3,
            "heating_curve_mid_outside_temp": 39.0,
            "heating_curve_warm_outside_temp": 32.0,
        },
        room_thermostat_enabled=False,
    )


@pytest.fixture
def mock_hass():
    hass = Mock()
    hass.config = Mock()
    hass.config.config_dir = "/tmp/test_config"
    hass.config.language = "en"
    hass.config.locale = SimpleNamespace(language="en")
    hass.data = {}
    hass.states = Mock()
    hass.states.get = Mock(return_value=None)
    hass.loop = DummyLoop()
    return hass


@pytest.fixture
def mock_entry():
    entry = Mock()
    entry.entry_id = "test_entry"
    entry.data = {
        "name": "Lambda_EU10L",
        "use_legacy_modbus_names": True,
    }
    entry.options = {}
    return entry


class TestHeatingCurveSensorInitFallback:
    """__init__() setzt zunächst nur die namensbasierte Fallback-Form - das
    Verhalten von vor v2.8.3, unverändert, da self.hass dort noch nicht
    verfügbar ist."""

    def test_init_uses_namebased_fallback_for_underscore_device_name(
        self, mock_hass, mock_entry
    ):
        sensor = _make_heating_curve_sensor(mock_hass, mock_entry)

        # "Lambda_EU10L" -> normalize_name_prefix() -> "lambda_eu10l" (Unterstrich bleibt)
        assert sensor._operating_state_entity == "sensor.lambda_eu10l_hc2_operating_state"
        assert sensor._eco_temp_reduction_entity == "number.lambda_eu10l_hc2_eco_temp_reduction"
        assert sensor._source_device_prefix == "hc2"


class TestHeatingCurveSensorRegistryResolutionIssue107:
    """Regressionstests für async_added_to_hass(): operating_state/eco_temp_reduction
    müssen über die Entity Registry aufgelöst werden, sobald self.hass verfügbar ist -
    nicht dauerhaft bei der namensbasierten __init__-Fallback-Form bleiben.
    """

    @pytest.mark.asyncio
    async def test_resolves_operating_state_via_registry_when_entity_id_diverges(
        self, mock_hass, mock_entry
    ):
        """Die real registrierte entity_id (z.B. "lambdaeu10l_..." ohne Unterstrich,
        weil unter einer älteren Version angelegt) muss verwendet werden, nicht die
        aus dem aktuellen Gerätenamen rekonstruierte Form.
        """
        sensor = _make_heating_curve_sensor(mock_hass, mock_entry)
        sensor.hass = mock_hass
        sensor.async_write_ha_state = Mock()

        real_operating_state_id = "sensor.lambdaeu10l_hc2_operating_state"

        def fake_get_entity_id(domain, platform, unique_id):
            if unique_id == "lambda_eu10l_hc2_operating_state":
                return real_operating_state_id
            return None

        mock_registry = Mock()
        mock_registry.async_get_entity_id = Mock(side_effect=fake_get_entity_id)

        with patch(
            "custom_components.lambda_heat_pumps.template_sensor.async_get_entity_registry",
            return_value=mock_registry,
        ):
            await sensor.async_added_to_hass()

        assert sensor._operating_state_entity == real_operating_state_id, (
            "operating_state muss ueber die Registry aufgeloest werden statt bei der "
            "namensbasierten __init__-Fallback-Form ('sensor.lambda_eu10l_hc2_operating_state') "
            "zu bleiben - genau das war Issue #107 fuer template_sensor.py."
        )
        assert real_operating_state_id in sensor._track_entities

    @pytest.mark.asyncio
    async def test_resolves_eco_temp_reduction_via_registry_with_number_suffix(
        self, mock_hass, mock_entry
    ):
        """eco_temp_reduction liegt in der number-Domain; number.py haengt "_number"
        an die unique_id an - das muss beim Lookup beruecksichtigt werden."""
        sensor = _make_heating_curve_sensor(mock_hass, mock_entry)
        sensor.hass = mock_hass
        sensor.async_write_ha_state = Mock()

        real_eco_id = "number.lambdaeu10l_hc2_eco_temp_reduction"

        def fake_get_entity_id(domain, platform, unique_id):
            if domain == "number" and unique_id == "lambda_eu10l_hc2_eco_temp_reduction_number":
                return real_eco_id
            return None

        mock_registry = Mock()
        mock_registry.async_get_entity_id = Mock(side_effect=fake_get_entity_id)

        with patch(
            "custom_components.lambda_heat_pumps.template_sensor.async_get_entity_registry",
            return_value=mock_registry,
        ):
            await sensor.async_added_to_hass()

        assert sensor._eco_temp_reduction_entity == real_eco_id
        mock_registry.async_get_entity_id.assert_any_call(
            "number", "lambda_heat_pumps", "lambda_eu10l_hc2_eco_temp_reduction_number"
        )

    @pytest.mark.asyncio
    async def test_falls_back_to_namebased_form_when_not_yet_in_registry(
        self, mock_hass, mock_entry
    ):
        """Erster Zyklus nach Neuanlage: Registry kennt die Entity noch nicht -
        Verhalten muss exakt der bisherigen namensbasierten Form entsprechen
        (kein Regressionsrisiko fuer Bestandsnutzer ohne Sonderzeichen)."""
        sensor = _make_heating_curve_sensor(mock_hass, mock_entry)
        sensor.hass = mock_hass
        sensor.async_write_ha_state = Mock()

        mock_registry = Mock()
        mock_registry.async_get_entity_id = Mock(return_value=None)

        with patch(
            "custom_components.lambda_heat_pumps.template_sensor.async_get_entity_registry",
            return_value=mock_registry,
        ):
            await sensor.async_added_to_hass()

        assert sensor._operating_state_entity == "sensor.lambda_eu10l_hc2_operating_state"
        assert sensor._eco_temp_reduction_entity == "number.lambda_eu10l_hc2_eco_temp_reduction"


# ---------------------------------------------------------------------------
# async_setup_entry() - Verdrahtung von resolve_sensor_entity_id() /
# resolve_template_entity_ids() beim Erzeugen der Sensoren
# ---------------------------------------------------------------------------


class TestTemplateSensorSetupEntryRegistryLookupIssue107:
    """Regressionstests: async_setup_entry() muss die Quell-entity_ids der
    Heizkurven-Sensoren (Außentemperatur, Stützpunkte) sowie die im COP-Template
    referenzierten Nachbar-Entities ueber die Registry aufloesen, statt den rohen
    generate_sensor_names()-Text zu verwenden.
    """

    @pytest.fixture
    def setup_entry(self, mock_entry):
        mock_entry.data = {
            "name": "eu08l",
            "use_legacy_modbus_names": True,
            "firmware_version": "V0.0.3-3K",
            "num_hps": 1,
            "num_boil": 1,
            "num_buff": 0,
            "num_sol": 0,
            "num_hc": 1,
        }
        return mock_entry

    @pytest.mark.asyncio
    async def test_heating_curve_ambient_and_number_entities_resolved_via_registry(
        self, mock_hass, setup_entry
    ):
        from custom_components.lambda_heat_pumps.const import DOMAIN

        mock_coordinator = Mock()
        mock_hass.data[DOMAIN] = {setup_entry.entry_id: {"coordinator": mock_coordinator}}
        # Cache vorbelegen, damit load_lambda_config() nicht auf Datei-I/O
        # (hass.async_add_executor_job) zugreift - hass ist hier ein reiner Mock.
        mock_hass.data["_lambda_config_cache"] = {
            "disabled_registers": set(),
            "sensors_names_override": {},
            "cycling_offsets": {},
            "energy_consumption_sensors": {},
            "energy_consumption_offsets": {},
            "modbus": {},
        }
        mock_add_entities = Mock()

        real_ambient_id = "sensor.custom_renamed_ambient_temperature_calculated"
        real_mid_id = "number.eu08l_hc1_custom_heating_curve_mid_outside_temp"

        def fake_get_entity_id(domain, platform, unique_id):
            if domain == "sensor" and unique_id == "eu08l_ambient_temperature_calculated":
                return real_ambient_id
            if domain == "number" and unique_id == "eu08l_hc1_heating_curve_mid_outside_temp_number":
                return real_mid_id
            return None  # cold/warm-Stuetzpunkte: (noch) nicht in der Registry -> Fallback

        mock_registry = Mock()
        mock_registry.async_get_entity_id = Mock(side_effect=fake_get_entity_id)

        captured = []

        def heating_curve_side_effect(**kwargs):
            captured.append(kwargs)
            return Mock()

        with patch(
            "custom_components.lambda_heat_pumps.template_sensor.LambdaHeatingCurveCalcSensor",
            side_effect=heating_curve_side_effect,
        ), patch(
            "custom_components.lambda_heat_pumps.template_sensor.async_get_entity_registry",
            return_value=mock_registry,
        ):
            await async_setup_entry(mock_hass, setup_entry, mock_add_entities)

        assert len(captured) == 1, f"Erwartet genau 1 Heizkurven-Sensor, bekam {len(captured)}"
        call_kwargs = captured[0]

        assert call_kwargs["ambient_sensor"] == real_ambient_id, (
            "Der Außentemperatur-Sensor muss ueber die Registry aufgeloest werden."
        )
        assert (
            call_kwargs["number_entities"]["heating_curve_mid_outside_temp"] == real_mid_id
        ), "Der mid-Stuetzpunkt muss ueber die Registry aufgeloest werden."
        # cold/warm nicht im (gemockten) Registry-Bestand -> selbstheilender Text-Fallback
        assert (
            call_kwargs["number_entities"]["heating_curve_cold_outside_temp"]
            == "number.eu08l_hc1_heating_curve_cold_outside_temp"
        )

    @pytest.mark.asyncio
    async def test_plain_template_source_entities_resolved_via_registry(
        self, mock_hass, setup_entry
    ):
        """COP-Berechnet-Template (cop_calc) referenziert zwei Nachbar-Sensoren via
        states(...); resolve_template_entity_ids() muss die real registrierte
        entity_id einsetzen, wenn sie von der generierten Form abweicht (Issue #107,
        hp2-Fall: berechneter COP blieb bei 0.0)."""
        from custom_components.lambda_heat_pumps.const import DOMAIN

        mock_coordinator = Mock()
        mock_hass.data[DOMAIN] = {setup_entry.entry_id: {"coordinator": mock_coordinator}}
        # Cache vorbelegen, damit load_lambda_config() nicht auf Datei-I/O
        # (hass.async_add_executor_job) zugreift - hass ist hier ein reiner Mock.
        mock_hass.data["_lambda_config_cache"] = {
            "disabled_registers": set(),
            "sensors_names_override": {},
            "cycling_offsets": {},
            "energy_consumption_sensors": {},
            "energy_consumption_offsets": {},
            "modbus": {},
        }
        mock_add_entities = Mock()

        real_thermal_id = "sensor.custom_hp1_compressor_thermal_energy_output_accumulated"

        def fake_get_entity_id(domain, platform, unique_id):
            if unique_id == "eu08l_hp1_compressor_thermal_energy_output_accumulated":
                return real_thermal_id
            return None

        mock_registry = Mock()
        mock_registry.async_get_entity_id = Mock(side_effect=fake_get_entity_id)

        captured = []

        def template_sensor_side_effect(**kwargs):
            captured.append(kwargs)
            return Mock()

        with patch(
            "custom_components.lambda_heat_pumps.template_sensor.LambdaTemplateSensor",
            side_effect=template_sensor_side_effect,
        ), patch(
            "custom_components.lambda_heat_pumps.template_sensor.async_get_entity_registry",
            return_value=mock_registry,
        ):
            await async_setup_entry(mock_hass, setup_entry, mock_add_entities)

        cop_calls = [c for c in captured if c.get("sensor_id") == "hp1_cop_calc"]
        assert len(cop_calls) == 1, f"Erwartet genau 1 cop_calc-Template-Sensor, bekam {len(cop_calls)}"
        template_str = cop_calls[0]["template_str"]

        assert f"states('{real_thermal_id}')" in template_str, (
            "Das Template muss die registry-aufgeloeste entity_id fuer den thermischen "
            f"Quell-Sensor enthalten, nicht die rekonstruierte Form. Template: {template_str}"
        )
        # Elektrischer Quell-Sensor (noch) nicht im gemockten Registry-Bestand -> Fallback
        assert (
            "states('sensor.eu08l_hp1_compressor_power_consumption_accumulated')"
            in template_str
        )
