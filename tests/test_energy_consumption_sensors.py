"""Test Energy Consumption Sensor functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from types import SimpleNamespace
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

from custom_components.lambda_heat_pumps.sensor import LambdaEnergyConsumptionSensor
from custom_components.lambda_heat_pumps.const import (
    ENERGY_CONSUMPTION_SENSOR_TEMPLATES,
    ENERGY_CONSUMPTION_MODES,
    ENERGY_CONSUMPTION_PERIODS,
)
from tests.conftest import DummyLoop



class TestLambdaEnergyConsumptionSensor:
    def test_thermal_sensor_creation_for_all_modes_and_periods(self, mock_hass, mock_entry):
        """Test creation and properties of all thermal energy sensors (all modes/periods)."""
        sensors = []
        # Only test templates with data_type == 'thermal_calculated'
        for sensor_id, template in ENERGY_CONSUMPTION_SENSOR_TEMPLATES.items():
            if template.get("data_type") == "thermal_calculated":
                # Parse mode and period from sensor_id
                # Thermal sensors have pattern: {mode}_thermal_energy_{period}
                if "_thermal_energy_" in sensor_id:
                    parts = sensor_id.split("_thermal_energy_")
                    if len(parts) != 2:
                        continue
                    mode, period = parts[0], parts[1]
                else:
                    # Fallback: try regular pattern (should not happen for thermal)
                    parts = sensor_id.split("_energy_")
                    if len(parts) != 2:
                        continue
                    mode, period = parts[0], parts[1]
                
                sensor = LambdaEnergyConsumptionSensor(
                    hass=mock_hass,
                    entry=mock_entry,
                    sensor_id=sensor_id,
                    name=template["name"],
                    entity_id=f"sensor.eu08l_hp1_{sensor_id}",
                    unique_id=f"eu08l_hp1_{sensor_id}",
                    unit=template["unit"],
                    state_class=template["state_class"],
                    device_class=template.get("device_class"),
                    device_type=template["device_type"],
                    hp_index=1,
                    mode=mode,
                    period=period,
                )
                sensors.append(sensor)
                # Verify sensor properties
                assert sensor._mode == mode
                assert sensor._period == period
                assert sensor._unit == "kWh"
                # For thermal, device_class should be ENERGY
                assert sensor._device_class == SensorDeviceClass.ENERGY
                assert sensor.entity_id == f"sensor.eu08l_hp1_{sensor_id}"
                assert sensor._sensor_id == sensor_id
                
                # Verify state_class based on period
                if period == "total":
                    assert sensor._attr_state_class == SensorStateClass.TOTAL_INCREASING
                else:
                    assert sensor._attr_state_class == SensorStateClass.TOTAL
                    
        # There should be as many sensors as there are thermal_calculated templates
        expected_count = len([t for t in ENERGY_CONSUMPTION_SENSOR_TEMPLATES.values() if t.get("data_type") == "thermal_calculated"])
        assert len(sensors) == expected_count, f"Expected {expected_count} thermal sensors, but created {len(sensors)}"

    @pytest.fixture
    def mock_hass(self):
        """Mock Home Assistant instance."""
        from unittest.mock import MagicMock
        hass = MagicMock()
        hass.states = MagicMock()
        hass.data = {'integrations': {}, 'customize': {}}  # Add integrations for async_write_ha_state
        hass.async_create_task = MagicMock()
        hass.config = MagicMock()
        hass.config.language = "en"
        hass.config.locale = SimpleNamespace(language="en")
        hass.loop = DummyLoop()
        return hass

    @pytest.fixture
    def mock_entry(self):
        """Mock ConfigEntry instance."""
        entry = Mock()
        entry.entry_id = "test_entry_id"
        entry.data = {
            "name": "eu08l",
            "host": "192.168.1.100",
            "port": 502,
        }
        return entry

    @pytest.fixture
    def energy_sensor(self, mock_hass, mock_entry):
        """Create a LambdaEnergyConsumptionSensor instance."""
        return LambdaEnergyConsumptionSensor(
            hass=mock_hass,
            entry=mock_entry,
            sensor_id="heating_energy_total",
            name="Heating Energy Total",
            entity_id="sensor.eu08l_hp1_heating_energy_total",
            unique_id="eu08l_hp1_heating_energy_total",
            unit="kWh",
            state_class="total_increasing",
            device_class=SensorDeviceClass.ENERGY,
            device_type="hp",
            hp_index=1,
            mode="heating",
            period="total",
        )

    def test_sensor_initialization(self, energy_sensor):
        """Test sensor initialization."""
        assert energy_sensor._sensor_id == "heating_energy_total"
        assert energy_sensor._name == "Heating Energy Total"
        assert energy_sensor.entity_id == "sensor.eu08l_hp1_heating_energy_total"
        assert energy_sensor._unique_id == "eu08l_hp1_heating_energy_total"
        assert energy_sensor._unit == "kWh"
        assert energy_sensor._hp_index == 1
        assert energy_sensor._mode == "heating"
        assert energy_sensor._period == "total"
        assert energy_sensor._energy_value == 0.0
        assert energy_sensor._yesterday_value == 0.0

    def test_sensor_properties(self, energy_sensor):
        """Test sensor properties."""
        assert energy_sensor._attr_native_unit_of_measurement == "kWh"
        assert energy_sensor._attr_name == "Heating Energy Total"
        assert energy_sensor._attr_unique_id == "eu08l_hp1_heating_energy_total"
        assert energy_sensor._attr_device_class == SensorDeviceClass.ENERGY
        assert energy_sensor._attr_state_class == SensorStateClass.TOTAL_INCREASING
        assert energy_sensor._attr_has_entity_name is True
        assert energy_sensor._attr_should_poll is False

    def test_set_energy_value(self, energy_sensor, mock_hass):
        """Test setting energy value."""
        from unittest.mock import patch, MagicMock
        # Patch async_write_ha_state to avoid integration issues
        with patch.object(energy_sensor, 'async_write_ha_state', new_callable=MagicMock):
            test_value = 123.45
            
            energy_sensor.set_energy_value(test_value)
            
            assert energy_sensor._energy_value == test_value

    def test_set_energy_value_string_conversion(self, energy_sensor, mock_hass):
        """Test setting energy value with string input."""
        from unittest.mock import patch, MagicMock
        # Patch async_write_ha_state to avoid integration issues
        with patch.object(energy_sensor, 'async_write_ha_state', new_callable=MagicMock):
            test_value = "123.45"
            expected_value = 123.45
            
            energy_sensor.set_energy_value(test_value)
            
            assert energy_sensor._energy_value == expected_value

    def test_update_yesterday_value(self, energy_sensor):
        """Test updating yesterday value."""
        energy_sensor._energy_value = 100.0
        energy_sensor._yesterday_value = 50.0
        
        energy_sensor.update_yesterday_value()
        
        assert energy_sensor._yesterday_value == 100.0

    def test_native_value_total(self, energy_sensor):
        """Test native value for total period."""
        energy_sensor._energy_value = 100.0
        energy_sensor._yesterday_value = 50.0
        
        result = energy_sensor.native_value
        
        assert result == 100.0

    def test_native_value_daily(self, energy_sensor):
        """Test native value for daily period."""
        # Change period to daily
        energy_sensor._period = "daily"
        energy_sensor._energy_value = 100.0
        energy_sensor._yesterday_value = 50.0
        
        result = energy_sensor.native_value
        
        assert result == 50.0  # Total - Yesterday

    def test_native_value_daily_negative_result(self, energy_sensor):
        """Test native value for daily period with negative result."""
        # Change period to daily
        energy_sensor._period = "daily"
        energy_sensor._energy_value = 30.0
        energy_sensor._yesterday_value = 50.0
        
        result = energy_sensor.native_value
        
        assert result == 0.0  # Should be clamped to 0

    def test_extra_state_attributes(self, energy_sensor):
        """Test extra state attributes."""
        attrs = energy_sensor.extra_state_attributes
        
        assert attrs["sensor_type"] == "energy_consumption"
        assert attrs["mode"] == "heating"
        assert attrs["period"] == "total"
        assert attrs["hp_index"] == 1

    def test_extra_state_attributes_with_offset(self, energy_sensor):
        """Test extra state attributes with applied offset."""
        energy_sensor._applied_offset = 100.0
        attrs = energy_sensor.extra_state_attributes
        
        assert attrs["applied_offset"] == 100.0

    def test_extra_state_attributes_daily_sensor(self, energy_sensor):
        """Test extra state attributes for daily sensor."""
        energy_sensor._period = "daily"
        attrs = energy_sensor.extra_state_attributes
        
        assert attrs["period"] == "daily"
        assert "applied_offset" in attrs  # Daily sensors also have offsets now

    @pytest.mark.asyncio
    async def test_async_added_to_hass(self, mock_hass, mock_entry):
        """Test async_added_to_hass method."""
        from unittest.mock import patch, MagicMock
        # Create a daily sensor (total sensors don't register dispatcher)
        daily_sensor = LambdaEnergyConsumptionSensor(
            hass=mock_hass,
            entry=mock_entry,
            sensor_id="heating_energy_daily",
            name="Heating Energy Daily",
            entity_id="sensor.eu08l_hp1_heating_energy_daily",
            unique_id="eu08l_hp1_heating_energy_daily",
            unit="kWh",
            state_class="total",
            device_class=SensorDeviceClass.ENERGY,
            device_type="hp",
            hp_index=1,
            mode="heating",
            period="daily",
        )
        
        # Mock last state (attributes als echtes Dict, sonst float(attrs.get(...)) → Mock)
        last_state = Mock()
        last_state.state = "50.0"
        last_state.attributes = {"applied_offset": 0.0}
        daily_sensor.async_get_last_state = AsyncMock(return_value=last_state)
        # Total-Sensor nicht verfügbar → Restore rekonstruiert _energy_value = yesterday + 50 = 50
        daily_sensor.hass.states.get = Mock(return_value=None)

        # Patch async_write_ha_state to avoid integration issues
        with patch.object(daily_sensor, 'async_write_ha_state', new_callable=MagicMock):
            # Mock dispatcher connect + Coordinator (kein Persist-State)
            with patch('custom_components.lambda_heat_pumps.sensor.async_dispatcher_connect') as mock_connect:
                with patch.object(daily_sensor, '_get_energy_sensor_persisted_state_from_coordinator', return_value=None):
                    await daily_sensor.async_added_to_hass()
            
            # Verify dispatcher was connected (daily sensors register for reset signals)
            mock_connect.assert_called_once()
            
            # Verify restore_state: ohne Total → _energy_value = yesterday + displayed = 0 + 50
            assert daily_sensor._energy_value == 50.0

    @pytest.mark.asyncio
    async def test_async_added_to_hass_no_last_state(self, energy_sensor):
        """Test async_added_to_hass method with no last state."""
        from unittest.mock import patch, MagicMock
        energy_sensor.async_get_last_state = AsyncMock(return_value=None)
        
        # Patch async_write_ha_state to avoid integration issues
        with patch.object(energy_sensor, 'async_write_ha_state', new_callable=MagicMock):
            with patch('custom_components.lambda_heat_pumps.sensor.async_dispatcher_connect'):
                await energy_sensor.async_added_to_hass()
            
            # Verify default value
            assert energy_sensor._energy_value == 0.0

    @pytest.mark.asyncio
    async def test_async_added_to_hass_invalid_last_state(self, energy_sensor):
        """Test async_added_to_hass method with invalid last state."""
        from unittest.mock import patch, MagicMock
        last_state = Mock()
        last_state.state = "invalid"
        last_state.attributes = {"applied_offset": 0.0}
        energy_sensor.async_get_last_state = AsyncMock(return_value=last_state)
        
        # Patch async_write_ha_state to avoid integration issues
        with patch.object(energy_sensor, 'async_write_ha_state', new_callable=MagicMock):
            with patch('custom_components.lambda_heat_pumps.sensor.async_dispatcher_connect'):
                await energy_sensor.async_added_to_hass()
            
            # Verify default value due to invalid state
            assert energy_sensor._energy_value == 0.0

    @pytest.mark.asyncio
    async def test_async_will_remove_from_hass(self, energy_sensor):
        """Test async_will_remove_from_hass method."""
        # Mock unsub dispatcher
        mock_unsub = Mock()
        energy_sensor._unsub_dispatcher = mock_unsub
        
        await energy_sensor.async_will_remove_from_hass()
        
        # Verify unsub was called
        mock_unsub.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_will_remove_from_hass_no_unsub(self, energy_sensor):
        """Test async_will_remove_from_hass method with no unsub."""
        energy_sensor._unsub_dispatcher = None
        
        # Should not raise an exception
        await energy_sensor.async_will_remove_from_hass()

    @pytest.mark.asyncio
    async def test_handle_reset_total(self, energy_sensor, mock_entry):
        """Total-Sensor: _handle_reset ändert _energy_value nicht."""
        energy_sensor._energy_value = 100.0
        await energy_sensor._handle_reset(mock_entry.entry_id)
        assert energy_sensor._energy_value == 100.0

    @pytest.mark.asyncio
    async def test_handle_reset_daily_updates_yesterday_not_energy(self, mock_hass, mock_entry):
        """Daily-Sensor: Reset setzt yesterday_value = Total und synchronisiert _energy_value mit Total."""
        from unittest.mock import MagicMock
        sensor = LambdaEnergyConsumptionSensor(
            hass=mock_hass,
            entry=mock_entry,
            sensor_id="heating_energy_daily",
            name="Heating Energy Daily",
            entity_id="sensor.eu08l_hp1_heating_energy_daily",
            unique_id="eu08l_hp1_heating_energy_daily",
            unit="kWh",
            state_class="total",
            device_class=SensorDeviceClass.ENERGY,
            device_type="hp",
            hp_index=1,
            mode="heating",
            period="daily",
        )
        sensor._energy_value = 500.0
        sensor._yesterday_value = 100.0
        total_state = MagicMock()
        total_state.state = "500.0"
        total_state.attributes = {}
        mock_hass.states.get = MagicMock(return_value=total_state)
        with patch.object(sensor, "async_write_ha_state", MagicMock()):
            await sensor._handle_reset(mock_entry.entry_id)
        assert sensor._energy_value == 500.0, "Daily reset synchronisiert _energy_value mit Total"
        assert sensor._yesterday_value == 500.0, "yesterday_value soll auf Total gesetzt werden"

    @pytest.mark.asyncio
    async def test_handle_reset_monthly_updates_previous_monthly_not_energy(self, mock_hass, mock_entry):
        """Monthly-Sensor: Reset setzt previous_monthly_value = Total und synchronisiert _energy_value mit Total."""
        from unittest.mock import MagicMock, patch
        sensor = LambdaEnergyConsumptionSensor(
            hass=mock_hass,
            entry=mock_entry,
            sensor_id="heating_energy_monthly",
            name="Heating Energy Monthly",
            entity_id="sensor.eu08l_hp1_heating_energy_monthly",
            unique_id="eu08l_hp1_heating_energy_monthly",
            unit="kWh",
            state_class="total",
            device_class=SensorDeviceClass.ENERGY,
            device_type="hp",
            hp_index=1,
            mode="heating",
            period="monthly",
        )
        sensor._energy_value = 2000.0
        sensor._previous_monthly_value = 500.0
        total_state = MagicMock()
        total_state.state = "2000.0"
        total_state.attributes = {}
        mock_hass.states.get = MagicMock(return_value=total_state)
        with patch.object(sensor, "async_write_ha_state", MagicMock()):
            await sensor._handle_reset(mock_entry.entry_id)
        assert sensor._energy_value == 2000.0, "Monthly reset synchronisiert _energy_value mit Total"
        assert sensor._previous_monthly_value == 2000.0, "previous_monthly_value soll auf Total gesetzt werden"

    @pytest.mark.asyncio
    async def test_handle_reset_yearly_updates_previous_yearly_not_energy(self, mock_hass, mock_entry):
        """Yearly-Sensor: Reset setzt previous_yearly_value = Total und synchronisiert _energy_value mit Total."""
        from unittest.mock import MagicMock, patch
        sensor = LambdaEnergyConsumptionSensor(
            hass=mock_hass,
            entry=mock_entry,
            sensor_id="heating_energy_yearly",
            name="Heating Energy Yearly",
            entity_id="sensor.eu08l_hp1_heating_energy_yearly",
            unique_id="eu08l_hp1_heating_energy_yearly",
            unit="kWh",
            state_class="total",
            device_class=SensorDeviceClass.ENERGY,
            device_type="hp",
            hp_index=1,
            mode="heating",
            period="yearly",
        )
        sensor._energy_value = 10000.0
        sensor._previous_yearly_value = 2000.0
        total_state = MagicMock()
        total_state.state = "10000.0"
        total_state.attributes = {}
        mock_hass.states.get = MagicMock(return_value=total_state)
        with patch.object(sensor, "async_write_ha_state", MagicMock()):
            await sensor._handle_reset(mock_entry.entry_id)
        assert sensor._energy_value == 10000.0, "Yearly reset synchronisiert _energy_value mit Total"
        assert sensor._previous_yearly_value == 10000.0, "previous_yearly_value soll auf Total gesetzt werden"

    @pytest.mark.asyncio
    async def test_day_change_simulation_daily_reset_then_increment(self, mock_hass, mock_entry):
        """Tageswechsel simulieren: Vor Mitternacht → Reset → Nach Mitternacht Inkrement.
        Stellt sicher, dass Daily-Sensoren nach dem Reset wieder korrekt aktualisiert werden
        (yesterday_value = Total, Anzeige 0; danach Inkrement erhöht Tageswert).
        """
        from unittest.mock import MagicMock
        # Daily-Sensor (Heizung, Tageswert)
        daily_sensor = LambdaEnergyConsumptionSensor(
            hass=mock_hass,
            entry=mock_entry,
            sensor_id="heating_energy_daily",
            name="Heating Energy Daily",
            entity_id="sensor.eu08l_hp1_heating_energy_daily",
            unique_id="eu08l_hp1_heating_energy_daily",
            unit="kWh",
            state_class="total",
            device_class=SensorDeviceClass.ENERGY,
            device_type="hp",
            hp_index=1,
            mode="heating",
            period="daily",
        )
        # Total-Sensor-State mocken (wird bei Reset für yesterday_value gelesen)
        total_state = MagicMock()
        total_state.state = "100.0"
        total_state.attributes = {}
        mock_hass.states.get = MagicMock(return_value=total_state)

        with patch.object(daily_sensor, "async_write_ha_state", MagicMock()):
            # —— Vor Mitternacht: Tageswert 100 kWh (Total 100, yesterday 0)
            daily_sensor._energy_value = 100.0
            daily_sensor._yesterday_value = 0.0
            assert daily_sensor.native_value == 100.0, "Vor Reset: Tageswert soll 100 kWh sein"

            # —— Mitternacht: Daily-Reset (Signal würde _handle_reset auslösen)
            await daily_sensor._handle_reset(mock_entry.entry_id)

            # Nach Reset: yesterday_value = Total, Anzeige = 0
            assert daily_sensor._yesterday_value == 100.0, (
                "Nach Reset: yesterday_value muss auf Total (100) gesetzt werden"
            )
            assert daily_sensor._energy_value == 100.0, (
                "Nach Reset: _energy_value wird mit Total synchronisiert (vom Coordinator weiter erhöht)"
            )
            assert daily_sensor.native_value == 0.0, (
                "Nach Reset: Tagesanzeige muss 0 sein (daily = _energy_value - yesterday_value)"
            )

            # —— Nach Mitternacht: Erstes Inkrement (Coordinator liefert 100.5 kWh)
            daily_sensor.set_energy_value(100.5)

            # Tageswert muss 0,5 kWh sein (100.5 - 100)
            assert daily_sensor._energy_value == 100.5
            assert daily_sensor.native_value == 0.5, (
                "Nach erstem Inkrement: Tageswert muss 0,5 kWh sein – "
                "wenn 0 bleibt, werden Daily-Sensoren nach Reset nicht aktualisiert (Bug)"
            )

    @pytest.mark.asyncio
    async def test_day_change_simulation_wrong_entry_id_ignored(self, mock_hass, mock_entry):
        """Tageswechsel: _handle_reset mit falscher entry_id ändert nichts (anderer Config-Eintrag)."""
        from unittest.mock import MagicMock
        daily_sensor = LambdaEnergyConsumptionSensor(
            hass=mock_hass,
            entry=mock_entry,
            sensor_id="heating_energy_daily",
            name="Heating Energy Daily",
            entity_id="sensor.eu08l_hp1_heating_energy_daily",
            unique_id="eu08l_hp1_heating_energy_daily",
            unit="kWh",
            state_class="total",
            device_class=SensorDeviceClass.ENERGY,
            device_type="hp",
            hp_index=1,
            mode="heating",
            period="daily",
        )
        daily_sensor._energy_value = 80.0
        daily_sensor._yesterday_value = 20.0
        with patch.object(daily_sensor, "async_write_ha_state", MagicMock()):
            await daily_sensor._handle_reset("other_entry_id")
        assert daily_sensor._yesterday_value == 20.0, "Falsche entry_id: yesterday_value unverändert"
        assert daily_sensor._energy_value == 80.0
        assert daily_sensor.native_value == 60.0

    def test_device_info(self, energy_sensor, mock_entry):
        """Test device info property."""
        # device_info calls build_subdevice_info (since hp_index is set)
        # or build_device_info (if no hp_index)
        result = energy_sensor.device_info
        
        # Verify it's a dict with expected keys
        assert isinstance(result, dict)
        assert "identifiers" in result
        assert "name" in result
        # Verify it's a subdevice (has hp_index)
        assert energy_sensor._hp_index == 1
        # The result should contain device identifiers
        assert len(result["identifiers"]) > 0

    def test_sensor_creation_for_all_modes_and_periods(self, mock_hass, mock_entry):
        """Test sensor creation for all modes and periods."""
        sensors = []
        
        for mode in ENERGY_CONSUMPTION_MODES:
            for period in ENERGY_CONSUMPTION_PERIODS:
                sensor_id = f"{mode}_energy_{period}"
                template = ENERGY_CONSUMPTION_SENSOR_TEMPLATES[sensor_id]
                
                sensor = LambdaEnergyConsumptionSensor(
                    hass=mock_hass,
                    entry=mock_entry,
                    sensor_id=sensor_id,
                    name=template["name"],
                    entity_id=f"sensor.eu08l_hp1_{sensor_id}",
                    unique_id=f"eu08l_hp1_{sensor_id}",
                    unit=template["unit"],
                    state_class=template["state_class"],
                    device_class=template.get("device_class"),
                    device_type=template["device_type"],
                    hp_index=1,
                    mode=mode,
                    period=period,
                )
                
                sensors.append(sensor)
                
                # Verify sensor properties
                assert sensor._mode == mode
                assert sensor._period == period
                assert sensor._unit == "kWh"
                assert sensor._device_class == SensorDeviceClass.ENERGY
        
        # Verify all sensors were created
        assert len(sensors) == len(ENERGY_CONSUMPTION_MODES) * len(ENERGY_CONSUMPTION_PERIODS)

    def test_sensor_state_class_mapping(self, mock_hass, mock_entry):
        """Test sensor state class mapping."""
        # Test total sensor
        total_sensor = LambdaEnergyConsumptionSensor(
            hass=mock_hass,
            entry=mock_entry,
            sensor_id="heating_energy_total",
            name="Heating Energy Total",
            entity_id="sensor.eu08l_hp1_heating_energy_total",
            unique_id="eu08l_hp1_heating_energy_total",
            unit="kWh",
            state_class="total_increasing",
            device_class=SensorDeviceClass.ENERGY,
            device_type="hp",
            hp_index=1,
            mode="heating",
            period="total",
        )
        
        assert total_sensor._attr_state_class == SensorStateClass.TOTAL_INCREASING
        
        # Test daily sensor
        daily_sensor = LambdaEnergyConsumptionSensor(
            hass=mock_hass,
            entry=mock_entry,
            sensor_id="heating_energy_daily",
            name="Heating Energy Daily",
            entity_id="sensor.eu08l_hp1_heating_energy_daily",
            unique_id="eu08l_hp1_heating_energy_daily",
            unit="kWh",
            state_class="total",
            device_class=SensorDeviceClass.ENERGY,
            device_type="hp",
            hp_index=1,
            mode="heating",
            period="daily",
        )
        
        assert daily_sensor._attr_state_class == SensorStateClass.TOTAL

    def test_sensor_initialization_with_different_state_classes(self, mock_hass, mock_entry):
        """Test sensor initialization with different state classes."""
        state_classes = ["total_increasing", "total", "measurement", "unknown"]
        expected_classes = [
            SensorStateClass.TOTAL_INCREASING,
            SensorStateClass.TOTAL,
            SensorStateClass.MEASUREMENT,
            None,
        ]
        
        for state_class, expected in zip(state_classes, expected_classes):
            sensor = LambdaEnergyConsumptionSensor(
                hass=mock_hass,
                entry=mock_entry,
                sensor_id="test_sensor",
                name="Test Sensor",
                entity_id="sensor.test_sensor",
                unique_id="test_sensor",
                unit="kWh",
                state_class=state_class,
                device_class=SensorDeviceClass.ENERGY,
                device_type="hp",
                hp_index=1,
                mode="heating",
                period="total",
            )
            
            assert sensor._attr_state_class == expected


@pytest.mark.asyncio
async def test_energy_consumption_offset_application(mock_hass, mock_entry):
    """Test that energy consumption offsets from lambda_wp_config.yaml are correctly applied to energy total sensors."""
    sensor = LambdaEnergyConsumptionSensor(
        hass=mock_hass,
        entry=mock_entry,
        sensor_id="heating_energy_total",
        name="Heating Energy Total",
        entity_id="sensor.test_hp1_heating_energy_total",
        unique_id="test_hp1_heating_energy_total",
        unit="kWh",
        state_class="total_increasing",
        device_class=SensorDeviceClass.ENERGY,
        device_type="hp",
        hp_index=1,
        mode="heating",
        period="total",
    )
    
    sensor.async_write_ha_state = Mock()
    
    # Mock load_lambda_config to return energy consumption offsets from config
    mock_config = {
        "energy_consumption_offsets": {
            "hp1": {
                "heating_energy_total": 150.5,  # Offset from config (kWh)
                "hot_water_energy_total": 0.0,
                "cooling_energy_total": 0.0,
                "defrost_energy_total": 0.0,
            }
        }
    }
    
    # Create a mock last_state with initial value
    mock_last_state = Mock()
    mock_last_state.state = "50.0"  # Initial value from previous state
    mock_last_state.attributes = {"applied_offset": 0.0}  # No offset applied yet
    
    # First restore state
    await sensor.restore_state(mock_last_state)
    
    with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value=mock_config):
        # Call _apply_energy_offset directly (not called automatically in restore_state)
        await sensor._apply_energy_offset()
        
        # Verify offset was applied: restored value (50.0) + offset (150.5) = 200.5
        assert sensor._energy_value == 200.5
        assert sensor._applied_offset == 150.5
        sensor.async_write_ha_state.assert_called()


@pytest.mark.asyncio
async def test_energy_consumption_offset_no_config(mock_hass, mock_entry):
    """Test that energy sensor works correctly when no offsets are configured."""
    sensor = LambdaEnergyConsumptionSensor(
        hass=mock_hass,
        entry=mock_entry,
        sensor_id="heating_energy_total",
        name="Heating Energy Total",
        entity_id="sensor.test_hp1_heating_energy_total",
        unique_id="test_hp1_heating_energy_total",
        unit="kWh",
        state_class="total_increasing",
        device_class=SensorDeviceClass.ENERGY,
        device_type="hp",
        hp_index=1,
        mode="heating",
        period="total",
    )
    
    sensor.async_write_ha_state = Mock()
    
    # Mock config with no energy_consumption_offsets
    mock_config = {}
    
    # Create a mock last_state with initial value
    mock_last_state = Mock()
    mock_last_state.state = "50.0"
    mock_last_state.attributes = {"applied_offset": 0.0}
    
    # First restore state
    await sensor.restore_state(mock_last_state)
    
    with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value=mock_config):
        # Call _apply_energy_offset directly (not called automatically in restore_state)
        await sensor._apply_energy_offset()
        
        # Value should remain unchanged when no offset configured
        assert sensor._energy_value == 50.0
        assert sensor._applied_offset == 0.0


@pytest.mark.asyncio
async def test_energy_consumption_offset_multiple_hps(mock_hass, mock_entry):
    """Test that energy offsets are correctly applied for different heat pumps (hp1, hp2)."""
    # HP1 sensor
    sensor_hp1 = LambdaEnergyConsumptionSensor(
        hass=mock_hass,
        entry=mock_entry,
        sensor_id="heating_energy_total",
        name="Heating Energy Total HP1",
        entity_id="sensor.test_hp1_heating_energy_total",
        unique_id="test_hp1_heating_energy_total",
        unit="kWh",
        state_class="total_increasing",
        device_class=SensorDeviceClass.ENERGY,
        device_type="hp",
        hp_index=1,
        mode="heating",
        period="total",
    )
    
    sensor_hp1.async_write_ha_state = Mock()
    
    # HP2 sensor
    sensor_hp2 = LambdaEnergyConsumptionSensor(
        hass=mock_hass,
        entry=mock_entry,
        sensor_id="heating_energy_total",
        name="Heating Energy Total HP2",
        entity_id="sensor.test_hp2_heating_energy_total",
        unique_id="test_hp2_heating_energy_total",
        unit="kWh",
        state_class="total_increasing",
        device_class=SensorDeviceClass.ENERGY,
        device_type="hp",
        hp_index=2,
        mode="heating",
        period="total",
    )
    
    sensor_hp2.async_write_ha_state = Mock()
    
    # Mock config with offsets for both HPs
    mock_config = {
        "energy_consumption_offsets": {
            "hp1": {
                "heating_energy_total": 150.5,
            },
            "hp2": {
                "heating_energy_total": 300.25,
            }
        }
    }
    
    # Create mock last_states for both sensors
    mock_last_state_hp1 = Mock()
    mock_last_state_hp1.state = "100.0"
    mock_last_state_hp1.attributes = {"applied_offset": 0.0}
    
    mock_last_state_hp2 = Mock()
    mock_last_state_hp2.state = "200.0"
    mock_last_state_hp2.attributes = {"applied_offset": 0.0}
    
    # First restore states
    await sensor_hp1.restore_state(mock_last_state_hp1)
    await sensor_hp2.restore_state(mock_last_state_hp2)
    
    with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", return_value=mock_config):
        # Call _apply_energy_offset directly (not called automatically in restore_state)
        await sensor_hp1._apply_energy_offset()
        await sensor_hp2._apply_energy_offset()
        
        # HP1: 100.0 + 150.5 = 250.5
        assert sensor_hp1._energy_value == 250.5
        assert sensor_hp1._applied_offset == 150.5
        
        # HP2: 200.0 + 300.25 = 500.25
        assert sensor_hp2._energy_value == 500.25
        assert sensor_hp2._applied_offset == 300.25
