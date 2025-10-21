"""Test Energy Consumption Sensor functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

from custom_components.lambda_heat_pumps.sensor import LambdaEnergyConsumptionSensor
from custom_components.lambda_heat_pumps.const import (
    ENERGY_CONSUMPTION_SENSOR_TEMPLATES,
    ENERGY_CONSUMPTION_MODES,
    ENERGY_CONSUMPTION_PERIODS,
)


class TestLambdaEnergyConsumptionSensor:
    """Test LambdaEnergyConsumptionSensor class."""

    @pytest.fixture
    def mock_hass(self):
        """Mock Home Assistant instance."""
        hass = Mock()
        hass.states = Mock()
        hass.data = {}
        hass.data['customize'] = {}
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

    def test_set_energy_value(self, energy_sensor):
        """Test setting energy value."""
        test_value = 123.45
        
        energy_sensor.set_energy_value(test_value)
        
        assert energy_sensor._energy_value == test_value

    def test_set_energy_value_string_conversion(self, energy_sensor):
        """Test setting energy value with string input."""
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
    async def test_async_added_to_hass(self, energy_sensor):
        """Test async_added_to_hass method."""
        # Mock last state
        last_state = Mock()
        last_state.state = "50.0"
        energy_sensor.async_get_last_state = AsyncMock(return_value=last_state)
        
        # Mock dispatcher connect
        with patch('custom_components.lambda_heat_pumps.sensor.async_dispatcher_connect') as mock_connect:
            await energy_sensor.async_added_to_hass()
        
        # Verify dispatcher was connected
        mock_connect.assert_called_once()
        
        # Verify restore_state was called
        assert energy_sensor._energy_value == 50.0

    @pytest.mark.asyncio
    async def test_async_added_to_hass_no_last_state(self, energy_sensor):
        """Test async_added_to_hass method with no last state."""
        energy_sensor.async_get_last_state = AsyncMock(return_value=None)
        
        with patch('custom_components.lambda_heat_pumps.sensor.async_dispatcher_connect'):
            await energy_sensor.async_added_to_hass()
        
        # Verify default value
        assert energy_sensor._energy_value == 0.0

    @pytest.mark.asyncio
    async def test_async_added_to_hass_invalid_last_state(self, energy_sensor):
        """Test async_added_to_hass method with invalid last state."""
        last_state = Mock()
        last_state.state = "invalid"
        energy_sensor.async_get_last_state = AsyncMock(return_value=last_state)
        
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

    def test_handle_reset(self, energy_sensor):
        """Test handle reset method."""
        energy_sensor._energy_value = 100.0
        
        energy_sensor._handle_reset()
        
        assert energy_sensor._energy_value == 0.0

    def test_device_info(self, energy_sensor, mock_entry):
        """Test device info property."""
        with patch('custom_components.lambda_heat_pumps.sensor.build_device_info') as mock_build:
            mock_build.return_value = {"test": "device_info"}
            
            result = energy_sensor.device_info
            
            assert result == {"test": "device_info"}
            mock_build.assert_called_once_with(mock_entry)

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



