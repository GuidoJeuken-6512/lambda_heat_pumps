#!/usr/bin/env python3
"""
Test für die Hauptfehler-Behebungen
"""

import sys
import os

# Füge den Pfad zur Integration hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'lambda_heat_pumps'))

def test_modbus_utils_exists():
    """Test dass modbus_utils.py existiert und Endianness-Funktionen enthält."""
    print("🧪 Teste modbus_utils.py...")
    
    try:
        # Test Import der Endianness-Funktionen
        from modbus_utils import combine_int32_registers
        print("✅ combine_int32_registers aus modbus_utils importiert")
        
        # Test combine_int32_registers
        registers = [0x1234, 0x5678]
        
        big_result = combine_int32_registers(registers, "big")
        little_result = combine_int32_registers(registers, "little")
        
        expected_big = (0x1234 << 16) | 0x5678
        expected_little = (0x5678 << 16) | 0x1234
        
        assert big_result == expected_big, f"Big-Endian: {big_result} != {expected_big}"
        assert little_result == expected_little, f"Little-Endian: {little_result} != {expected_little}"
        
        print(f"✅ combine_int32_registers funktioniert:")
        print(f"  Big-Endian: 0x{big_result:08X}")
        print(f"  Little-Endian: 0x{little_result:08X}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import-Fehler: {e}")
        return False
    except Exception as e:
        print(f"❌ Test-Fehler: {e}")
        return False

def test_const_has_helper_functions():
    """Test dass const.py die Helper-Funktionen nicht mehr enthält."""
    print("\n🧪 Teste const.py Cleanup...")
    
    try:
        import const
        
        # Prüfe dass die Helper-Funktionen NICHT mehr in const sind
        assert not hasattr(const, 'get_energy_consumption_periods'), "get_energy_consumption_periods sollte nicht mehr in const sein"
        assert not hasattr(const, 'get_energy_consumption_reset_intervals'), "get_energy_consumption_reset_intervals sollte nicht mehr in const sein"
        assert not hasattr(const, 'get_all_reset_intervals'), "get_all_reset_intervals sollte nicht mehr in const sein"
        assert not hasattr(const, 'get_all_periods'), "get_all_periods sollte nicht mehr in const sein"
        
        print("✅ const.py wurde korrekt bereinigt")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import-Fehler: {e}")
        return False
    except Exception as e:
        print(f"❌ Test-Fehler: {e}")
        return False

def test_utils_file_structure():
    """Test dass utils.py die richtige Struktur hat."""
    print("\n🧪 Teste utils.py Struktur...")
    
    try:
        # Prüfe dass utils.py existiert und lesbar ist
        utils_path = os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'lambda_heat_pumps', 'utils.py')
        assert os.path.exists(utils_path), "utils.py existiert nicht"
        
        # Lese die Datei und prüfe auf Helper-Funktionen
        with open(utils_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Prüfe dass die Helper-Funktionen in der Datei sind
        assert 'def get_energy_consumption_periods():' in content, "get_energy_consumption_periods nicht in utils.py"
        assert 'def get_energy_consumption_reset_intervals():' in content, "get_energy_consumption_reset_intervals nicht in utils.py"
        assert 'def get_all_reset_intervals():' in content, "get_all_reset_intervals nicht in utils.py"
        assert 'def get_all_periods():' in content, "get_all_periods nicht in utils.py"
        
        # Prüfe dass Endianness-Funktionen NICHT in utils.py sind
        assert 'def combine_int32_registers(' not in content, "combine_int32_registers sollte nicht in utils.py sein"
        
        print("✅ utils.py hat die richtige Struktur")
        
        return True
        
    except Exception as e:
        print(f"❌ Test-Fehler: {e}")
        return False

def main():
    """Hauptfunktion."""
    print("🚀 Teste Hauptfehler-Behebungen")
    print("=" * 60)
    
    success = True
    
    # Test 1: modbus_utils.py enthält Endianness-Funktionen
    if not test_modbus_utils_exists():
        success = False
    
    # Test 2: const.py wurde bereinigt
    if not test_const_has_helper_functions():
        success = False
    
    # Test 3: utils.py hat die richtige Struktur
    if not test_utils_file_structure():
        success = False
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 Hauptfehler erfolgreich behoben!")
        print("\n📋 Zusammenfassung:")
        print("✅ Endianness-Funktionen in modbus_utils.py")
        print("✅ Helper-Funktionen in utils.py")
        print("✅ const.py wurde bereinigt")
        print("✅ Bessere Code-Organisation")
    else:
        print("\n❌ Hauptfehler-Behebung fehlgeschlagen!")
        return False
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
