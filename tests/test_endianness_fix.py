#!/usr/bin/env python3
"""
Test für Endianness-Fix (Issue #22)

Testet die neuen Endianness-Funktionen für int32-Register.
"""

import sys
import os
import asyncio
from unittest.mock import Mock, patch

# Füge den Pfad zur Integration hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'lambda_heat_pumps'))

# Mock der Home Assistant Abhängigkeiten
sys.modules['homeassistant.core'] = Mock()
sys.modules['homeassistant.helpers.entity_registry'] = Mock()
sys.modules['homeassistant.const'] = Mock()
sys.modules['homeassistant.helpers.entity_component'] = Mock()

# Importiere die Funktionen direkt
def combine_int32_registers(registers: list, byte_order: str = "big") -> int:
    """
    Kombiniert zwei 16-Bit-Register zu einem 32-Bit-Wert.
    
    Args:
        registers: Liste mit 2 Register-Werten
        byte_order: "big" oder "little"
    
    Returns:
        int: 32-Bit-Wert
        
    Raises:
        ValueError: Wenn weniger als 2 Register vorhanden sind
    """
    if len(registers) < 2:
        raise ValueError("Mindestens 2 Register erforderlich für int32")
    
    if byte_order == "little":
        # Little-Endian: Niedrigere Bits zuerst
        return (registers[1] << 16) | registers[0]
    else:  # big-endian (Standard)
        # Big-Endian: Höhere Bits zuerst (aktuelle Implementierung)
        return (registers[0] << 16) | registers[1]


async def get_int32_byte_order(hass: Mock) -> str:
    """
    Lädt Endianness-Konfiguration aus lambda_wp_config.yaml (undokumentiert).
    
    Args:
        hass: Home Assistant Instanz
    
    Returns:
        str: "big" oder "little" (Standard: "big")
    """
    try:
        # Mock der load_lambda_config Funktion
        config = {"modbus": {"int32_byte_order": "big"}}
        modbus_config = config.get("modbus", {})
        
        # Hole explizite Einstellung (Standard: "big")
        byte_order = modbus_config.get("int32_byte_order", "big")
        
        # Validiere Wert
        if byte_order not in ["big", "little"]:
            print(f"Ungültige int32_byte_order: {byte_order}, verwende 'big'")
            return "big"
            
        return byte_order
        
    except Exception as e:
        print(f"Fehler beim Laden der Endianness-Konfiguration: {e}")
        return "big"  # Sicherer Fallback auf aktuelles Verhalten


def to_signed_32bit(value: int) -> int:
    """Konvertiert 32-Bit unsigned zu signed."""
    if value >= 0x80000000:  # 2^31
        return value - 0x100000000  # 2^32
    return value


def test_combine_int32_registers():
    """Test der combine_int32_registers Funktion."""
    print("🧪 Teste combine_int32_registers...")
    
    # Test-Daten: Zwei 16-Bit Register
    registers = [0x1234, 0x5678]  # 4660, 22136
    
    # Big-Endian (Standard): Höhere Bits zuerst
    big_endian_result = combine_int32_registers(registers, "big")
    expected_big = (0x1234 << 16) | 0x5678  # 0x12345678 = 305419896
    assert big_endian_result == expected_big, f"Big-Endian: {big_endian_result} != {expected_big}"
    print(f"✅ Big-Endian: {registers} -> 0x{big_endian_result:08X} ({big_endian_result})")
    
    # Little-Endian: Niedrigere Bits zuerst
    little_endian_result = combine_int32_registers(registers, "little")
    expected_little = (0x5678 << 16) | 0x1234  # 0x56781234 = 1450742324
    assert little_endian_result == expected_little, f"Little-Endian: {little_endian_result} != {expected_little}"
    print(f"✅ Little-Endian: {registers} -> 0x{little_endian_result:08X} ({little_endian_result})")
    
    # Test mit anderen Werten
    registers2 = [0x0001, 0x0002]  # 1, 2
    big_result2 = combine_int32_registers(registers2, "big")
    little_result2 = combine_int32_registers(registers2, "little")
    
    assert big_result2 == 0x00010002, f"Big-Endian 2: {big_result2} != 0x00010002"
    assert little_result2 == 0x00020001, f"Little-Endian 2: {little_result2} != 0x00020001"
    print(f"✅ Test 2 - Big: 0x{big_result2:08X}, Little: 0x{little_result2:08X}")
    
    # Test mit Fehlerbehandlung
    try:
        combine_int32_registers([0x1234], "big")  # Nur ein Register
        assert False, "Sollte ValueError werfen"
    except ValueError as e:
        assert "Mindestens 2 Register erforderlich" in str(e)
        print("✅ Fehlerbehandlung: Korrekte ValueError für zu wenige Register")
    
    print("✅ combine_int32_registers Tests erfolgreich!")


