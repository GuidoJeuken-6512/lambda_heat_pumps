#!/usr/bin/env python3
"""
Test für Energy Periods Fix
Prüft, dass ENERGY_CONSUMPTION_PERIODS nicht leer ist.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'custom_components', 'lambda_heat_pumps'))

import const

def test_energy_periods_fix():
    """Teste den Energy Periods Fix."""
    print("=== Test: Energy Periods Fix ===\n")
    
    # 1. Prüfe ENERGY_CONSUMPTION_PERIODS
    print("1. ENERGY_CONSUMPTION_PERIODS:")
    print(f"  Werte: {const.ENERGY_CONSUMPTION_PERIODS}")
    print(f"  Anzahl: {len(const.ENERGY_CONSUMPTION_PERIODS)}")
    
    if len(const.ENERGY_CONSUMPTION_PERIODS) > 0:
        print("  ✅ ENERGY_CONSUMPTION_PERIODS ist nicht leer")
    else:
        print("  ❌ ENERGY_CONSUMPTION_PERIODS ist leer")
    
    print()
    
    # 2. Prüfe ENERGY_CONSUMPTION_MODES
    print("2. ENERGY_CONSUMPTION_MODES:")
    print(f"  Werte: {const.ENERGY_CONSUMPTION_MODES}")
    print(f"  Anzahl: {len(const.ENERGY_CONSUMPTION_MODES)}")
    
    if len(const.ENERGY_CONSUMPTION_MODES) > 0:
        print("  ✅ ENERGY_CONSUMPTION_MODES ist nicht leer")
    else:
        print("  ❌ ENERGY_CONSUMPTION_MODES ist leer")
    
    print()
    
    # 3. Prüfe erwartete Sensor-IDs
    print("3. Erwartete Sensor-IDs:")
    expected_sensors = []
    for mode in const.ENERGY_CONSUMPTION_MODES:
        for period in const.ENERGY_CONSUMPTION_PERIODS:
            sensor_id = f"{mode}_energy_{period}"
            expected_sensors.append(sensor_id)
            print(f"  {sensor_id}")
    
    print(f"\n  Erwartete Anzahl Sensoren: {len(expected_sensors)}")
    
    if len(expected_sensors) > 0:
        print("  ✅ Sensor-IDs werden generiert")
    else:
        print("  ❌ Keine Sensor-IDs werden generiert")
    
    print()
    
    # 4. Prüfe Templates
    print("4. Template-Verfügbarkeit:")
    missing_templates = []
    for sensor_id in expected_sensors:
        if sensor_id not in const.ENERGY_CONSUMPTION_SENSOR_TEMPLATES:
            missing_templates.append(sensor_id)
    
    if len(missing_templates) == 0:
        print(f"  ✅ Alle {len(expected_sensors)} Templates verfügbar")
    else:
        print(f"  ❌ {len(missing_templates)} Templates fehlen:")
        for template in missing_templates:
            print(f"    - {template}")
    
    print("\n=== Test abgeschlossen ===")

if __name__ == "__main__":
    test_energy_periods_fix()
