#!/usr/bin/env python3
"""
Einfacher Test für Reset-Attribute Vereinfachung
Prüft, dass period und reset_signal aus den Templates entfernt wurden.
"""

import re

def test_reset_attributes_simplification():
    """Teste, dass period und reset_signal aus den Templates entfernt wurden."""
    print("=== Test: Reset-Attribute Vereinfachung ===\n")
    
    # Lese const.py
    with open('custom_components/lambda_heat_pumps/const.py', 'r') as f:
        content = f.read()
    
    # Suche nach period und reset_signal in Templates
    period_matches = re.findall(r'"period":\s*"[^"]*"', content)
    reset_signal_matches = re.findall(r'"reset_signal":\s*"[^"]*"', content)
    
    print(f"1. Gefundene 'period' Einträge: {len(period_matches)}")
    if period_matches:
        print("  ❌ period Einträge noch vorhanden:")
        for match in period_matches[:5]:  # Zeige erste 5
            print(f"    {match}")
        if len(period_matches) > 5:
            print(f"    ... und {len(period_matches) - 5} weitere")
    else:
        print("  ✅ Keine period Einträge gefunden")
    
    print()
    
    print(f"2. Gefundene 'reset_signal' Einträge: {len(reset_signal_matches)}")
    if reset_signal_matches:
        print("  ❌ reset_signal Einträge noch vorhanden:")
        for match in reset_signal_matches[:5]:  # Zeige erste 5
            print(f"    {match}")
        if len(reset_signal_matches) > 5:
            print(f"    ... und {len(reset_signal_matches) - 5} weitere")
    else:
        print("  ✅ Keine reset_signal Einträge gefunden")
    
    print()
    
    # Suche nach reset_interval
    reset_interval_matches = re.findall(r'"reset_interval":\s*"[^"]*"', content)
    print(f"3. Gefundene 'reset_interval' Einträge: {len(reset_interval_matches)}")
    if reset_interval_matches:
        print("  ✅ reset_interval Einträge gefunden:")
        for match in reset_interval_matches[:5]:  # Zeige erste 5
            print(f"    {match}")
        if len(reset_interval_matches) > 5:
            print(f"    ... und {len(reset_interval_matches) - 5} weitere")
    else:
        print("  ❌ Keine reset_interval Einträge gefunden")
    
    print()
    
    # Prüfe sensor.py
    with open('custom_components/lambda_heat_pumps/sensor.py', 'r') as f:
        sensor_content = f.read()
    
    period_usage = re.findall(r'self\._period', sensor_content)
    reset_interval_usage = re.findall(r'self\._reset_interval', sensor_content)
    
    print(f"4. Sensor.py - self._period Verwendung: {len(period_usage)}")
    print(f"5. Sensor.py - self._reset_interval Verwendung: {len(reset_interval_usage)}")
    
    if len(period_usage) == 0 and len(reset_interval_usage) > 0:
        print("  ✅ Korrekte Umstellung von _period auf _reset_interval")
    else:
        print("  ❌ Umstellung nicht vollständig")
    
    print("\n=== Test abgeschlossen ===")

if __name__ == "__main__":
    test_reset_attributes_simplification()

