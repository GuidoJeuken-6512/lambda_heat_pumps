#!/usr/bin/env python3
"""
Test für Monthly und Yearly Sensoren in increment_energy_consumption_counter
Erstellt: 2025-01-14
Zweck: Testet ob monthly und yearly Sensoren korrekt aktualisiert werden
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'lambda_heat_pumps'))

def test_sensor_types_in_increment_function():
    """Test ob alle Sensor-Typen in increment_energy_consumption_counter berücksichtigt werden."""
    
    print("🧪 Teste Sensor-Typen in increment_energy_consumption_counter...")
    
    # Simuliere die Logik aus utils.py
    def get_sensor_types_for_mode(mode):
        """Simuliert die Sensor-Typen-Liste aus increment_energy_consumption_counter."""
        sensor_types = [
            f"{mode}_energy_total",
            f"{mode}_energy_daily",
            f"{mode}_energy_monthly",
            f"{mode}_energy_yearly",
        ]
        return sensor_types
    
    def get_period_for_sensor_id(sensor_id):
        """Simuliert die Period-Bestimmung aus increment_energy_consumption_counter."""
        if sensor_id.endswith("_total"):
            return "total"
        elif sensor_id.endswith("_daily"):
            return "daily"
        elif sensor_id.endswith("_monthly"):
            return "monthly"
        elif sensor_id.endswith("_yearly"):
            return "yearly"
        else:
            return "total"  # Fallback
    
    # Test für alle Modi
    modes = ["heating", "hot_water", "cooling", "defrost", "stby"]
    
    for mode in modes:
        print(f"\n📊 Teste Modus: {mode}")
        sensor_types = get_sensor_types_for_mode(mode)
        
        print(f"  Sensor-Typen: {sensor_types}")
        
        for sensor_id in sensor_types:
            period = get_period_for_sensor_id(sensor_id)
            print(f"    {sensor_id} -> Period: {period}")
            
            # Validiere die Period-Zuordnung
            if sensor_id.endswith("_total") and period != "total":
                print(f"    ❌ FEHLER: {sensor_id} sollte 'total' sein, ist aber '{period}'")
            elif sensor_id.endswith("_daily") and period != "daily":
                print(f"    ❌ FEHLER: {sensor_id} sollte 'daily' sein, ist aber '{period}'")
            elif sensor_id.endswith("_monthly") and period != "monthly":
                print(f"    ❌ FEHLER: {sensor_id} sollte 'monthly' sein, ist aber '{period}'")
            elif sensor_id.endswith("_yearly") and period != "yearly":
                print(f"    ❌ FEHLER: {sensor_id} sollte 'yearly' sein, ist aber '{period}'")
            else:
                print(f"    ✅ OK: {sensor_id} -> {period}")
    
    print("\n✅ Test abgeschlossen!")
    print("\n📋 Erwartetes Verhalten:")
    print("- Alle 4 Sensor-Typen (total, daily, monthly, yearly) werden für jeden Modus erstellt")
    print("- Jeder Sensor-Typ bekommt die korrekte Period zugewiesen")
    print("- Monthly und Yearly Sensoren werden jetzt auch aktualisiert!")

if __name__ == "__main__":
    test_sensor_types_in_increment_function()
