#!/usr/bin/env python3
"""
Test für Reset-Attribute Vereinfachung
Prüft, dass nur noch reset_interval verwendet wird und period/reset_signal entfernt wurden.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'custom_components', 'lambda_heat_pumps'))

# Direkte Imports ohne relative Imports
import const
import utils

def test_reset_attributes_simplification():
    """Teste, dass nur noch reset_interval verwendet wird."""
    print("=== Test: Reset-Attribute Vereinfachung ===\n")
    
    # 1. Prüfe Energy Consumption Templates
    print("1. Energy Consumption Templates:")
    for sensor_id, template in const.ENERGY_CONSUMPTION_SENSOR_TEMPLATES.items():
        if "reset_interval" in template:
            print(f"  ✅ {sensor_id}: reset_interval = {template['reset_interval']}")
            
            # Prüfe, dass period und reset_signal entfernt wurden
            if "period" in template:
                print(f"  ❌ {sensor_id}: period noch vorhanden: {template['period']}")
            if "reset_signal" in template:
                print(f"  ❌ {sensor_id}: reset_signal noch vorhanden: {template['reset_signal']}")
        else:
            print(f"  ⚠️  {sensor_id}: kein reset_interval")
    
    print()
    
    # 2. Prüfe Cycling Templates
    print("2. Cycling Templates:")
    cycling_templates = {k: v for k, v in const.CALCULATED_SENSOR_TEMPLATES.items() 
                        if 'cycling' in v.get("name", "").lower() and "reset_interval" in v}
    
    for sensor_id, template in cycling_templates.items():
        print(f"  ✅ {sensor_id}: reset_interval = {template['reset_interval']}")
        
        # Prüfe, dass period und reset_signal entfernt wurden
        if "period" in template:
            print(f"  ❌ {sensor_id}: period noch vorhanden: {template['period']}")
        if "reset_signal" in template:
            print(f"  ❌ {sensor_id}: reset_signal noch vorhanden: {template['reset_signal']}")
    
    print()
    
    # 3. Prüfe Funktionen
    print("3. Funktionen:")
    periods = const.get_energy_consumption_periods()
    print(f"  ✅ get_energy_consumption_periods(): {periods}")
    
    all_periods = const.get_all_periods()
    print(f"  ✅ get_all_periods(): {all_periods}")
    
    # 4. Prüfe Signal-Generierung
    print("\n4. Signal-Generierung:")
    for period in periods:
        signal = utils.get_reset_signal_for_period(period)
        print(f"  ✅ {period} -> {signal}")
    
    print("\n=== Test abgeschlossen ===")

if __name__ == "__main__":
    test_reset_attributes_simplification()