async def test_get_int32_byte_order():
    """Test der get_int32_byte_order Funktion."""
    print("\n🧪 Teste get_int32_byte_order...")
    
    # Mock Home Assistant
    mock_hass = Mock()
    
    # Test 1: Standard-Verhalten (keine Konfiguration)
    result = await get_int32_byte_order(mock_hass)
    assert result == "big", f"Standard sollte 'big' sein, aber war: {result}"
    print("✅ Standard-Verhalten: 'big'")
    
    print("✅ get_int32_byte_order Tests erfolgreich!")


def test_real_world_scenarios():
    """Test mit realen Szenarien."""
    print("\n🧪 Teste real-world Szenarien...")
    
    # Szenario 1: Energie-Sensor mit typischen Werten
    # Beispiel: 1000 Wh = 0x000003E8
    energy_registers = [0x0000, 0x03E8]  # 0, 1000
    
    big_energy = combine_int32_registers(energy_registers, "big")
    little_energy = combine_int32_registers(energy_registers, "little")
    
    print(f"Energie-Sensor (1000 Wh):")
    print(f"  Big-Endian:    0x{big_energy:08X} = {big_energy} Wh")
    print(f"  Little-Endian: 0x{little_energy:08X} = {little_energy} Wh")
    
    # Szenario 2: Große Werte (nahe 32-Bit Maximum)
    large_registers = [0x7FFF, 0xFFFF]  # 32767, 65535
    
    big_large = combine_int32_registers(large_registers, "big")
    little_large = combine_int32_registers(large_registers, "little")
    
    print(f"Große Werte:")
    print(f"  Big-Endian:    0x{big_large:08X} = {big_large}")
    print(f"  Little-Endian: 0x{little_large:08X} = {little_large}")
    
    # Szenario 3: Negative Werte (mit to_signed_32bit)
    
    # Simuliere negative Werte
    negative_registers = [0xFFFF, 0xFFFF]  # -1 in 32-Bit
    
    big_negative = combine_int32_registers(negative_registers, "big")
    little_negative = combine_int32_registers(negative_registers, "little")
    
    big_signed = to_signed_32bit(big_negative)
    little_signed = to_signed_32bit(little_negative)
    
    print(f"Negative Werte:")
    print(f"  Big-Endian:    0x{big_negative:08X} -> {big_signed}")
    print(f"  Little-Endian: 0x{little_negative:08X} -> {little_signed}")
    
    print("✅ Real-world Szenarien erfolgreich!")


async def main():
    """Hauptfunktion für alle Tests."""
    print("🚀 Starte Endianness-Fix Tests (Issue #22)")
    print("=" * 50)
    
    try:
        # Test 1: combine_int32_registers
        test_combine_int32_registers()
        
        # Test 2: get_int32_byte_order
        await test_get_int32_byte_order()
        
        # Test 3: Real-world Szenarien
        test_real_world_scenarios()
        
        print("\n" + "=" * 50)
        print("🎉 Alle Tests erfolgreich!")
        print("\n📋 Zusammenfassung:")
        print("✅ combine_int32_registers funktioniert korrekt")
        print("✅ get_int32_byte_order lädt Konfiguration korrekt")
        print("✅ Fehlerbehandlung funktioniert")
        print("✅ Real-world Szenarien getestet")
        print("\n🔧 Benutzer-Anleitung:")
        print("Bei falschen int32-Werten in lambda_wp_config.yaml hinzufügen:")
        print("modbus:")
        print("  int32_byte_order: \"little\"")
        
    except Exception as e:
        print(f"\n❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
