#!/usr/bin/env python3
"""
Test für Kompatibilität der Sensor-Änderungen mit sensor.py, coordinator.py, utils.py und automations.py
"""

import sys
import os

# Füge den custom_components Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

def test_sensor_imports():
    """Test: sensor.py kann alle neuen Funktionen importieren."""
    try:
        from lambda_heat_pumps.const import (
            get_operating_state_from_template,
            get_reset_signal_from_template,
            get_all_reset_intervals,
            get_all_periods,
            get_energy_consumption_modes,
            get_energy_consumption_periods
        )
        print("✓ sensor.py kann neue Funktionen importieren")
        return True
    except ImportError as e:
        print(f"❌ Import-Fehler: {e}")
        return False

def test_coordinator_compatibility():
    """Test: coordinator.py ist kompatibel mit neuen Template-Attributen."""
    try:
        from lambda_heat_pumps.const import CALCULATED_SENSOR_TEMPLATES
        
        # Teste, ob coordinator.py die neuen Attribute verwenden kann
        for sensor_key, template in CALCULATED_SENSOR_TEMPLATES.items():
            if 'cycling' in sensor_key:
                # Prüfe, ob die neuen Attribute vorhanden sind
                assert "operating_state" in template, f"operating_state fehlt in {sensor_key}"
                assert "period" in template, f"period fehlt in {sensor_key}"
                assert "reset_interval" in template, f"reset_interval fehlt in {sensor_key}"
                assert "reset_signal" in template, f"reset_signal fehlt in {sensor_key}"
        
        print("✓ coordinator.py ist kompatibel mit neuen Template-Attributen")
        return True
    except Exception as e:
        print(f"❌ coordinator.py Kompatibilitäts-Fehler: {e}")
        return False

def test_utils_compatibility():
    """Test: utils.py ist kompatibel mit neuen Template-Attributen."""
    try:
        from lambda_heat_pumps.const import (
            get_operating_state_from_template,
            get_reset_signal_from_template,
            get_all_reset_intervals,
            get_all_periods
        )
        
        # Teste die neuen Funktionen
        assert get_operating_state_from_template("heating_cycling_daily") == "heating"
        assert get_reset_signal_from_template("heating_cycling_daily") == "lambda_heat_pumps_reset_daily"
        assert get_reset_signal_from_template("heating_cycling_2h") == "lambda_heat_pumps_reset_2h"
        assert get_reset_signal_from_template("heating_cycling_4h") == "lambda_heat_pumps_reset_4h"
        
        intervals = get_all_reset_intervals()
        assert "daily" in intervals
        assert "2h" in intervals
        assert "4h" in intervals
        
        periods = get_all_periods()
        assert "daily" in periods
        assert "2h" in periods
        assert "4h" in periods
        assert "total" in periods
        
        print("✓ utils.py ist kompatibel mit neuen Template-Attributen")
        return True
    except Exception as e:
        print(f"❌ utils.py Kompatibilitäts-Fehler: {e}")
        return False

def test_automations_compatibility():
    """Test: automations.py ist kompatibel mit neuen Reset-Signalen."""
    try:
        from lambda_heat_pumps.automations import (
            SIGNAL_RESET_DAILY,
            SIGNAL_RESET_2H,
            SIGNAL_RESET_4H
        )
        
        # Prüfe, ob die Signale korrekt definiert sind
        assert SIGNAL_RESET_DAILY == "lambda_heat_pumps_reset_daily"
        assert SIGNAL_RESET_2H == "lambda_heat_pumps_reset_2h"
        assert SIGNAL_RESET_4H == "lambda_heat_pumps_reset_4h"
        
        print("✓ automations.py ist kompatibel mit neuen Reset-Signalen")
        return True
    except Exception as e:
        print(f"❌ automations.py Kompatibilitäts-Fehler: {e}")
        return False

def test_sensor_reset_logic():
    """Test: Sensor Reset-Logik funktioniert mit neuen Attributen."""
    try:
        from lambda_heat_pumps.const import (
            get_reset_signal_from_template,
            get_operating_state_from_template,
            CALCULATED_SENSOR_TEMPLATES
        )
        
        # Teste verschiedene Sensoren
        test_sensors = [
            "heating_cycling_daily",
            "heating_cycling_2h", 
            "heating_cycling_4h",
            "heating_cycling_total",
            "hot_water_energy_daily",
            "cooling_energy_2h"  # Dieser existiert nicht, sollte None zurückgeben
        ]
        
        for sensor_key in test_sensors:
            if sensor_key in CALCULATED_SENSOR_TEMPLATES:
                operating_state = get_operating_state_from_template(sensor_key)
                reset_signal = get_reset_signal_from_template(sensor_key)
                
                print(f"  {sensor_key}: operating_state={operating_state}, reset_signal={reset_signal}")
                
                # Prüfe Konsistenz
                if "daily" in sensor_key:
                    assert reset_signal == "lambda_heat_pumps_reset_daily"
                elif "2h" in sensor_key:
                    assert reset_signal == "lambda_heat_pumps_reset_2h"
                elif "4h" in sensor_key:
                    assert reset_signal == "lambda_heat_pumps_reset_4h"
                elif "total" in sensor_key:
                    assert reset_signal is None
        
        print("✓ Sensor Reset-Logik funktioniert mit neuen Attributen")
        return True
    except Exception as e:
        print(f"❌ Sensor Reset-Logik Fehler: {e}")
        return False

def test_backward_compatibility():
    """Test: Rückwärtskompatibilität mit alten Konstanten."""
    try:
        from lambda_heat_pumps.const import (
            ENERGY_CONSUMPTION_MODES,
            ENERGY_CONSUMPTION_PERIODS,
            OPERATING_STATE_MAP
        )
        
        # Prüfe, ob alte Konstanten noch funktionieren
        assert isinstance(ENERGY_CONSUMPTION_MODES, list)
        assert isinstance(ENERGY_CONSUMPTION_PERIODS, list)
        assert isinstance(OPERATING_STATE_MAP, dict)
        
        # Prüfe, ob die Werte korrekt sind
        assert "heating" in ENERGY_CONSUMPTION_MODES
        assert "daily" in ENERGY_CONSUMPTION_PERIODS
        assert OPERATING_STATE_MAP[1] == "CH"
        
        print("✓ Rückwärtskompatibilität mit alten Konstanten gewährleistet")
        return True
    except Exception as e:
        print(f"❌ Rückwärtskompatibilität Fehler: {e}")
        return False

def main():
    """Führe alle Kompatibilitätstests aus."""
    print("🧪 Teste Kompatibilität der Sensor-Änderungen")
    print("=" * 60)
    
    tests = [
        test_sensor_imports,
        test_coordinator_compatibility,
        test_utils_compatibility,
        test_automations_compatibility,
        test_sensor_reset_logic,
        test_backward_compatibility
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ {test.__name__} fehlgeschlagen")
        except Exception as e:
            print(f"❌ {test.__name__} Exception: {e}")
    
    print("=" * 60)
    print(f"📊 Tests: {passed}/{total} bestanden")
    
    if passed == total:
        print("✅ Alle Kompatibilitätstests bestanden!")
        return True
    else:
        print("❌ Einige Kompatibilitätstests fehlgeschlagen!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
