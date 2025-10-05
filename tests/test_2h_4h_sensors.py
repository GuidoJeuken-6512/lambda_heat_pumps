#!/usr/bin/env python3
"""
Test für die 2h und 4h Sensoren Verbesserungen
"""

import sys
import os

# Füge den custom_components Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

def test_2h_4h_sensors():
    """Test: 2h und 4h Sensoren haben korrekte Attribute."""
    from lambda_heat_pumps.const import CALCULATED_SENSOR_TEMPLATES
    
    # Test 2h Sensoren
    heating_2h = CALCULATED_SENSOR_TEMPLATES["heating_cycling_2h"]
    assert heating_2h["operating_state"] == "heating"
    assert heating_2h["period"] == "2h"
    assert heating_2h["reset_interval"] == "2h"
    assert heating_2h["reset_signal"] == "lambda_heat_pumps_reset_2h"
    
    hot_water_2h = CALCULATED_SENSOR_TEMPLATES["hot_water_cycling_2h"]
    assert hot_water_2h["operating_state"] == "hot_water"
    assert hot_water_2h["period"] == "2h"
    assert hot_water_2h["reset_interval"] == "2h"
    assert hot_water_2h["reset_signal"] == "lambda_heat_pumps_reset_2h"
    
    cooling_2h = CALCULATED_SENSOR_TEMPLATES["cooling_cycling_2h"]
    assert cooling_2h["operating_state"] == "cooling"
    assert cooling_2h["period"] == "2h"
    assert cooling_2h["reset_interval"] == "2h"
    assert cooling_2h["reset_signal"] == "lambda_heat_pumps_reset_2h"
    
    defrost_2h = CALCULATED_SENSOR_TEMPLATES["defrost_cycling_2h"]
    assert defrost_2h["operating_state"] == "defrost"
    assert defrost_2h["period"] == "2h"
    assert defrost_2h["reset_interval"] == "2h"
    assert defrost_2h["reset_signal"] == "lambda_heat_pumps_reset_2h"
    
    print("✓ 2h Sensoren Test bestanden")

def test_4h_sensors():
    """Test: 4h Sensoren haben korrekte Attribute."""
    from lambda_heat_pumps.const import CALCULATED_SENSOR_TEMPLATES
    
    # Test 4h Sensoren
    heating_4h = CALCULATED_SENSOR_TEMPLATES["heating_cycling_4h"]
    assert heating_4h["operating_state"] == "heating"
    assert heating_4h["period"] == "4h"
    assert heating_4h["reset_interval"] == "4h"
    assert heating_4h["reset_signal"] == "lambda_heat_pumps_reset_4h"
    
    hot_water_4h = CALCULATED_SENSOR_TEMPLATES["hot_water_cycling_4h"]
    assert hot_water_4h["operating_state"] == "hot_water"
    assert hot_water_4h["period"] == "4h"
    assert hot_water_4h["reset_interval"] == "4h"
    assert hot_water_4h["reset_signal"] == "lambda_heat_pumps_reset_4h"
    
    cooling_4h = CALCULATED_SENSOR_TEMPLATES["cooling_cycling_4h"]
    assert cooling_4h["operating_state"] == "cooling"
    assert cooling_4h["period"] == "4h"
    assert cooling_4h["reset_interval"] == "4h"
    assert cooling_4h["reset_signal"] == "lambda_heat_pumps_reset_4h"
    
    defrost_4h = CALCULATED_SENSOR_TEMPLATES["defrost_cycling_4h"]
    assert defrost_4h["operating_state"] == "defrost"
    assert defrost_4h["period"] == "4h"
    assert defrost_4h["reset_interval"] == "4h"
    assert defrost_4h["reset_signal"] == "lambda_heat_pumps_reset_4h"
    
    print("✓ 4h Sensoren Test bestanden")

