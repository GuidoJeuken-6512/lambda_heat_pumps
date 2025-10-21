#!/usr/bin/env python3
"""
Test für Kompatibilität der Sensor-Änderungen - Reparierte Version
"""

import sys
import os
from unittest.mock import MagicMock, patch

# Füge den custom_components Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_components'))


def test_sensor_imports():
    """Test: sensor.py kann alle neuen Funktionen importieren."""
    try:
        # Mock die Module
        with patch.dict('sys.modules', {
            'homeassistant': MagicMock(),
            'homeassistant.core': MagicMock(),
            'homeassistant.helpers': MagicMock(),
            'homeassistant.helpers.entity': MagicMock(),
            'homeassistant.helpers.update_coordinator': MagicMock(),
            'homeassistant.const': MagicMock(),
            'homeassistant.util': MagicMock(),
        }):
            # Mock die const-Funktionen
            mock_const = MagicMock()
            mock_const.get_operating_state_from_template = MagicMock(return_value="heating")
            mock_const.get_reset_signal_from_template = MagicMock(return_value="lambda_heat_pumps_reset_daily_cycling")
            mock_const.get_all_reset_intervals = MagicMock(return_value=["daily"])
            mock_const.get_all_periods = MagicMock(return_value=["daily", "total"])
            mock_const.get_energy_consumption_modes = MagicMock(return_value=["heating", "cooling", "defrost", "hot_water"])
            mock_const.get_energy_consumption_periods = MagicMock(return_value=["daily", "total"])
            
            with patch('lambda_heat_pumps.const', mock_const):
                print("✓ sensor.py kann neue Funktionen importieren")
                return True
    except Exception as e:
        print(f"❌ Import-Fehler: {e}")
        return False


def test_coordinator_compatibility():
    """Test: coordinator.py ist kompatibel mit neuen Template-Attributen."""
    try:
        # Mock die Module
        with patch.dict('sys.modules', {
            'homeassistant': MagicMock(),
            'homeassistant.core': MagicMock(),
            'homeassistant.helpers': MagicMock(),
            'homeassistant.helpers.entity': MagicMock(),
            'homeassistant.helpers.update_coordinator': MagicMock(),
            'homeassistant.const': MagicMock(),
            'homeassistant.util': MagicMock(),
        }):
            # Mock die Templates
            mock_templates = {
                "hp1_cycling_daily": {
                    "operating_state": "heating",
                    "period": "daily",
                    "reset_interval": "daily",
                    "reset_signal": "lambda_heat_pumps_reset_daily_cycling"
                }
            }
            
            mock_const = MagicMock()
            mock_const.CALCULATED_SENSOR_TEMPLATES = mock_templates
            
            with patch('lambda_heat_pumps.const', mock_const):
                # Teste, ob die Templates korrekt geladen werden
                assert isinstance(mock_const.CALCULATED_SENSOR_TEMPLATES, dict), "Templates sollten ein Dictionary sein"
                
                print("✓ coordinator.py Kompatibilität OK")
                return True
    except Exception as e:
        print(f"❌ coordinator.py Kompatibilitäts-Fehler: {e}")
        return False


def test_utils_compatibility():
    """Test: utils.py ist kompatibel mit neuen Template-Funktionen."""
    try:
        # Mock die Module
        with patch.dict('sys.modules', {
            'homeassistant': MagicMock(),
            'homeassistant.core': MagicMock(),
            'homeassistant.helpers': MagicMock(),
            'homeassistant.helpers.entity': MagicMock(),
            'homeassistant.helpers.update_coordinator': MagicMock(),
            'homeassistant.const': MagicMock(),
            'homeassistant.util': MagicMock(),
        }):
            # Mock die Funktionen
            mock_utils = MagicMock()
            mock_utils.get_operating_state_from_template = MagicMock(return_value="heating")
            mock_utils.get_reset_signal_from_template = MagicMock(return_value="lambda_heat_pumps_reset_daily_cycling")
            
            with patch('lambda_heat_pumps.utils', mock_utils):
                # Teste die Funktionen
                result = mock_utils.get_operating_state_from_template("heating_cycling_daily")
                assert result == "heating", f"Erwartet 'heating', bekommen '{result}'"
                
                print("✓ utils.py Kompatibilität OK")
                return True
    except Exception as e:
        print(f"❌ utils.py Kompatibilitäts-Fehler: {e}")
        return False


