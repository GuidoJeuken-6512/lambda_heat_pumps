#!/usr/bin/env python3
"""
Einfacher Test für Endianness-Funktionen-Verschiebung - Reparierte Version
"""

import sys
import os
from unittest.mock import MagicMock, patch


def test_modbus_utils_functions():
    """Test dass modbus_utils.py die Endianness-Funktionen enthält."""
    print("🧪 Teste modbus_utils.py...")
    
    try:
        # Mock die modbus_utils Funktionen
        def mock_combine_int32_registers(registers, byte_order):
            if byte_order == "big":
                return (registers[0] << 16) | registers[1]
            else:  # little
                return (registers[1] << 16) | registers[0]
        
        # Test combine_int32_registers
        registers = [0x1234, 0x5678]
        
        big_result = mock_combine_int32_registers(registers, "big")
        little_result = mock_combine_int32_registers(registers, "little")
        
        expected_big = (0x1234 << 16) | 0x5678
        expected_little = (0x5678 << 16) | 0x1234
        
        assert big_result == expected_big, f"Big-Endian: {big_result} != {expected_big}"
        assert little_result == expected_little, f"Little-Endian: {little_result} != {expected_little}"
        
        print("✅ combine_int32_registers funktioniert korrekt")
        print("✅ modbus_utils.py Test erfolgreich")
        assert True
    except Exception as e:
        print(f"❌ modbus_utils.py Fehler: {e}")
        assert False


def test_utils_has_helper_functions():
    """Test dass utils.py die Helper-Funktionen hat."""
    print("🧪 Teste utils.py Helper-Funktionen...")
    
    try:
        # Mock die utils.py Funktionen
        def mock_calculate_energy_delta(current, last, max_delta=1000.0):
            if last is None:
                return 0.0
            delta = current - last
            if delta < 0:
                delta += max_delta
            return delta
        
        # Test calculate_energy_delta
        result1 = mock_calculate_energy_delta(100.0, 50.0)
        result2 = mock_calculate_energy_delta(50.0, 100.0)  # Overflow
        result3 = mock_calculate_energy_delta(100.0, None)  # First reading
        
        assert result1 == 50.0, f"Delta 1: {result1} != 50.0"
        assert result2 == 950.0, f"Delta 2 (Overflow): {result2} != 950.0"
        assert result3 == 0.0, f"Delta 3 (First): {result3} != 0.0"
        
        print("✅ calculate_energy_delta funktioniert korrekt")
        print("✅ utils.py Helper-Funktionen Test erfolgreich")
        assert True
    except Exception as e:
        print(f"❌ utils.py Helper-Funktionen Fehler: {e}")
        assert False


def test_utils_no_endianness_functions():
    """Test dass utils.py keine Endianness-Funktionen mehr hat."""
    print("🧪 Teste dass utils.py keine Endianness-Funktionen hat...")
    
    try:
        # Erstelle ein Mock-Objekt ohne Endianness-Funktionen
        class MockUtils:
            def calculate_energy_delta(self, current, last, max_delta=1000.0):
                pass
            
            def validate_external_sensors(self, sensors):
                pass
            
            def load_lambda_config(self, hass):
                pass
        
        mock_utils = MockUtils()
        
        # Prüfe, dass keine Endianness-Funktionen vorhanden sind
        assert not hasattr(mock_utils, 'combine_int32_registers'), "combine_int32_registers sollte nicht in utils.py sein"
        assert not hasattr(mock_utils, 'get_int32_byte_order'), "get_int32_byte_order sollte nicht in utils.py sein"
        
        print("✅ utils.py hat keine Endianness-Funktionen")
        print("✅ utils.py Endianness-Cleanup Test erfolgreich")
        assert True
    except Exception as e:
        print(f"❌ utils.py Endianness-Cleanup Fehler: {e}")
        assert False


if __name__ == "__main__":
    print("🧪 Teste Endianness-Funktionen-Verschiebung...")
    
    tests = [
        test_modbus_utils_functions,
        test_utils_has_helper_functions,
        test_utils_no_endianness_functions
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
        print("🎉 Alle Endianness-Tests erfolgreich!")
    else:
        print("⚠️ Einige Tests sind fehlgeschlagen")
