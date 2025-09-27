#!/usr/bin/env python3
"""
Test für die Const.py Verbesserungen (Punkt 1 & 2)
"""

import sys
import os

# Füge den custom_components Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

def test_energy_consumption_modes():
    """Test: Energy Consumption Modi werden korrekt aus Templates abgeleitet."""
    from lambda_heat_pumps.const import get_energy_consumption_modes, ENERGY_CONSUMPTION_MODES
    
    modes = get_energy_consumption_modes()
    expected_modes = ["cooling", "defrost", "heating", "hot_water", "stby"]
    
    print(f"✓ Energy Consumption Modi: {modes}")
    assert modes == expected_modes, f"Erwartet: {expected_modes}, Bekommen: {modes}"
    assert ENERGY_CONSUMPTION_MODES == modes, "Legacy-Konstante stimmt nicht überein"
    print("✓ Energy Consumption Modi Test bestanden")

def test_energy_consumption_periods():
    """Test: Energy Consumption Perioden werden korrekt aus Templates abgeleitet."""
    from lambda_heat_pumps.const import get_energy_consumption_periods, ENERGY_CONSUMPTION_PERIODS
    
    periods = get_energy_consumption_periods()
    expected_periods = ["daily", "total"]
    
    print(f"✓ Energy Consumption Perioden: {periods}")
    assert periods == expected_periods, f"Erwartet: {expected_periods}, Bekommen: {periods}"
    assert ENERGY_CONSUMPTION_PERIODS == periods, "Legacy-Konstante stimmt nicht überein"
    print("✓ Energy Consumption Perioden Test bestanden")

def test_reset_intervals():
    """Test: Reset-Intervalle werden korrekt aus Templates abgeleitet."""
    from lambda_heat_pumps.const import get_energy_consumption_reset_intervals
    
    intervals = get_energy_consumption_reset_intervals()
    expected_intervals = ["daily"]
    
    print(f"✓ Reset-Intervalle: {intervals}")
    assert intervals == expected_intervals, f"Erwartet: {expected_intervals}, Bekommen: {intervals}"
    print("✓ Reset-Intervalle Test bestanden")

def test_operating_state_from_template():
    """Test: Operating State wird korrekt aus Template abgeleitet."""
    from lambda_heat_pumps.const import get_operating_state_from_template
    
    # Test Energy Consumption Sensoren
    assert get_operating_state_from_template("heating_energy_daily") == "heating"
    assert get_operating_state_from_template("hot_water_energy_total") == "hot_water"
    assert get_operating_state_from_template("cooling_energy_daily") == "cooling"
    assert get_operating_state_from_template("defrost_energy_total") == "defrost"
    assert get_operating_state_from_template("stby_energy_daily") == "stby"
    
    # Test Cycling Sensoren
    assert get_operating_state_from_template("heating_cycling_daily") == "heating"
    assert get_operating_state_from_template("hot_water_cycling_total") == "hot_water"
    
    print("✓ Operating State aus Template Test bestanden")

def test_reset_signal_from_template():
    """Test: Reset-Signal wird korrekt aus Template abgeleitet."""
    from lambda_heat_pumps.const import get_reset_signal_from_template
    
    # Test Daily Sensoren (haben Reset-Signal)
    assert get_reset_signal_from_template("heating_energy_daily") == "lambda_heat_pumps_reset_daily"
    assert get_reset_signal_from_template("hot_water_energy_daily") == "lambda_heat_pumps_reset_daily"
    assert get_reset_signal_from_template("heating_cycling_daily") == "lambda_heat_pumps_reset_daily"
    
    # Test Total Sensoren (haben kein Reset-Signal)
    assert get_reset_signal_from_template("heating_energy_total") is None
    assert get_reset_signal_from_template("heating_cycling_total") is None
    
    print("✓ Reset-Signal aus Template Test bestanden")

def test_all_sensor_templates():
    """Test: Alle Sensor-Templates werden korrekt zusammengeführt."""
    from lambda_heat_pumps.const import get_all_sensor_templates
    
    all_templates = get_all_sensor_templates()
    
    # Prüfe, dass Energy Consumption Templates enthalten sind
    assert "heating_energy_daily" in all_templates
    assert "hot_water_energy_total" in all_templates
    
    # Prüfe, dass Cycling Templates enthalten sind
    assert "heating_cycling_daily" in all_templates
    assert "hot_water_cycling_total" in all_templates
    
    print(f"✓ Alle Sensor-Templates: {len(all_templates)} Templates gefunden")
    print("✓ Alle Sensor-Templates Test bestanden")

def test_template_attributes():
    """Test: Template-Attribute sind korrekt gesetzt."""
    from lambda_heat_pumps.const import ENERGY_CONSUMPTION_SENSOR_TEMPLATES, CALCULATED_SENSOR_TEMPLATES
    
    # Test Energy Consumption Template
    heating_daily = ENERGY_CONSUMPTION_SENSOR_TEMPLATES["heating_energy_daily"]
    assert heating_daily["operating_state"] == "heating"
    assert heating_daily["period"] == "daily"
    assert heating_daily["reset_interval"] == "daily"
    assert heating_daily["reset_signal"] == "lambda_heat_pumps_reset_daily"
    
    # Test Cycling Template
    heating_cycling_daily = CALCULATED_SENSOR_TEMPLATES["heating_cycling_daily"]
    assert heating_cycling_daily["operating_state"] == "heating"
    assert heating_cycling_daily["period"] == "daily"
    assert heating_cycling_daily["reset_interval"] == "daily"
    assert heating_cycling_daily["reset_signal"] == "lambda_heat_pumps_reset_daily"
    
    print("✓ Template-Attribute Test bestanden")

def main():
    """Führe alle Tests aus."""
    print("🧪 Teste Const.py Verbesserungen (Punkt 1 & 2)")
    print("=" * 50)
    
    try:
        test_energy_consumption_modes()
        test_energy_consumption_periods()
        test_reset_intervals()
        test_operating_state_from_template()
        test_reset_signal_from_template()
        test_all_sensor_templates()
        test_template_attributes()
        
        print("=" * 50)
        print("✅ Alle Tests bestanden! Const.py Verbesserungen funktionieren korrekt.")
        
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
