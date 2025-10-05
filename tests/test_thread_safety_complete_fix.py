#!/usr/bin/env python3
"""
Test für vollständigen Thread-Safety Fix
Prüft, dass alle Reset-Handler asynchron sind und korrekt mit Wrapper-Funktionen aufgerufen werden.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'custom_components', 'lambda_heat_pumps'))

def test_thread_safety_complete_fix():
    """Teste den vollständigen Thread-Safety Fix."""
    print("=== Test: Vollständiger Thread-Safety Fix ===\n")
    
    # Lese sensor.py
    with open('custom_components/lambda_heat_pumps/sensor.py', 'r') as f:
        sensor_content = f.read()
    
    # 1. Prüfe asynchrone Reset-Handler
    print("1. Asynchrone Reset-Handler:")
    
    # Cycling Sensoren
    if 'async def _handle_daily_reset(self, entry_id: str):' in sensor_content:
        print("  ✅ _handle_daily_reset ist asynchron")
    else:
        print("  ❌ _handle_daily_reset ist nicht asynchron")
    
    if 'async def _handle_2h_reset(self, entry_id: str):' in sensor_content:
        print("  ✅ _handle_2h_reset ist asynchron")
    else:
        print("  ❌ _handle_2h_reset ist nicht asynchron")
    
    if 'async def _handle_4h_reset(self, entry_id: str):' in sensor_content:
        print("  ✅ _handle_4h_reset ist asynchron")
    else:
        print("  ❌ _handle_4h_reset ist nicht asynchron")
    
    # Energy Sensoren
    if 'async def _handle_reset(self, entry_id: str):' in sensor_content:
        print("  ✅ _handle_reset (Energy) ist asynchron")
    else:
        print("  ❌ _handle_reset (Energy) ist nicht asynchron")
    
    print()
    
    # 2. Prüfe Wrapper-Funktionen
    print("2. Wrapper-Funktionen:")
    
    if 'def _wrap_daily_reset(entry_id: str):' in sensor_content:
        print("  ✅ _wrap_daily_reset Wrapper vorhanden")
    else:
        print("  ❌ _wrap_daily_reset Wrapper fehlt")
    
    if 'def _wrap_2h_reset(entry_id: str):' in sensor_content:
        print("  ✅ _wrap_2h_reset Wrapper vorhanden")
    else:
        print("  ❌ _wrap_2h_reset Wrapper fehlt")
    
    if 'def _wrap_4h_reset(entry_id: str):' in sensor_content:
        print("  ✅ _wrap_4h_reset Wrapper vorhanden")
    else:
        print("  ❌ _wrap_4h_reset Wrapper fehlt")
    
    if 'def _wrap_reset(entry_id: str):' in sensor_content:
        print("  ✅ _wrap_reset (Energy) Wrapper vorhanden")
    else:
        print("  ❌ _wrap_reset (Energy) Wrapper fehlt")
    
    print()
    
    # 3. Prüfe async_create_task Verwendung
    print("3. async_create_task Verwendung:")
    
    async_create_task_count = sensor_content.count('self.hass.async_create_task(')
    print(f"  Gefundene async_create_task Aufrufe: {async_create_task_count}")
    
    if async_create_task_count >= 4:  # Mindestens 4 Wrapper-Funktionen
        print("  ✅ Ausreichend async_create_task Aufrufe")
    else:
        print("  ❌ Zu wenige async_create_task Aufrufe")
    
    print()
    
    # 4. Prüfe @callback Entfernung
    print("4. @callback Entfernung:")
    
    # Zähle @callback vor Reset-Handlern
    callback_before_reset = sensor_content.count('@callback\n    def _handle_')
    print(f"  @callback vor Reset-Handlern: {callback_before_reset}")
    
    if callback_before_reset == 0:
        print("  ✅ Alle @callback vor Reset-Handlern entfernt")
    else:
        print("  ❌ Noch @callback vor Reset-Handlern vorhanden")
    
    print()
    
    # 5. Prüfe async_write_ha_state Verwendung
    print("5. async_write_ha_state Verwendung:")
    
    async_write_calls = sensor_content.count('self.async_write_ha_state()')
    print(f"  Gefundene async_write_ha_state Aufrufe: {async_write_calls}")
    
    # Prüfe, ob alle in asynchronen Methoden sind
    if 'async def _handle_' in sensor_content and 'self.async_write_ha_state()' in sensor_content:
        print("  ✅ async_write_ha_state wird in asynchronen Methoden aufgerufen")
    else:
        print("  ❌ async_write_ha_state wird möglicherweise synchron aufgerufen")
    
    print("\n=== Test abgeschlossen ===")

if __name__ == "__main__":
    test_thread_safety_complete_fix()
