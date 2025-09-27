#!/usr/bin/env python3
"""
Test für Monthly und Yearly Energy Consumption Sensoren
Erstellt: 2025-01-14
Zweck: Testet die korrekte Funktionalität der monthly und yearly Sensoren
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'lambda_heat_pumps'))

import unittest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

# Mock the imports that cause issues
sys.modules['homeassistant'] = Mock()
sys.modules['homeassistant.core'] = Mock()
sys.modules['homeassistant.helpers'] = Mock()
sys.modules['homeassistant.helpers.entity'] = Mock()
sys.modules['homeassistant.helpers.restore_state'] = Mock()
sys.modules['homeassistant.helpers.update_coordinator'] = Mock()
sys.modules['homeassistant.components.sensor'] = Mock()
sys.modules['homeassistant.config_entries'] = Mock()
sys.modules['homeassistant.helpers.dispatcher'] = Mock()
sys.modules['homeassistant.helpers.entity_platform'] = Mock()
sys.modules['homeassistant.exceptions'] = Mock()
sys.modules['homeassistant.helpers.template'] = Mock()

# Mock const module
class MockConst:
    ENERGY_CONSUMPTION_SENSOR_TEMPLATES = {}
    ENERGY_CONSUMPTION_MODES = []
    ENERGY_CONSUMPTION_PERIODS = []
    SENSOR_TYPES = {}
    HP_SENSOR_TEMPLATES = {}
    HC_SENSOR_TEMPLATES = {}
    SOL_SENSOR_TEMPLATES = {}
    BUFF_SENSOR_TEMPLATES = {}
    BOIL_SENSOR_TEMPLATES = {}
    CALCULATED_SENSOR_TEMPLATES = {}
    CLIMATE_TEMPLATES = {}
    DOMAIN = "lambda_heat_pumps"

sys.modules['const'] = MockConst()

# Mock other modules
sys.modules['automations'] = Mock()
sys.modules['const_mapping'] = Mock()
sys.modules['coordinator'] = Mock()
sys.modules['template_sensor'] = Mock()

from sensor import LambdaEnergyConsumptionSensor

class TestMonthlyYearlySensors(unittest.TestCase):
    """Test für Monthly und Yearly Energy Consumption Sensoren."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.hass = Mock()
        self.entry = Mock()
        self.entry.entry_id = "test_entry"
        
        # Mock Home Assistant components
        self.hass.async_create_task = Mock()
        
    def test_monthly_sensor_initialization(self):
        """Test monthly sensor initialization."""
        sensor = LambdaEnergyConsumptionSensor(
            hass=self.hass,
            entry=self.entry,
            sensor_id="heating_energy_monthly",
            name="Heating Energy Monthly",
            entity_id="sensor.test_heating_energy_monthly",
            unique_id="test_heating_energy_monthly",
            unit="kWh",
            state_class="total",
            device_class="energy",
            device_type="hp",
            hp_index=1,
            mode="heating",
            period="monthly"
        )
        
        # Test initial values
        self.assertEqual(sensor._reset_interval, "monthly")
        self.assertEqual(sensor._energy_value, 0.0)
        self.assertEqual(sensor._previous_monthly_value, 0.0)
        self.assertEqual(sensor._previous_yearly_value, 0.0)
        
    def test_yearly_sensor_initialization(self):
        """Test yearly sensor initialization."""
        sensor = LambdaEnergyConsumptionSensor(
            hass=self.hass,
            entry=self.entry,
            sensor_id="heating_energy_yearly",
            name="Heating Energy Yearly",
            entity_id="sensor.test_heating_energy_yearly",
            unique_id="test_heating_energy_yearly",
            unit="kWh",
            state_class="total",
            device_class="energy",
            device_type="hp",
            hp_index=1,
            mode="heating",
            period="yearly"
        )
        
        # Test initial values
        self.assertEqual(sensor._reset_interval, "yearly")
        self.assertEqual(sensor._energy_value, 0.0)
        self.assertEqual(sensor._previous_monthly_value, 0.0)
        self.assertEqual(sensor._previous_yearly_value, 0.0)
        
    def test_monthly_sensor_value_calculation(self):
        """Test monthly sensor value calculation."""
        sensor = LambdaEnergyConsumptionSensor(
            hass=self.hass,
            entry=self.entry,
            sensor_id="heating_energy_monthly",
            name="Heating Energy Monthly",
            entity_id="sensor.test_heating_energy_monthly",
            unique_id="test_heating_energy_monthly",
            unit="kWh",
            state_class="total",
            device_class="energy",
            device_type="hp",
            hp_index=1,
            mode="heating",
            period="monthly"
        )
        
        # Set energy value and previous monthly value
        sensor._energy_value = 100.0
        sensor._previous_monthly_value = 50.0
        
        # Test value calculation
        self.assertEqual(sensor.native_value, 50.0)  # 100 - 50 = 50
        
        # Test with higher previous value (should return 0)
        sensor._previous_monthly_value = 150.0
        self.assertEqual(sensor.native_value, 0.0)  # max(0, 100 - 150) = 0
        
    def test_yearly_sensor_value_calculation(self):
        """Test yearly sensor value calculation."""
        sensor = LambdaEnergyConsumptionSensor(
            hass=self.hass,
            entry=self.entry,
            sensor_id="heating_energy_yearly",
            name="Heating Energy Yearly",
            entity_id="sensor.test_heating_energy_yearly",
            unique_id="test_heating_energy_yearly",
            unit="kWh",
            state_class="total",
            device_class="energy",
            device_type="hp",
            hp_index=1,
            mode="heating",
            period="yearly"
        )
        
        # Set energy value and previous yearly value
        sensor._energy_value = 1000.0
        sensor._previous_yearly_value = 500.0
        
        # Test value calculation
        self.assertEqual(sensor.native_value, 500.0)  # 1000 - 500 = 500
        
        # Test with higher previous value (should return 0)
        sensor._previous_yearly_value = 1500.0
        self.assertEqual(sensor.native_value, 0.0)  # max(0, 1000 - 1500) = 0
        
    def test_monthly_sensor_reset_behavior(self):
        """Test monthly sensor reset behavior."""
        sensor = LambdaEnergyConsumptionSensor(
            hass=self.hass,
            entry=self.entry,
            sensor_id="heating_energy_monthly",
            name="Heating Energy Monthly",
            entity_id="sensor.test_heating_energy_monthly",
            unique_id="test_heating_energy_monthly",
            unit="kWh",
            state_class="total",
            device_class="energy",
            device_type="hp",
            hp_index=1,
            mode="heating",
            period="monthly"
        )
        
        # Set initial values
        sensor._energy_value = 100.0
        sensor._previous_monthly_value = 0.0
        
        # Mock async_write_ha_state
        sensor.async_write_ha_state = Mock()
        
        # Test reset behavior
        asyncio.run(sensor._handle_reset("test_entry"))
        
        # Monthly sensor should save current value and NOT reset energy_value
        self.assertEqual(sensor._previous_monthly_value, 100.0)
        self.assertEqual(sensor._energy_value, 100.0)  # Should NOT be reset
        sensor.async_write_ha_state.assert_called_once()
        
    def test_yearly_sensor_reset_behavior(self):
        """Test yearly sensor reset behavior."""
        sensor = LambdaEnergyConsumptionSensor(
            hass=self.hass,
            entry=self.entry,
            sensor_id="heating_energy_yearly",
            name="Heating Energy Yearly",
            entity_id="sensor.test_heating_energy_yearly",
            unique_id="test_heating_energy_yearly",
            unit="kWh",
            state_class="total",
            device_class="energy",
            device_type="hp",
            hp_index=1,
            mode="heating",
            period="yearly"
        )
        
        # Set initial values
        sensor._energy_value = 1000.0
        sensor._previous_yearly_value = 0.0
        
        # Mock async_write_ha_state
        sensor.async_write_ha_state = Mock()
        
        # Test reset behavior
        asyncio.run(sensor._handle_reset("test_entry"))
        
        # Yearly sensor should save current value and NOT reset energy_value
        self.assertEqual(sensor._previous_yearly_value, 1000.0)
        self.assertEqual(sensor._energy_value, 1000.0)  # Should NOT be reset
        sensor.async_write_ha_state.assert_called_once()
        
    def test_daily_sensor_reset_behavior(self):
        """Test daily sensor reset behavior (should reset energy_value)."""
        sensor = LambdaEnergyConsumptionSensor(
            hass=self.hass,
            entry=self.entry,
            sensor_id="heating_energy_daily",
            name="Heating Energy Daily",
            entity_id="sensor.test_heating_energy_daily",
            unique_id="test_heating_energy_daily",
            unit="kWh",
            state_class="total",
            device_class="energy",
            device_type="hp",
            hp_index=1,
            mode="heating",
            period="daily"
        )
        
        # Set initial values
        sensor._energy_value = 50.0
        
        # Mock async_write_ha_state
        sensor.async_write_ha_state = Mock()
        
        # Test reset behavior
        asyncio.run(sensor._handle_reset("test_entry"))
        
        # Daily sensor should reset energy_value
        self.assertEqual(sensor._energy_value, 0.0)
        sensor.async_write_ha_state.assert_called_once()
        
    def test_extra_state_attributes(self):
        """Test extra state attributes for monthly and yearly sensors."""
        # Test monthly sensor attributes
        monthly_sensor = LambdaEnergyConsumptionSensor(
            hass=self.hass,
            entry=self.entry,
            sensor_id="heating_energy_monthly",
            name="Heating Energy Monthly",
            entity_id="sensor.test_heating_energy_monthly",
            unique_id="test_heating_energy_monthly",
            unit="kWh",
            state_class="total",
            device_class="energy",
            device_type="hp",
            hp_index=1,
            mode="heating",
            period="monthly"
        )
        
        monthly_sensor._previous_monthly_value = 100.0
        attrs = monthly_sensor.extra_state_attributes
        
        self.assertEqual(attrs["reset_interval"], "monthly")
        self.assertEqual(attrs["previous_monthly_value"], 100.0)
        self.assertNotIn("previous_yearly_value", attrs)
        
        # Test yearly sensor attributes
        yearly_sensor = LambdaEnergyConsumptionSensor(
            hass=self.hass,
            entry=self.entry,
            sensor_id="heating_energy_yearly",
            name="Heating Energy Yearly",
            entity_id="sensor.test_heating_energy_yearly",
            unique_id="test_heating_energy_yearly",
            unit="kWh",
            state_class="total",
            device_class="energy",
            device_type="hp",
            hp_index=1,
            mode="heating",
            period="yearly"
        )
        
        yearly_sensor._previous_yearly_value = 1000.0
        attrs = yearly_sensor.extra_state_attributes
        
        self.assertEqual(attrs["reset_interval"], "yearly")
        self.assertEqual(attrs["previous_yearly_value"], 1000.0)
        self.assertNotIn("previous_monthly_value", attrs)

if __name__ == "__main__":
    unittest.main()