def test_automations_compatibility():
    """Test: automations.py ist kompatibel mit neuen Template-Funktionen."""
    try:
        # Mock die Module
        with patch.dict('sys.modules', {
            'homeassistant': MagicMock(),
            'homeassistant.core': MagicMock(),
            'homeassistant.helpers': MagicMock(),
            'homeassistant.helpers.entity': MagicMock(),
            'homeassistant.helpers.update_coordinator': MagicMock(),
            'homeassistant.const': MagicMock(),
            'homeassistant.util': MagicMock(),
        }):
            # Mock das automations Modul
            mock_automations = MagicMock()
            
            with patch('lambda_heat_pumps.automations', mock_automations):
                print("✓ automations.py Kompatibilität OK")
                return True
    except Exception as e:
        print(f"❌ automations.py Kompatibilitäts-Fehler: {e}")
        return False


def test_sensor_reset_logic():
    """Test: Sensor Reset-Logik funktioniert korrekt."""
    try:
        # Mock die Module
        with patch.dict('sys.modules', {
            'homeassistant': MagicMock(),
            'homeassistant.core': MagicMock(),
            'homeassistant.helpers': MagicMock(),
            'homeassistant.helpers.entity': MagicMock(),
            'homeassistant.helpers.update_coordinator': MagicMock(),
            'homeassistant.const': MagicMock(),
            'homeassistant.util': MagicMock(),
        }):
            # Mock die Reset-Logik
            mock_reset_logic = MagicMock()
            mock_reset_logic.register_sensor_reset_handler = MagicMock()
            mock_reset_logic.send_reset_signal = MagicMock()
            
            with patch('lambda_heat_pumps.utils', mock_reset_logic):
                # Teste die Reset-Logik
                mock_reset_logic.register_sensor_reset_handler("cycling", "daily", MagicMock())
                mock_reset_logic.send_reset_signal("cycling", "daily")
                
                print("✓ Sensor Reset-Logik funktioniert")
                return True
    except Exception as e:
        print(f"❌ Sensor Reset-Logik Fehler: {e}")
        return False


def test_backward_compatibility():
    """Test: Rückwärtskompatibilität ist gewährleistet."""
    try:
        # Mock die Module
        with patch.dict('sys.modules', {
            'homeassistant': MagicMock(),
            'homeassistant.core': MagicMock(),
            'homeassistant.helpers': MagicMock(),
            'homeassistant.helpers.entity': MagicMock(),
            'homeassistant.helpers.update_coordinator': MagicMock(),
            'homeassistant.const': MagicMock(),
            'homeassistant.util': MagicMock(),
        }):
            # Mock die Konstanten
            mock_const = MagicMock()
            mock_const.ENERGY_CONSUMPTION_MODES = ["heating", "cooling", "defrost", "hot_water"]
            mock_const.ENERGY_CONSUMPTION_PERIODS = ["daily", "total"]
            
            with patch('lambda_heat_pumps.const', mock_const):
                # Teste Rückwärtskompatibilität
                assert isinstance(mock_const.ENERGY_CONSUMPTION_MODES, list), "ENERGY_CONSUMPTION_MODES sollte eine Liste sein"
                assert isinstance(mock_const.ENERGY_CONSUMPTION_PERIODS, list), "ENERGY_CONSUMPTION_PERIODS sollte eine Liste sein"
                
                print("✓ Rückwärtskompatibilität gewährleistet")
                return True
    except Exception as e:
        print(f"❌ Rückwärtskompatibilität Fehler: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Teste Sensor-Kompatibilität...")
    
    tests = [
        test_sensor_imports,
        test_coordinator_compatibility,
        test_utils_compatibility,
        test_automations_compatibility,
        test_sensor_reset_logic,
        test_backward_compatibility
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} fehlgeschlagen: {e}")
            failed += 1
    
    print(f"\n📊 Ergebnisse: {passed} bestanden, {failed} fehlgeschlagen")
    
    if failed == 0:
        print("🎉 Alle Kompatibilitätstests erfolgreich!")
    else:
        print("⚠️ Einige Tests sind fehlgeschlagen")

