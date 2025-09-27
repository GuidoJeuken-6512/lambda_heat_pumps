#!/usr/bin/env python3
"""
Test für Endianness-Funktionen-Verschiebung

Testet, dass die Endianness-Funktionen korrekt von modbus_utils importiert werden.
"""

import sys
import os
import asyncio
from unittest.mock import Mock

# Füge den Pfad zur Integration hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'lambda_heat_pumps'))

# Mock der Home Assistant Abhängigkeiten
sys.modules['homeassistant.core'] = Mock()
sys.modules['homeassistant.helpers.entity_registry'] = Mock()
sys.modules['homeassistant.const'] = Mock()
sys.modules['homeassistant.helpers.entity_component'] = Mock()
sys.modules['homeassistant.config_entries'] = Mock()
sys.modules['homeassistant.helpers.update_coordinator'] = Mock()
sys.modules['homeassistant.helpers.dispatcher'] = Mock()
sys.modules['homeassistant.util'] = Mock()
sys.modules['homeassistant.helpers.entity_registry'] = Mock()
sys.modules['pymodbus.client'] = Mock()

# Mock der Integration-Module
sys.modules['lambda_heat_pumps.const'] = Mock()
sys.modules['lambda_heat_pumps.utils'] = Mock()

def test_import_from_modbus_utils():
    """Test dass Endianness-Funktionen aus modbus_utils importiert werden können."""
    print("🧪 Teste Import aus modbus_utils...")
    
    try:
        # Test Import der Endianness-Funktionen
        from modbus_utils import get_int32_byte_order, combine_int32_registers
        print("✅ Import aus modbus_utils erfolgreich")
        
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
        
        # Test get_int32_byte_order (mit Mock)
        async def test_get_int32_byte_order():
            mock_hass = Mock()
            result = await get_int32_byte_order(mock_hass)
            assert result == "big", f"Standard sollte 'big' sein, aber war: {result}"
            print("✅ get_int32_byte_order funktioniert")
        
        asyncio.run(test_get_int32_byte_order())
        
        print("✅ Alle Endianness-Funktionen aus modbus_utils funktionieren!")
        
    except ImportError as e:
        print(f"❌ Import-Fehler: {e}")
        return False
    except Exception as e:
        print(f"❌ Test-Fehler: {e}")
        return False
    
    return True


def test_coordinator_imports():
    """Test dass coordinator.py die Endianness-Funktionen korrekt importiert."""
    print("\n🧪 Teste Coordinator-Imports...")
    
    try:
        # Test dass coordinator.py die Funktionen importieren kann
        import coordinator
        print("✅ coordinator.py kann importiert werden")
        
        # Prüfe ob die Funktionen verfügbar sind
        assert hasattr(coordinator, 'get_int32_byte_order'), "get_int32_byte_order nicht in coordinator verfügbar"
        assert hasattr(coordinator, 'combine_int32_registers'), "combine_int32_registers nicht in coordinator verfügbar"
        
        print("✅ Endianness-Funktionen sind in coordinator verfügbar")
        
    except ImportError as e:
        print(f"❌ Coordinator Import-Fehler: {e}")
        return False
    except Exception as e:
        print(f"❌ Coordinator Test-Fehler: {e}")
        return False
    
    return True


def test_utils_cleanup():
    """Test dass utils.py keine Endianness-Funktionen mehr enthält."""
    print("\n🧪 Teste utils.py Cleanup...")
    
    try:
        import utils
        
        # Prüfe dass die Funktionen NICHT mehr in utils sind
        assert not hasattr(utils, 'get_int32_byte_order'), "get_int32_byte_order sollte nicht mehr in utils sein"
        assert not hasattr(utils, 'combine_int32_registers'), "combine_int32_registers sollte nicht mehr in utils sein"
        
        print("✅ utils.py wurde korrekt bereinigt")
        
    except ImportError as e:
        print(f"❌ Utils Import-Fehler: {e}")
        return False
    except Exception as e:
        print(f"❌ Utils Test-Fehler: {e}")
        return False
    
    return True


def main():
    """Hauptfunktion."""
    print("🚀 Teste Endianness-Funktionen-Verschiebung")
    print("=" * 60)
    
    success = True
    
    try:
        # Test 1: Import aus modbus_utils
        if not test_import_from_modbus_utils():
            success = False
        
        # Test 2: Coordinator-Imports
        if not test_coordinator_imports():
            success = False
        
        # Test 3: Utils-Cleanup
        if not test_utils_cleanup():
            success = False
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 Verschiebung erfolgreich!")
            print("\n📋 Zusammenfassung:")
            print("✅ Endianness-Funktionen in modbus_utils.py")
            print("✅ Coordinator importiert aus modbus_utils")
            print("✅ utils.py wurde bereinigt")
            print("✅ Keine zirkulären Abhängigkeiten")
            print("\n🔧 Vorteile:")
            print("• Bessere Code-Organisation")
            print("• Modbus-spezifische Funktionen in modbus_utils")
            print("• Klarere Trennung der Verantwortlichkeiten")
        else:
            print("\n❌ Verschiebung fehlgeschlagen!")
            return False
        
    except Exception as e:
        print(f"\n❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