def test_all_reset_intervals():
    """Test: Alle Reset-Intervalle werden korrekt abgeleitet."""
    from lambda_heat_pumps.const import get_all_reset_intervals
    
    intervals = get_all_reset_intervals()
    expected_intervals = ["2h", "4h", "daily"]
    
    print(f"✓ Alle Reset-Intervalle: {intervals}")
    assert intervals == expected_intervals, f"Erwartet: {expected_intervals}, Bekommen: {intervals}"
    print("✓ Alle Reset-Intervalle Test bestanden")

def test_all_periods():
    """Test: Alle Perioden werden korrekt abgeleitet."""
    from lambda_heat_pumps.const import get_all_periods
    
    periods = get_all_periods()
    expected_periods = ["2h", "4h", "daily", "total"]
    
    print(f"✓ Alle Perioden: {periods}")
    assert periods == expected_periods, f"Erwartet: {expected_periods}, Bekommen: {periods}"
    print("✓ Alle Perioden Test bestanden")

def test_reset_signals():
    """Test: Reset-Signale werden korrekt aus Templates abgeleitet."""
    from lambda_heat_pumps.const import get_reset_signal_from_template
    
    # Test 2h Sensoren
    assert get_reset_signal_from_template("heating_cycling_2h") == "lambda_heat_pumps_reset_2h"
    assert get_reset_signal_from_template("hot_water_cycling_2h") == "lambda_heat_pumps_reset_2h"
    assert get_reset_signal_from_template("cooling_cycling_2h") == "lambda_heat_pumps_reset_2h"
    assert get_reset_signal_from_template("defrost_cycling_2h") == "lambda_heat_pumps_reset_2h"
    
    # Test 4h Sensoren
    assert get_reset_signal_from_template("heating_cycling_4h") == "lambda_heat_pumps_reset_4h"
    assert get_reset_signal_from_template("hot_water_cycling_4h") == "lambda_heat_pumps_reset_4h"
    assert get_reset_signal_from_template("cooling_cycling_4h") == "lambda_heat_pumps_reset_4h"
    assert get_reset_signal_from_template("defrost_cycling_4h") == "lambda_heat_pumps_reset_4h"
    
    # Test Daily Sensoren
    assert get_reset_signal_from_template("heating_cycling_daily") == "lambda_heat_pumps_reset_daily"
    assert get_reset_signal_from_template("heating_energy_daily") == "lambda_heat_pumps_reset_daily"
    
    # Test Total Sensoren (kein Reset-Signal)
    assert get_reset_signal_from_template("heating_cycling_total") is None
    assert get_reset_signal_from_template("heating_energy_total") is None
    
    print("✓ Reset-Signale Test bestanden")

def test_operating_states():
    """Test: Operating States werden korrekt aus Templates abgeleitet."""
    from lambda_heat_pumps.const import get_operating_state_from_template
    
    # Test 2h Sensoren
    assert get_operating_state_from_template("heating_cycling_2h") == "heating"
    assert get_operating_state_from_template("hot_water_cycling_2h") == "hot_water"
    assert get_operating_state_from_template("cooling_cycling_2h") == "cooling"
    assert get_operating_state_from_template("defrost_cycling_2h") == "defrost"
    
    # Test 4h Sensoren
    assert get_operating_state_from_template("heating_cycling_4h") == "heating"
    assert get_operating_state_from_template("hot_water_cycling_4h") == "hot_water"
    assert get_operating_state_from_template("cooling_cycling_4h") == "cooling"
    assert get_operating_state_from_template("defrost_cycling_4h") == "defrost"
    
    print("✓ Operating States Test bestanden")

def main():
    """Führe alle Tests aus."""
    print("🧪 Teste 2h und 4h Sensoren Verbesserungen")
    print("=" * 50)
    
    try:
        test_2h_4h_sensors()
        test_4h_sensors()
        test_all_reset_intervals()
        test_all_periods()
        test_reset_signals()
        test_operating_states()
        
        print("=" * 50)
        print("✅ Alle Tests bestanden! 2h und 4h Sensoren funktionieren korrekt.")
        
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
