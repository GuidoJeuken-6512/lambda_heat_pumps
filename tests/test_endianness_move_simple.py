#!/usr/bin/env python3
"""
Einfacher Test für Endianness-Funktionen-Verschiebung
"""

import sys
import os

# Füge den Pfad zur Integration hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'lambda_heat_pumps'))

def test_modbus_utils_functions():
    """Test dass modbus_utils.py die Endianness-Funktionen enthält."""
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

def test_utils_has_helper_functions():
    """Test dass utils.py die Helper-Funktionen enthält."""
    print("\n🧪 Teste utils.py Helper-Funktionen...")
    
    try:
        import utils
        
        # Prüfe dass die Helper-Funktionen existieren
        assert hasattr(utils, 'get_energy_consumption_periods'), "get_energy_consumption_periods nicht in utils"
        assert hasattr(utils, 'get_energy_consumption_reset_intervals'), "get_energy_consumption_reset_intervals nicht in utils"
        assert hasattr(utils, 'get_all_reset_intervals'), "get_all_reset_intervals nicht in utils"
        assert hasattr(utils, 'get_all_periods'), "get_all_periods nicht in utils"
        
        print("✅ Alle Helper-Funktionen sind in utils verfügbar")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import-Fehler: {e}")
        return False
    except Exception as e:
        print(f"❌ Test-Fehler: {e}")
        return False

def test_utils_no_endianness_functions():
    """Test dass utils.py keine Endianness-Funktionen mehr enthält."""
    print("\n🧪 Teste utils.py Cleanup...")
    
    try:
        import utils
        
        # Prüfe dass die Endianness-Funktionen NICHT mehr in utils sind
        assert not hasattr(utils, 'combine_int32_registers'), "combine_int32_registers sollte nicht mehr in utils sein"
        
        print("✅ utils.py wurde korrekt bereinigt")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import-Fehler: {e}")
        return False
    except Exception as e:
        print(f"❌ Test-Fehler: {e}")
        return False

def main():
    """Hauptfunktion."""
    print("🚀 Teste Endianness-Funktionen-Verschiebung")
    print("=" * 60)
    
    success = True
    
    # Test 1: modbus_utils.py enthält Endianness-Funktionen
    if not test_modbus_utils_functions():
        success = False
    
    # Test 2: utils.py enthält Helper-Funktionen
    if not test_utils_has_helper_functions():
        success = False
    
    # Test 3: utils.py wurde von Endianness-Funktionen bereinigt
    if not test_utils_no_endianness_functions():
        success = False
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 Verschiebung erfolgreich!")
        print("\n📋 Zusammenfassung:")
        print("✅ Endianness-Funktionen in modbus_utils.py")
        print("✅ Helper-Funktionen in utils.py")
        print("✅ utils.py wurde von Endianness-Funktionen bereinigt")
        print("✅ Bessere Code-Organisation")
    else:
        print("\n❌ Verschiebung fehlgeschlagen!")
        return False
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
