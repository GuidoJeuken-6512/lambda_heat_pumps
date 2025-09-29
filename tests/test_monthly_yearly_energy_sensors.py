#!/usr/bin/env python3
"""
Test für Monthly/Yearly Energy Consumption Sensoren
Testet die neuen Template-basierten Monthly und Yearly Sensoren.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'lambda_heat_pumps'))

import unittest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Import der zu testenden Module
from custom_components.lambda_heat_pumps.const import (
    ENERGY_CONSUMPTION_SENSOR_TEMPLATES,
)
from custom_components.lambda_heat_pumps.utils import (
    get_energy_consumption_periods,
    get_energy_consumption_reset_intervals,
    get_all_reset_intervals,
    get_all_periods
)
from custom_components.lambda_heat_pumps.automations import (
    SIGNAL_RESET_MONTHLY,
    SIGNAL_RESET_YEARLY,
    setup_cycling_automations,
    cleanup_cycling_automations
)


class TestMonthlyYearlyEnergySensors(unittest.TestCase):
    """Test-Klasse für Monthly/Yearly Energy Consumption Sensoren."""
    
    def test_monthly_templates_exist(self):
        """Test: Monthly Templates sind vorhanden."""
        monthly_templates = [
            "heating_energy_monthly",
            "hot_water_energy_monthly", 
            "cooling_energy_monthly",
            "defrost_energy_monthly",
            "stby_energy_monthly"
        ]
        
        for template_key in monthly_templates:
            with self.subTest(template=template_key):
                self.assertIn(template_key, ENERGY_CONSUMPTION_SENSOR_TEMPLATES)
                template = ENERGY_CONSUMPTION_SENSOR_TEMPLATES[template_key]
                self.assertEqual(template["reset_interval"], "monthly")
                self.assertEqual(template["state_class"], "total")
                self.assertEqual(template["device_class"], "energy")
                self.assertIn("Monthly", template["name"])
    
    def test_yearly_templates_exist(self):
        """Test: Yearly Templates sind vorhanden."""
        yearly_templates = [
            "heating_energy_yearly",
            "hot_water_energy_yearly",
            "cooling_energy_yearly", 
            "defrost_energy_yearly",
            "stby_energy_yearly"
        ]
        
        for template_key in yearly_templates:
            with self.subTest(template=template_key):
                self.assertIn(template_key, ENERGY_CONSUMPTION_SENSOR_TEMPLATES)
                template = ENERGY_CONSUMPTION_SENSOR_TEMPLATES[template_key]
                self.assertEqual(template["reset_interval"], "yearly")
                self.assertEqual(template["state_class"], "total")
                self.assertEqual(template["device_class"], "energy")
                self.assertIn("Yearly", template["name"])
    
    def test_template_consistency(self):
        """Test: Template-Konsistenz zwischen Monthly/Yearly."""
        monthly_templates = [k for k in ENERGY_CONSUMPTION_SENSOR_TEMPLATES.keys() if k.endswith("_monthly")]
        yearly_templates = [k for k in ENERGY_CONSUMPTION_SENSOR_TEMPLATES.keys() if k.endswith("_yearly")]
        
        # Sollten gleich viele Templates haben
        self.assertEqual(len(monthly_templates), len(yearly_templates))
        
        # Jeder Monthly-Template sollte einen entsprechenden Yearly-Template haben
        for monthly_key in monthly_templates:
            base_key = monthly_key.replace("_monthly", "")
            yearly_key = f"{base_key}_yearly"
            self.assertIn(yearly_key, yearly_templates)
    
    def test_reset_intervals_include_monthly_yearly(self):
        """Test: Reset-Intervalle enthalten monthly und yearly."""
        reset_intervals = get_energy_consumption_reset_intervals()
        all_reset_intervals = get_all_reset_intervals()
        
        self.assertIn("monthly", reset_intervals)
        self.assertIn("yearly", reset_intervals)
        self.assertIn("monthly", all_reset_intervals)
        self.assertIn("yearly", all_reset_intervals)
    
    def test_periods_include_monthly_yearly(self):
        """Test: Perioden enthalten monthly und yearly."""
        periods = get_energy_consumption_periods()
        all_periods = get_all_periods()
        
        self.assertIn("monthly", periods)
        self.assertIn("yearly", periods)
        self.assertIn("monthly", all_periods)
        self.assertIn("yearly", all_periods)
    
    def test_reset_signals_exist(self):
        """Test: Reset-Signale sind definiert."""
        self.assertEqual(SIGNAL_RESET_MONTHLY, "lambda_heat_pumps_reset_monthly")
        self.assertEqual(SIGNAL_RESET_YEARLY, "lambda_heat_pumps_reset_yearly")
    
    def test_template_operating_states(self):
        """Test: Operating States sind korrekt zugeordnet."""
        expected_operating_states = {
            "heating_energy_monthly": "heating",
            "hot_water_energy_monthly": "hot_water",
            "cooling_energy_monthly": "cooling",
            "defrost_energy_monthly": "defrost",
            "stby_energy_monthly": "stby",
            "heating_energy_yearly": "heating",
            "hot_water_energy_yearly": "hot_water", 
            "cooling_energy_yearly": "cooling",
            "defrost_energy_yearly": "defrost",
            "stby_energy_yearly": "stby"
        }
        
        for template_key, expected_state in expected_operating_states.items():
            with self.subTest(template=template_key):
                template = ENERGY_CONSUMPTION_SENSOR_TEMPLATES[template_key]
                self.assertEqual(template["operating_state"], expected_state)
    
    def test_template_precision_consistency(self):
        """Test: Precision ist konsistent (6 für alle Energy Sensoren)."""
        for template_key, template in ENERGY_CONSUMPTION_SENSOR_TEMPLATES.items():
            if template_key.endswith(("_monthly", "_yearly")):
                with self.subTest(template=template_key):
                    self.assertEqual(template["precision"], 6)
                    self.assertEqual(template["unit"], "kWh")
    
    def test_template_device_type_consistency(self):
        """Test: Device Type ist konsistent (hp für alle)."""
        for template_key, template in ENERGY_CONSUMPTION_SENSOR_TEMPLATES.items():
            if template_key.endswith(("_monthly", "_yearly")):
                with self.subTest(template=template_key):
                    self.assertEqual(template["device_type"], "hp")
                    self.assertEqual(template["firmware_version"], 1)
                    self.assertFalse(template["writeable"])


class TestMonthlyYearlyAutomations(unittest.TestCase):
    """Test-Klasse für Monthly/Yearly Automations."""
    
    def setUp(self):
        """Setup für Tests."""
        self.hass = Mock()
        self.entry_id = "test_entry_123"
        
        # Mock hass.data
        self.hass.data = {
            "lambda_heat_pumps": {
                self.entry_id: {}
            }
        }
    
    def test_cleanup_cycling_automations_handles_monthly_yearly(self):
        """Test: Cleanup behandelt Monthly und Yearly Listener."""
        # Setup mit Mock-Listenern
        mock_monthly_listener = Mock()
        mock_yearly_listener = Mock()
        
        self.hass.data["lambda_heat_pumps"][self.entry_id] = {
            "monthly_listener": mock_monthly_listener,
            "yearly_listener": mock_yearly_listener
        }
        
        # Cleanup aufrufen
        cleanup_cycling_automations(self.hass, self.entry_id)
        
        # Prüfen dass Listener aufgerufen wurden
        mock_monthly_listener.assert_called_once()
        mock_yearly_listener.assert_called_once()
        
        # Prüfen dass Listener aus hass.data entfernt wurden
        entry_data = self.hass.data["lambda_heat_pumps"][self.entry_id]
        self.assertNotIn("monthly_listener", entry_data)
        self.assertNotIn("yearly_listener", entry_data)


if __name__ == "__main__":
    # Test-Suite ausführen
    unittest.main(verbosity=2)
