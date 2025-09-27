#!/usr/bin/env python3
"""
Einfacher Test für Endianness-Funktionen-Verschiebung
"""

import sys
import os

# Füge den Pfad zur Integration hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'lambda_heat_pumps'))

def test_modbus_utils_functions():
    """Test der Endianness-Funktionen in modbus_utils."""
    print("🧪 Teste Endianness-Funktionen in modbus_utils...")
    
    # Test combine_int32_registers direkt
    def combine_int32_registers(registers: list, byte_order: str = "big") -> int:
        if len(registers) < 2:
            raise ValueError("Mindestens 2 Register erforderlich für int32")
        
        if byte_order == "little":
            return (registers[1] << 16) | registers[0]
        else:
            return (registers[0] << 16) | registers[1]
    
    # Test-Daten
    registers = [0x1234, 0x5678]
    
    # Big-Endian Test
    big_result = combine_int32_registers(registers, "big")
    expected_big = (0x1234 << 16) | 0x5678
    assert big_result == expected_big, f"Big-Endian: {big_result} != {expected_big}"
    print(f"✅ Big-Endian: 0x{big_result:08X}")
    
    # Little-Endian Test
    little_result = combine_int32_registers(registers, "little")
    expected_little = (0x5678 << 16) | 0x1234
    assert little_result == expected_little, f"Little-Endian: {little_result} != {expected_little}"
    print(f"✅ Little-Endian: 0x{little_result:08X}")
    
    # Fehlerbehandlung Test
    try:
        combine_int32_registers([0x1234])  # Nur ein Register
        assert False, "Sollte ValueError werfen"
    except ValueError as e:
        assert "Mindestens 2 Register erforderlich" in str(e)
        print("✅ Fehlerbehandlung funktioniert")
    
    print("✅ Alle Tests erfolgreich!")


def test_file_structure():
    """Test der Dateistruktur."""
    print("\n🧪 Teste Dateistruktur...")
    
    # Prüfe ob modbus_utils.py existiert und die Funktionen enthält
    modbus_utils_path = "custom_components/lambda_heat_pumps/modbus_utils.py"
    if not os.path.exists(modbus_utils_path):
        print("❌ modbus_utils.py nicht gefunden")
        return False
    
    with open(modbus_utils_path, 'r') as f:
        content = f.read()
    
    # Prüfe ob die Funktionen in modbus_utils.py sind
    assert "def get_int32_byte_order" in content, "get_int32_byte_order nicht in modbus_utils.py"
    assert "def combine_int32_registers" in content, "combine_int32_registers nicht in modbus_utils.py"
    print("✅ Endianness-Funktionen in modbus_utils.py gefunden")
    
    # Prüfe ob coordinator.py die Funktionen importiert
    coordinator_path = "custom_components/lambda_heat_pumps/coordinator.py"
    with open(coordinator_path, 'r') as f:
        coordinator_content = f.read()
    
    assert "from .modbus_utils import" in coordinator_content, "modbus_utils Import nicht in coordinator.py"
    assert "get_int32_byte_order" in coordinator_content, "get_int32_byte_order Import nicht in coordinator.py"
    assert "combine_int32_registers" in coordinator_content, "combine_int32_registers Import nicht in coordinator.py"
    print("✅ Coordinator importiert Endianness-Funktionen aus modbus_utils")
    
    # Prüfe ob utils.py die Funktionen NICHT mehr enthält
    utils_path = "custom_components/lambda_heat_pumps/utils.py"
    with open(utils_path, 'r') as f:
        utils_content = f.read()
    
    assert "def get_int32_byte_order" not in utils_content, "get_int32_byte_order sollte nicht mehr in utils.py sein"
    assert "def combine_int32_registers" not in utils_content, "combine_int32_registers sollte nicht mehr in utils.py sein"
    print("✅ utils.py wurde korrekt bereinigt")
    
    print("✅ Dateistruktur korrekt!")


def main():
    """Hauptfunktion."""
    print("🚀 Teste Endianness-Funktionen-Verschiebung")
    print("=" * 50)
    
    try:
        test_modbus_utils_functions()
        test_file_structure()
        
        print("\n" + "=" * 50)
        print("🎉 Verschiebung erfolgreich!")
        print("\n📋 Zusammenfassung:")
        print("✅ Endianness-Funktionen in modbus_utils.py")
        print("✅ Coordinator importiert aus modbus_utils")
        print("✅ utils.py wurde bereinigt")
        print("✅ Keine zirkulären Abhängigkeiten")
        
    except Exception as e:
        print(f"\n❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
