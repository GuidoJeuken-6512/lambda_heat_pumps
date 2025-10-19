#!/usr/bin/env python3
"""
Einfache Tests ohne Home Assistant Abhängigkeiten
"""

import sys
import os
from unittest.mock import MagicMock, patch


def test_basic_imports():
    """Test: Grundlegende Imports funktionieren."""
    try:
        # Teste, ob wir die Dateien lesen können
        config_path = os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'lambda_heat_pumps')
        
        files_to_check = [
            '__init__.py',
            'const.py',
            'utils.py',
            'coordinator.py',
            'sensor.py',
            'config_flow.py'
        ]
        
        for file in files_to_check:
            file_path = os.path.join(config_path, file)
            if os.path.exists(file_path):
                print(f"✓ {file} existiert")
            else:
                print(f"❌ {file} fehlt")
                assert False
        
        print("✓ Alle Grunddateien vorhanden")
        assert True
    except Exception as e:
        print(f"❌ Import-Fehler: {e}")
        assert False


def test_const_file_structure():
    """Test: const.py Struktur ist korrekt."""
    try:
        const_path = os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'lambda_heat_pumps', 'const.py')
        
        with open(const_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Prüfe wichtige Konstanten
        required_constants = [
            'DOMAIN',
            'HP_SENSOR_TEMPLATES',
            'ENERGY_CONSUMPTION_MODES',
            'ENERGY_CONSUMPTION_PERIODS'
        ]
        
        for constant in required_constants:
            if constant in content:
                print(f"✓ {constant} gefunden")
            else:
                print(f"❌ {constant} fehlt")
                assert False
        
        print("✓ const.py Struktur ist korrekt")
        assert True
    except Exception as e:
        print(f"❌ const.py Fehler: {e}")
        assert False


def test_utils_file_structure():
    """Test: utils.py Struktur ist korrekt."""
    try:
        utils_path = os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'lambda_heat_pumps', 'utils.py')
        
        with open(utils_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Prüfe wichtige Funktionen
        required_functions = [
            'calculate_energy_delta',
            'validate_external_sensors',
            'load_lambda_config'
        ]
        
        for function in required_functions:
            if f'def {function}' in content:
                print(f"✓ {function} gefunden")
            else:
                print(f"❌ {function} fehlt")
                assert False
        
        print("✓ utils.py Struktur ist korrekt")
        assert True
    except Exception as e:
        print(f"❌ utils.py Fehler: {e}")
        assert False


def test_coordinator_file_structure():
    """Test: coordinator.py Struktur ist korrekt."""
    try:
        coordinator_path = os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'lambda_heat_pumps', 'coordinator.py')
        
        with open(coordinator_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Prüfe wichtige Klassen und Funktionen
        required_items = [
            'class LambdaDataUpdateCoordinator',
            'def _track_hp_energy_consumption',
            'def _handle_sensor_change',
            'def _detect_and_handle_sensor_changes'
        ]
        
        for item in required_items:
            if item in content:
                print(f"✓ {item} gefunden")
            else:
                print(f"❌ {item} fehlt")
                assert False
        
        print("✓ coordinator.py Struktur ist korrekt")
        assert True
    except Exception as e:
        print(f"❌ coordinator.py Fehler: {e}")
        assert False


def test_sensor_file_structure():
    """Test: sensor.py Struktur ist korrekt."""
    try:
        sensor_path = os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'lambda_heat_pumps', 'sensor.py')
        
        with open(sensor_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Prüfe wichtige Klassen
        required_classes = [
            'class LambdaSensor',
            'class LambdaTemplateSensor',
            'class LambdaEnergyConsumptionSensor'
        ]
        
        for class_name in required_classes:
            if class_name in content:
                print(f"✓ {class_name} gefunden")
            else:
                print(f"❌ {class_name} fehlt")
                assert False
        
        print("✓ sensor.py Struktur ist korrekt")
        assert True
    except Exception as e:
        print(f"❌ sensor.py Fehler: {e}")
        assert False


def test_config_flow_file_structure():
    """Test: config_flow.py Struktur ist korrekt."""
    try:
        config_flow_path = os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'lambda_heat_pumps', 'config_flow.py')
        
        with open(config_flow_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Prüfe wichtige Klassen und Funktionen
        required_items = [
            'class LambdaConfigFlow',
            'class LambdaOptionsFlow',
            'def async_step_user',
            'def async_step_init'
        ]
        
        for item in required_items:
            if item in content:
                print(f"✓ {item} gefunden")
            else:
                print(f"❌ {item} fehlt")
                assert False
        
        print("✓ config_flow.py Struktur ist korrekt")
        assert True
    except Exception as e:
        print(f"❌ config_flow.py Fehler: {e}")
        assert False


def test_translation_files():
    """Test: Übersetzungsdateien sind vorhanden."""
    try:
        translations_path = os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'lambda_heat_pumps', 'translations')
        
        if not os.path.exists(translations_path):
            print("❌ translations Verzeichnis fehlt")
            assert False
        
        # Prüfe Übersetzungsdateien
        translation_files = ['de.json', 'en.json']
        
        for file in translation_files:
            file_path = os.path.join(translations_path, file)
            if os.path.exists(file_path):
                print(f"✓ {file} vorhanden")
                
                # Prüfe, ob update_interval Beschreibung enthalten ist
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'update_interval' in content and 'data_description' in content:
                        print(f"✓ {file} enthält update_interval Beschreibung")
                    else:
                        print(f"❌ {file} fehlt update_interval Beschreibung")
                        assert False
            else:
                print(f"❌ {file} fehlt")
                assert False
        
        print("✓ Übersetzungsdateien sind korrekt")
        assert True
    except Exception as e:
        print(f"❌ Übersetzungsdateien Fehler: {e}")
        assert False


def test_manifest_file():
    """Test: manifest.json ist korrekt."""
    try:
        manifest_path = os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'lambda_heat_pumps', 'manifest.json')
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Prüfe wichtige Felder
        required_fields = [
            '"domain"',
            '"name"',
            '"version"',
            '"config_flow"',
            '"requirements"'
        ]
        
        for field in required_fields:
            if field in content:
                print(f"✓ {field} gefunden")
            else:
                print(f"❌ {field} fehlt")
                assert False
        
        # Prüfe Version
        if '"version": "1.4.1"' in content:
            print("✓ Version 1.4.1 gefunden")
        else:
            print("❌ Version 1.4.1 fehlt")
            assert False
        
        print("✓ manifest.json ist korrekt")
        assert True
    except Exception as e:
        print(f"❌ manifest.json Fehler: {e}")
        assert False


if __name__ == "__main__":
    print("🧪 Teste Grundstruktur der Integration...")
    
    tests = [
        test_basic_imports,
        test_const_file_structure,
        test_utils_file_structure,
        test_coordinator_file_structure,
        test_sensor_file_structure,
        test_config_flow_file_structure,
        test_translation_files,
        test_manifest_file
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            print(f"\n--- {test.__name__} ---")
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} fehlgeschlagen: {e}")
            failed += 1
    
    print(f"\n📊 Ergebnisse: {passed} bestanden, {failed} fehlgeschlagen")
    
    if failed == 0:
        print("🎉 Alle Strukturtests erfolgreich!")
    else:
        print("⚠️ Einige Tests sind fehlgeschlagen")
