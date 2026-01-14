"""Test COP Sensor functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from types import SimpleNamespace
from homeassistant.core import HomeAssistant, State, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.helpers.event import async_track_state_change_event

from custom_components.lambda_heat_pumps.sensor import LambdaCOPSensor
from tests.conftest import DummyLoop


class TestLambdaCOPSensor:
    """Test suite for LambdaCOPSensor class."""

    @pytest.fixture
    def mock_hass(self):
        """Mock Home Assistant instance."""
        from unittest.mock import MagicMock
        hass = MagicMock()
        hass.states = MagicMock()
        hass.data = {'integrations': {}, 'customize': {}}
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
        entry.domain = "lambda_heat_pumps"
        entry.data = {
            "name": "eu08l",
            "host": "192.168.1.100",
            "port": 502,
        }
        return entry

    @pytest.fixture
    def cop_sensor(self, mock_hass, mock_entry):
        """Create a LambdaCOPSensor instance."""
        return LambdaCOPSensor(
            hass=mock_hass,
            entry=mock_entry,
            sensor_id="heating_cop_daily",
            name="Heating COP Daily",
            entity_id="sensor.eu08l_hp1_heating_cop_daily",
            unique_id="eu08l_hp1_heating_cop_daily",
            unit=None,  # COP ist dimensionslos
            state_class="measurement",
            device_class=None,
            device_type="hp",
            hp_index=1,
            mode="heating",
            period="daily",
            thermal_energy_entity_id="sensor.eu08l_hp1_heating_thermal_energy_daily",
            electrical_energy_entity_id="sensor.eu08l_hp1_heating_energy_daily",
        )

    def test_sensor_initialization(self, cop_sensor):
        """Test sensor initialization."""
        assert cop_sensor._sensor_id == "heating_cop_daily"
        assert cop_sensor._name == "Heating COP Daily"
        assert cop_sensor.entity_id == "sensor.eu08l_hp1_heating_cop_daily"
        assert cop_sensor._unique_id == "eu08l_hp1_heating_cop_daily"
        assert cop_sensor._unit is None
        assert cop_sensor._hp_index == 1
        assert cop_sensor._mode == "heating"
        assert cop_sensor._period == "daily"
        assert cop_sensor._thermal_energy_entity_id == "sensor.eu08l_hp1_heating_thermal_energy_daily"
        assert cop_sensor._electrical_energy_entity_id == "sensor.eu08l_hp1_heating_energy_daily"
        assert cop_sensor._precision == 2
        assert cop_sensor._attr_suggested_display_precision == 2
        assert cop_sensor._cop_value is None
        assert cop_sensor._unsub_state_changes is None

    def test_sensor_properties(self, cop_sensor):
        """Test sensor properties."""
        assert cop_sensor._attr_native_unit_of_measurement is None
        assert cop_sensor._attr_name == "Heating COP Daily"
        assert cop_sensor._attr_unique_id == "eu08l_hp1_heating_cop_daily"
        assert cop_sensor._attr_device_class is None
        assert cop_sensor._attr_state_class == SensorStateClass.MEASUREMENT
        assert cop_sensor._attr_has_entity_name is True
        assert cop_sensor._attr_should_poll is False
        assert cop_sensor._attr_suggested_display_precision == 2

    def test_calculate_cop_basic(self, cop_sensor):
        """Test basic COP calculation."""
        # Mock states
        thermal_state = Mock()
        thermal_state.state = "10.0"
        electrical_state = Mock()
        electrical_state.state = "2.5"
        
        cop_sensor.hass.states.get = Mock(side_effect=lambda eid: {
            "sensor.eu08l_hp1_heating_thermal_energy_daily": thermal_state,
            "sensor.eu08l_hp1_heating_energy_daily": electrical_state,
        }.get(eid))
        
        result = cop_sensor._calculate_cop()
        
        # COP = 10.0 / 2.5 = 4.0
        assert result == 4.0
        assert isinstance(result, float)

    def test_calculate_cop_with_precision(self, cop_sensor):
        """Test COP calculation with rounding to 2 decimal places."""
        # Mock states - Values that require rounding
        thermal_state = Mock()
        thermal_state.state = "11.19"
        electrical_state = Mock()
        electrical_state.state = "3.76"
        
        cop_sensor.hass.states.get = Mock(side_effect=lambda eid: {
            "sensor.eu08l_hp1_heating_thermal_energy_daily": thermal_state,
            "sensor.eu08l_hp1_heating_energy_daily": electrical_state,
        }.get(eid))
        
        result = cop_sensor._calculate_cop()
        
        # COP = 11.19 / 3.76 = 2.9760638298... → rounded to 2.98
        assert result == 2.98
        assert isinstance(result, float)

    def test_calculate_cop_with_comma_decimal(self, cop_sensor):
        """Test COP calculation with comma as decimal separator."""
        # Mock states - European decimal format
        thermal_state = Mock()
        thermal_state.state = "11,19"
        electrical_state = Mock()
        electrical_state.state = "3,76"
        
        cop_sensor.hass.states.get = Mock(side_effect=lambda eid: {
            "sensor.eu08l_hp1_heating_thermal_energy_daily": thermal_state,
            "sensor.eu08l_hp1_heating_energy_daily": electrical_state,
        }.get(eid))
        
        result = cop_sensor._calculate_cop()
        
        # Should handle comma separator correctly
        # COP = 11.19 / 3.76 = 2.9760638298... → rounded to 2.98
        assert result == 2.98

    def test_calculate_cop_division_by_zero(self, cop_sensor):
        """Test COP calculation when electrical energy is zero."""
        # Mock states - electrical energy is zero
        thermal_state = Mock()
        thermal_state.state = "10.0"
        electrical_state = Mock()
        electrical_state.state = "0.0"
        
        cop_sensor.hass.states.get = Mock(side_effect=lambda eid: {
            "sensor.eu08l_hp1_heating_thermal_energy_daily": thermal_state,
            "sensor.eu08l_hp1_heating_energy_daily": electrical_state,
        }.get(eid))
        
        result = cop_sensor._calculate_cop()
        
        # Should return 0.0 when electrical energy is 0
        assert result == 0.0

    def test_calculate_cop_negative_electrical(self, cop_sensor):
        """Test COP calculation when electrical energy is negative."""
        # Mock states - electrical energy is negative
        thermal_state = Mock()
        thermal_state.state = "10.0"
        electrical_state = Mock()
        electrical_state.state = "-1.0"
        
        cop_sensor.hass.states.get = Mock(side_effect=lambda eid: {
            "sensor.eu08l_hp1_heating_thermal_energy_daily": thermal_state,
            "sensor.eu08l_hp1_heating_energy_daily": electrical_state,
        }.get(eid))
        
        result = cop_sensor._calculate_cop()
        
        # Should return 0.0 when electrical energy is negative
        assert result == 0.0

    def test_calculate_cop_thermal_unavailable(self, cop_sensor):
        """Test COP calculation when thermal sensor is unavailable."""
        # Mock states - thermal sensor unavailable
        thermal_state = None
        electrical_state = Mock()
        electrical_state.state = "2.5"
        
        cop_sensor.hass.states.get = Mock(side_effect=lambda eid: {
            "sensor.eu08l_hp1_heating_thermal_energy_daily": thermal_state,
            "sensor.eu08l_hp1_heating_energy_daily": electrical_state,
        }.get(eid))
        
        result = cop_sensor._calculate_cop()
        
        # Should return None when thermal sensor is unavailable
        assert result is None

    def test_calculate_cop_electrical_unavailable(self, cop_sensor):
        """Test COP calculation when electrical sensor is unavailable."""
        # Mock states - electrical sensor unavailable
        thermal_state = Mock()
        thermal_state.state = "10.0"
        electrical_state = None
        
        cop_sensor.hass.states.get = Mock(side_effect=lambda eid: {
            "sensor.eu08l_hp1_heating_thermal_energy_daily": thermal_state,
            "sensor.eu08l_hp1_heating_energy_daily": electrical_state,
        }.get(eid))
        
        result = cop_sensor._calculate_cop()
        
        # Should return None when electrical sensor is unavailable
        assert result is None

    def test_calculate_cop_thermal_state_unknown(self, cop_sensor):
        """Test COP calculation when thermal sensor state is 'unknown'."""
        # Mock states - thermal sensor state is 'unknown'
        thermal_state = Mock()
        thermal_state.state = "unknown"
        electrical_state = Mock()
        electrical_state.state = "2.5"
        
        cop_sensor.hass.states.get = Mock(side_effect=lambda eid: {
            "sensor.eu08l_hp1_heating_thermal_energy_daily": thermal_state,
            "sensor.eu08l_hp1_heating_energy_daily": electrical_state,
        }.get(eid))
        
        result = cop_sensor._calculate_cop()
        
        # Should return None when thermal sensor state is 'unknown'
        assert result is None

    def test_calculate_cop_electrical_state_unavailable(self, cop_sensor):
        """Test COP calculation when electrical sensor state is 'unavailable'."""
        # Mock states - electrical sensor state is 'unavailable'
        thermal_state = Mock()
        thermal_state.state = "10.0"
        electrical_state = Mock()
        electrical_state.state = "unavailable"
        
        cop_sensor.hass.states.get = Mock(side_effect=lambda eid: {
            "sensor.eu08l_hp1_heating_thermal_energy_daily": thermal_state,
            "sensor.eu08l_hp1_heating_energy_daily": electrical_state,
        }.get(eid))
        
        result = cop_sensor._calculate_cop()
        
        # Should return None when electrical sensor state is 'unavailable'
        assert result is None

    def test_calculate_cop_invalid_state_value(self, cop_sensor):
        """Test COP calculation with invalid state value."""
        # Mock states - invalid state value
        thermal_state = Mock()
        thermal_state.state = "10.0"
        electrical_state = Mock()
        electrical_state.state = "invalid_value"
        
        cop_sensor.hass.states.get = Mock(side_effect=lambda eid: {
            "sensor.eu08l_hp1_heating_thermal_energy_daily": thermal_state,
            "sensor.eu08l_hp1_heating_energy_daily": electrical_state,
        }.get(eid))
        
        result = cop_sensor._calculate_cop()
        
        # Should return None when state value cannot be converted to float
        assert result is None

    def test_native_value_when_cop_available(self, cop_sensor):
        """Test native_value property when COP is available."""
        cop_sensor._cop_value = 3.45
        
        result = cop_sensor.native_value
        
        # Should return the stored COP value rounded to 2 decimal places
        assert result == 3.45

    def test_native_value_when_cop_none(self, cop_sensor):
        """Test native_value property when COP is None (unavailable)."""
        cop_sensor._cop_value = None
        
        result = cop_sensor.native_value
        
        # Should return None when COP is not available
        assert result is None

    def test_native_value_rounding(self, cop_sensor):
        """Test native_value property rounds correctly."""
        # Set a value that needs rounding
        cop_sensor._cop_value = 2.9760638298
        
        result = cop_sensor.native_value
        
        # Should round to 2 decimal places
        assert result == 2.98

    def test_extra_state_attributes(self, cop_sensor):
        """Test extra state attributes."""
        attrs = cop_sensor.extra_state_attributes
        
        assert attrs["sensor_type"] == "cop"
        assert attrs["mode"] == "heating"
        assert attrs["period"] == "daily"
        assert attrs["hp_index"] == 1
        assert attrs["thermal_energy_entity"] == "sensor.eu08l_hp1_heating_thermal_energy_daily"
        assert attrs["electrical_energy_entity"] == "sensor.eu08l_hp1_heating_energy_daily"

    def test_extra_state_attributes_all_modes(self, mock_hass, mock_entry):
        """Test extra state attributes for all COP sensor modes."""
        modes = ["heating", "hot_water", "cooling"]
        periods = ["daily", "monthly", "total"]
        
        for mode in modes:
            for period in periods:
                sensor_id = f"{mode}_cop_{period}"
                mode_display = mode.replace("_", " ").title().replace(" ", "_")
                sensor_name = f"{mode_display} COP {period.title()}"
                
                sensor = LambdaCOPSensor(
                    hass=mock_hass,
                    entry=mock_entry,
                    sensor_id=sensor_id,
                    name=sensor_name,
                    entity_id=f"sensor.eu08l_hp1_{sensor_id}",
                    unique_id=f"eu08l_hp1_{sensor_id}",
                    unit=None,
                    state_class="measurement",
                    device_class=None,
                    device_type="hp",
                    hp_index=1,
                    mode=mode,
                    period=period,
                    thermal_energy_entity_id=f"sensor.eu08l_hp1_{mode}_thermal_energy_{period}",
                    electrical_energy_entity_id=f"sensor.eu08l_hp1_{mode}_energy_{period}",
                )
                
                attrs = sensor.extra_state_attributes
                assert attrs["sensor_type"] == "cop"
                assert attrs["mode"] == mode
                assert attrs["period"] == period
                assert attrs["hp_index"] == 1

    def test_device_info(self, cop_sensor, mock_entry):
        """Test device info property."""
        # device_info calls build_subdevice_info (since hp_index is set)
        result = cop_sensor.device_info
        
        # Verify it's a dict with expected keys
        assert isinstance(result, dict)
        assert "identifiers" in result
        assert "name" in result
        # Verify it's a subdevice (has hp_index)
        assert cop_sensor._hp_index == 1
        # The result should contain device identifiers
        assert len(result["identifiers"]) > 0

    @pytest.mark.asyncio
    async def test_async_added_to_hass(self, cop_sensor, mock_hass, mock_entry):
        """Test async_added_to_hass method."""
        from unittest.mock import patch, MagicMock
        
        # Mock last state
        last_state = Mock()
        last_state.state = "3.45"
        cop_sensor.async_get_last_state = AsyncMock(return_value=last_state)
        cop_sensor.restore_state = AsyncMock()
        
        # Mock states for source sensors
        thermal_state = Mock()
        thermal_state.state = "10.0"
        electrical_state = Mock()
        electrical_state.state = "2.5"
        mock_hass.states.get = Mock(side_effect=lambda eid: {
            "sensor.eu08l_hp1_heating_thermal_energy_daily": thermal_state,
            "sensor.eu08l_hp1_heating_energy_daily": electrical_state,
        }.get(eid))
        
        # Patch async_write_ha_state
        with patch.object(cop_sensor, 'async_write_ha_state', new_callable=MagicMock):
            # Mock async_track_state_change_event
            with patch('custom_components.lambda_heat_pumps.sensor.async_track_state_change_event') as mock_track:
                mock_track.return_value = Mock()  # Return unsubscribe function
                
                await cop_sensor.async_added_to_hass()
                
                # Verify restore_state was called
                cop_sensor.restore_state.assert_called_once_with(last_state)
                
                # Verify state tracking was registered
                mock_track.assert_called_once()
                call_args = mock_track.call_args
                assert call_args[0][0] == mock_hass
                assert len(call_args[0][1]) == 2  # Two source entities
                assert "sensor.eu08l_hp1_heating_thermal_energy_daily" in call_args[0][1]
                assert "sensor.eu08l_hp1_heating_energy_daily" in call_args[0][1]
                
                # Verify _update_cop was called (since cop_value is None after restore_state)
                # This happens in async_added_to_hass if _cop_value is None

    @pytest.mark.asyncio
    async def test_async_added_to_hass_no_last_state(self, cop_sensor, mock_hass):
        """Test async_added_to_hass method with no last state."""
        from unittest.mock import patch, MagicMock
        
        cop_sensor.async_get_last_state = AsyncMock(return_value=None)
        cop_sensor.restore_state = AsyncMock()
        
        # Mock states for source sensors
        thermal_state = Mock()
        thermal_state.state = "10.0"
        electrical_state = Mock()
        electrical_state.state = "2.5"
        mock_hass.states.get = Mock(side_effect=lambda eid: {
            "sensor.eu08l_hp1_heating_thermal_energy_daily": thermal_state,
            "sensor.eu08l_hp1_heating_energy_daily": electrical_state,
        }.get(eid))
        
        # Patch async_write_ha_state
        with patch.object(cop_sensor, 'async_write_ha_state', new_callable=MagicMock):
            # Mock async_track_state_change_event
            with patch('custom_components.lambda_heat_pumps.sensor.async_track_state_change_event') as mock_track:
                mock_track.return_value = Mock()
                
                await cop_sensor.async_added_to_hass()
                
                # Verify restore_state was called with None
                cop_sensor.restore_state.assert_called_once_with(None)
                
                # Verify state tracking was registered
                mock_track.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_will_remove_from_hass(self, cop_sensor):
        """Test async_will_remove_from_hass method."""
        # Mock unsub function
        mock_unsub = Mock()
        cop_sensor._unsub_state_changes = mock_unsub
        
        await cop_sensor.async_will_remove_from_hass()
        
        # Verify unsub was called
        mock_unsub.assert_called_once()
        assert cop_sensor._unsub_state_changes is None

    @pytest.mark.asyncio
    async def test_async_will_remove_from_hass_no_unsub(self, cop_sensor):
        """Test async_will_remove_from_hass method with no unsub."""
        cop_sensor._unsub_state_changes = None
        
        # Should not raise an exception
        await cop_sensor.async_will_remove_from_hass()

    def test_update_cop_callback(self, cop_sensor, mock_hass):
        """Test _update_cop callback method."""
        from unittest.mock import patch, MagicMock
        
        # Set initial COP value
        cop_sensor._cop_value = 3.0
        
        # Mock states for source sensors
        thermal_state = Mock()
        thermal_state.state = "20.0"
        electrical_state = Mock()
        electrical_state.state = "5.0"
        mock_hass.states.get = Mock(side_effect=lambda eid: {
            "sensor.eu08l_hp1_heating_thermal_energy_daily": thermal_state,
            "sensor.eu08l_hp1_heating_energy_daily": electrical_state,
        }.get(eid))
        
        # Patch async_write_ha_state
        with patch.object(cop_sensor, 'async_write_ha_state', new_callable=MagicMock) as mock_write:
            cop_sensor._update_cop()
            
            # Verify COP was recalculated: 20.0 / 5.0 = 4.0
            assert cop_sensor._cop_value == 4.0
            # Verify state was written
            mock_write.assert_called_once()

    def test_update_cop_no_change(self, cop_sensor, mock_hass):
        """Test _update_cop when COP value doesn't change."""
        from unittest.mock import patch, MagicMock
        
        # Set initial COP value
        cop_sensor._cop_value = 4.0
        
        # Mock states for source sensors (same values, so COP should be 4.0)
        thermal_state = Mock()
        thermal_state.state = "20.0"
        electrical_state = Mock()
        electrical_state.state = "5.0"
        mock_hass.states.get = Mock(side_effect=lambda eid: {
            "sensor.eu08l_hp1_heating_thermal_energy_daily": thermal_state,
            "sensor.eu08l_hp1_heating_energy_daily": electrical_state,
        }.get(eid))
        
        # Patch async_write_ha_state
        with patch.object(cop_sensor, 'async_write_ha_state', new_callable=MagicMock) as mock_write:
            cop_sensor._update_cop()
            
            # COP should still be 4.0 (no change)
            assert cop_sensor._cop_value == 4.0
            # State should NOT be written when value doesn't change (correct behavior)
            # _update_cop only calls async_write_ha_state() if new_cop != old_cop
            mock_write.assert_not_called()

    def test_update_cop_unavailable(self, cop_sensor, mock_hass):
        """Test _update_cop when source sensors are unavailable."""
        from unittest.mock import patch, MagicMock
        
        # Set initial COP value
        cop_sensor._cop_value = 4.0
        
        # Mock states - thermal sensor unavailable
        thermal_state = None
        electrical_state = Mock()
        electrical_state.state = "5.0"
        mock_hass.states.get = Mock(side_effect=lambda eid: {
            "sensor.eu08l_hp1_heating_thermal_energy_daily": thermal_state,
            "sensor.eu08l_hp1_heating_energy_daily": electrical_state,
        }.get(eid))
        
        # Patch async_write_ha_state
        with patch.object(cop_sensor, 'async_write_ha_state', new_callable=MagicMock) as mock_write:
            cop_sensor._update_cop()
            
            # COP should be None when source is unavailable
            assert cop_sensor._cop_value is None
            # State should still be written
            mock_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_state_change_event_handling(self, cop_sensor, mock_hass):
        """Test state change event handling."""
        from unittest.mock import patch, MagicMock
        
        # Set initial COP value
        cop_sensor._cop_value = 3.0
        
        # Create state change callback
        # This is the callback that would be registered by async_track_state_change_event
        def create_state_change_callback():
            @callback
            def _state_change_callback(event):
                new_state = event.data.get("new_state")
                old_state = event.data.get("old_state")
                entity_id = event.data.get("entity_id")
                
                if new_state is None:
                    return
                
                if old_state is None or old_state.state != new_state.state:
                    cop_sensor._update_cop()
            
            return _state_change_callback
        
        callback_func = create_state_change_callback()
        
        # Mock states after change
        thermal_state = Mock()
        thermal_state.state = "15.0"
        electrical_state = Mock()
        electrical_state.state = "3.0"
        mock_hass.states.get = Mock(side_effect=lambda eid: {
            "sensor.eu08l_hp1_heating_thermal_energy_daily": thermal_state,
            "sensor.eu08l_hp1_heating_energy_daily": electrical_state,
        }.get(eid))
        
        # Patch async_write_ha_state
        with patch.object(cop_sensor, 'async_write_ha_state', new_callable=MagicMock) as mock_write:
            # Create a mock event
            mock_event = Mock()
            mock_event.data = {
                "entity_id": "sensor.eu08l_hp1_heating_thermal_energy_daily",
                "new_state": thermal_state,
                "old_state": Mock(state="10.0"),
            }
            
            # Call the callback
            callback_func(mock_event)
            
            # Verify COP was recalculated: 15.0 / 3.0 = 5.0
            assert cop_sensor._cop_value == 5.0
            mock_write.assert_called_once()

    def test_sensor_creation_for_all_modes_and_periods(self, mock_hass, mock_entry):
        """Test sensor creation for all COP sensor modes and periods."""
        cop_modes = ["heating", "hot_water", "cooling"]
        cop_periods = ["daily", "monthly", "total"]
        
        sensors = []
        for mode in cop_modes:
            for period in cop_periods:
                sensor_id = f"{mode}_cop_{period}"
                mode_display = mode.replace("_", " ").title().replace(" ", "_")
                sensor_name = f"{mode_display} COP {period.title()}"
                
                sensor = LambdaCOPSensor(
                    hass=mock_hass,
                    entry=mock_entry,
                    sensor_id=sensor_id,
                    name=sensor_name,
                    entity_id=f"sensor.eu08l_hp1_{sensor_id}",
                    unique_id=f"eu08l_hp1_{sensor_id}",
                    unit=None,
                    state_class="measurement",
                    device_class=None,
                    device_type="hp",
                    hp_index=1,
                    mode=mode,
                    period=period,
                    thermal_energy_entity_id=f"sensor.eu08l_hp1_{mode}_thermal_energy_{period}",
                    electrical_energy_entity_id=f"sensor.eu08l_hp1_{mode}_energy_{period}",
                )
                
                sensors.append(sensor)
                
                # Verify sensor properties
                assert sensor._mode == mode
                assert sensor._period == period
                assert sensor._unit is None
                assert sensor._device_class is None
                assert sensor._attr_state_class == SensorStateClass.MEASUREMENT
                assert sensor._precision == 2
                assert sensor._attr_suggested_display_precision == 2
        
        # Verify all sensors were created (3 modes * 3 periods = 9 sensors)
        assert len(sensors) == len(cop_modes) * len(cop_periods)

    def test_cop_sensor_precision(self, cop_sensor):
        """Test that COP sensor precision is correctly set."""
        assert cop_sensor._precision == 2
        assert cop_sensor._attr_suggested_display_precision == 2

    def test_cop_calculation_edge_cases(self, cop_sensor, mock_hass):
        """Test COP calculation with edge case values."""
        test_cases = [
            # (thermal, electrical, expected_cop)
            ("1.0", "1.0", 1.0),  # COP = 1.0
            ("5.0", "1.0", 5.0),  # COP = 5.0
            ("0.1", "1.0", 0.1),  # COP < 1.0
            ("100.0", "10.0", 10.0),  # High COP
            ("0.001", "0.001", 1.0),  # Very small values
        ]
        
        for thermal_str, electrical_str, expected in test_cases:
            thermal_state = Mock()
            thermal_state.state = thermal_str
            electrical_state = Mock()
            electrical_state.state = electrical_str
            
            mock_hass.states.get = Mock(side_effect=lambda eid, t=thermal_state, e=electrical_state: {
                "sensor.eu08l_hp1_heating_thermal_energy_daily": t,
                "sensor.eu08l_hp1_heating_energy_daily": e,
            }.get(eid))
            
            result = cop_sensor._calculate_cop()
            assert result == round(expected, 2), f"Failed for thermal={thermal_str}, electrical={electrical_str}"

    @pytest.mark.asyncio
    async def test_restore_state(self, cop_sensor):
        """Test restore_state method."""
        from unittest.mock import MagicMock
        
        # Mock last state
        last_state = Mock()
        last_state.state = "3.45"
        last_state.attributes = {}
        
        # Patch async_write_ha_state
        with patch.object(cop_sensor, 'async_write_ha_state', new_callable=MagicMock):
            await cop_sensor.restore_state(last_state)
            
            # Verify COP value was restored (rounded to 2 decimal places)
            assert cop_sensor._cop_value == 3.45

    @pytest.mark.asyncio
    async def test_restore_state_invalid_value(self, cop_sensor):
        """Test restore_state with invalid value."""
        from unittest.mock import MagicMock
        
        # Mock last state with invalid value
        last_state = Mock()
        last_state.state = "invalid"
        last_state.attributes = {}
        
        # Patch async_write_ha_state
        with patch.object(cop_sensor, 'async_write_ha_state', new_callable=MagicMock):
            await cop_sensor.restore_state(last_state)
            
            # COP value should remain None when restore fails
            assert cop_sensor._cop_value is None

    @pytest.mark.asyncio
    async def test_restore_state_none(self, cop_sensor):
        """Test restore_state with None."""
        from unittest.mock import MagicMock
        
        # Patch async_write_ha_state
        with patch.object(cop_sensor, 'async_write_ha_state', new_callable=MagicMock):
            await cop_sensor.restore_state(None)
            
            # COP value should remain None
            assert cop_sensor._cop_value is None

    def test_cop_entity_ids_format(self, mock_hass, mock_entry):
        """Test that COP sensor entity IDs follow the correct format."""
        sensor = LambdaCOPSensor(
            hass=mock_hass,
            entry=mock_entry,
            sensor_id="heating_cop_daily",
            name="Heating COP Daily",
            entity_id="sensor.eu08l_hp1_heating_cop_daily",
            unique_id="eu08l_hp1_heating_cop_daily",
            unit=None,
            state_class="measurement",
            device_class=None,
            device_type="hp",
            hp_index=1,
            mode="heating",
            period="daily",
            thermal_energy_entity_id="sensor.eu08l_hp1_heating_thermal_energy_daily",
            electrical_energy_entity_id="sensor.eu08l_hp1_heating_energy_daily",
        )
        
        # Verify entity ID format
        assert sensor.entity_id == "sensor.eu08l_hp1_heating_cop_daily"
        assert sensor._unique_id == "eu08l_hp1_heating_cop_daily"
        assert sensor._thermal_energy_entity_id == "sensor.eu08l_hp1_heating_thermal_energy_daily"
        assert sensor._electrical_energy_entity_id == "sensor.eu08l_hp1_heating_energy_daily"

