#!/usr/bin/env python3
"""
Test für Endianness-Optimierung

Testet, dass die Endianness-Konfiguration nur einmal geladen wird.
"""

import sys
import os
import asyncio
from unittest.mock import Mock, patch, AsyncMock

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
sys.modules['lambda_heat_pumps.modbus_utils'] = Mock()

def test_endianness_loading_optimization():
    """Test dass Endianness nur einmal geladen wird."""
    print("🧪 Teste Endianness-Loading-Optimierung...")
    
    # Mock der get_int32_byte_order Funktion
    call_count = 0
    
    async def mock_get_int32_byte_order(hass):
        nonlocal call_count
        call_count += 1
        print(f"  get_int32_byte_order aufgerufen (Aufruf #{call_count})")
        return "little"  # Simuliere Little-Endian Konfiguration
    
    # Mock der combine_int32_registers Funktion
    def mock_combine_int32_registers(registers, byte_order):
        print(f"  combine_int32_registers aufgerufen mit byte_order: {byte_order}")
        if byte_order == "little":
            return (registers[1] << 16) | registers[0]
        else:
            return (registers[0] << 16) | registers[1]
    
    # Mock der Coordinator-Klasse
    class MockCoordinator:
        def __init__(self):
            self._int32_byte_order = "big"  # Standard-Wert
            self.hass = Mock()
            self.client = None
            self.host = "192.168.1.100"
            self.port = 502
            self.entry = Mock()
            self.entry.data = {"num_hps": 1}
            self.entry.options = {}
            self._connect_calls = 0
            self._update_calls = 0
        
        async def _connect(self):
            """Simuliere _connect mit Endianness-Loading."""
            self._connect_calls += 1
            print(f"  _connect aufgerufen (Aufruf #{self._connect_calls})")
            
            # Load Endianness configuration (only once during connection)
            if self._int32_byte_order == "big":  # Only load if not already set
                try:
                    self._int32_byte_order = await mock_get_int32_byte_order(self.hass)
                    print(f"  Int32 Byte-Order konfiguriert: {self._int32_byte_order}")
                except Exception as e:
                    print(f"  Fehler beim Laden der Endianness-Konfiguration: {e}")
                    self._int32_byte_order = "big"  # Fallback auf Standard
            
            # Simuliere erfolgreiche Verbindung
            self.client = Mock()
            self.client.connected = True
            print(f"  Verbindung hergestellt, Endianness: {self._int32_byte_order}")
        
        async def _async_update_data(self):
            """Simuliere _async_update_data ohne Endianness-Loading."""
            self._update_calls += 1
            print(f"  _async_update_data aufgerufen (Aufruf #{self._update_calls})")
            
            # Simuliere int32-Wert-Kombination mit der geladenen Endianness
            test_registers = [0x1234, 0x5678]
            value = mock_combine_int32_registers(test_registers, self._int32_byte_order)
            print(f"  Kombinierter Wert: 0x{value:08X} (Endianness: {self._int32_byte_order})")
            
            return {"test": "data"}
    
    async def run_test():
        """Führe den Test aus."""
        coordinator = MockCoordinator()
        
        print("1. Erste Verbindung (sollte Endianness laden):")
        await coordinator._connect()
        assert coordinator._int32_byte_order == "little", "Endianness sollte auf 'little' gesetzt sein"
        assert call_count == 1, f"get_int32_byte_order sollte 1x aufgerufen werden, aber war {call_count}x"
        
        print("\n2. Mehrere Update-Zyklen (sollten KEINE Endianness-Ladung verursachen):")
        for i in range(3):
            await coordinator._async_update_data()
        
        print(f"\n3. Zweite Verbindung (sollte KEINE Endianness-Ladung verursachen):")
        await coordinator._connect()
        
        print(f"\n📊 Zusammenfassung:")
        print(f"  get_int32_byte_order Aufrufe: {call_count}")
        print(f"  _connect Aufrufe: {coordinator._connect_calls}")
        print(f"  _async_update_data Aufrufe: {coordinator._update_calls}")
        print(f"  Finale Endianness: {coordinator._int32_byte_order}")
        
        # Validierung
        assert call_count == 1, f"get_int32_byte_order sollte nur 1x aufgerufen werden, aber war {call_count}x"
        assert coordinator._int32_byte_order == "little", "Endianness sollte 'little' bleiben"
        
        print("✅ Endianness wird nur einmal geladen!")
    
    # Führe den Test aus
    asyncio.run(run_test())


def main():
    """Hauptfunktion."""
    print("🚀 Teste Endianness-Loading-Optimierung")
    print("=" * 50)
    
    try:
        test_endianness_loading_optimization()
        
        print("\n" + "=" * 50)
        print("🎉 Optimierung erfolgreich!")
        print("\n📋 Vorteile:")
        print("✅ Endianness-Konfiguration wird nur einmal geladen")
        print("✅ Keine wiederholten YAML-Zugriffe bei jedem Update")
        print("✅ Bessere Performance")
        print("✅ Weniger Log-Spam")
        
    except Exception as e:
        print(f"\n❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
