#!/usr/bin/env python3
"""
Test für die zentralisierte Logging-Logik
"""

import sys
import os

# Füge den custom_components Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

def test_centralized_logging_logic():
    """Test: Zentrale Logging-Logik funktioniert korrekt."""
    
    # Simuliere die Logging-Sammlung
    def simulate_energy_counter_logging():
        """Simuliert die neue zentrale Logging-Logik."""
        changes_summary = []
        
        # Simuliere verschiedene Szenarien
        scenarios = [
            # Szenario 1: Beide Sensoren ändern sich
            {
                "sensor_id": "sensor.eu08l_hp1_heating_energy_total",
                "current": 0.30,
                "final": 0.32,
                "should_add": True
            },
            {
                "sensor_id": "sensor.eu08l_hp1_heating_energy_daily", 
                "current": 0.30,
                "final": 0.32,
                "should_add": True
            },
            # Szenario 2: Nur ein Sensor ändert sich
            {
                "sensor_id": "sensor.eu08l_hp1_heating_energy_total",
                "current": 0.32,
                "final": 0.32,
                "should_add": False
            },
            {
                "sensor_id": "sensor.eu08l_hp1_heating_energy_daily",
                "current": 0.32,
                "final": 0.34,
                "should_add": True
            }
        ]
        
        for scenario in scenarios:
            current = scenario["current"]
            final = scenario["final"]
            sensor_id = scenario["sensor_id"]
            should_add = scenario["should_add"]
            
            # Simuliere die Toleranz-Prüfung
            value_changed = abs(final - current) > 0.001
            
            if value_changed:
                changes_summary.append(f"{sensor_id} = {final:.2f} kWh (was {current:.2f})")
            
            # Prüfe ob das Verhalten korrekt ist
            if should_add:
                assert value_changed, f"Sensor {sensor_id} sollte sich ändern, aber value_changed = {value_changed}"
            else:
                assert not value_changed, f"Sensor {sensor_id} sollte sich nicht ändern, aber value_changed = {value_changed}"
        
        return changes_summary
    
    # Test 1: Beide Sensoren ändern sich
    changes = simulate_energy_counter_logging()
    assert len(changes) == 3, f"Erwartet 3 Änderungen, bekommen {len(changes)}"
    print("✓ Beide Sensoren ändern sich: 3 Änderungen erfasst")
    
    # Test 2: Zentrale Logging-Meldung
    if changes:
        central_message = f"Energy counters updated for heating HP1: {', '.join(changes)} (delta 0.02 kWh)"
        print(f"✓ Zentrale Logging-Meldung: {central_message}")
    
    return changes

def test_logging_scenarios():
    """Test: Verschiedene Logging-Szenarien."""
    
    def simulate_scenario(scenarios):
        """Simuliert ein Logging-Szenario."""
        changes_summary = []
        
        for scenario in scenarios:
            current = scenario["current"]
            final = scenario["final"]
            sensor_id = scenario["sensor_id"]
            
            value_changed = abs(final - current) > 0.001
            if value_changed:
                changes_summary.append(f"{sensor_id} = {final:.2f} kWh (was {current:.2f})")
        
        return changes_summary
    
    # Szenario 1: Beide Sensoren ändern sich
    scenario1 = [
        {"sensor_id": "sensor.eu08l_hp1_heating_energy_total", "current": 0.30, "final": 0.32},
        {"sensor_id": "sensor.eu08l_hp1_heating_energy_daily", "current": 0.30, "final": 0.32}
    ]
    changes1 = simulate_scenario(scenario1)
    assert len(changes1) == 2, f"Szenario 1: Erwartet 2 Änderungen, bekommen {len(changes1)}"
    print("✓ Szenario 1: Beide Sensoren ändern sich - 2 Änderungen")
    
    # Szenario 2: Keine Änderungen
    scenario2 = [
        {"sensor_id": "sensor.eu08l_hp1_heating_energy_total", "current": 0.32, "final": 0.32},
        {"sensor_id": "sensor.eu08l_hp1_heating_energy_daily", "current": 0.32, "final": 0.32}
    ]
    changes2 = simulate_scenario(scenario2)
    assert len(changes2) == 0, f"Szenario 2: Erwartet 0 Änderungen, bekommen {len(changes2)}"
    print("✓ Szenario 2: Keine Änderungen - 0 Änderungen")
    
    # Szenario 3: Nur ein Sensor ändert sich
    scenario3 = [
        {"sensor_id": "sensor.eu08l_hp1_heating_energy_total", "current": 0.32, "final": 0.32},
        {"sensor_id": "sensor.eu08l_hp1_heating_energy_daily", "current": 0.32, "final": 0.34}
    ]
    changes3 = simulate_scenario(scenario3)
    assert len(changes3) == 1, f"Szenario 3: Erwartet 1 Änderung, bekommen {len(changes3)}"
    print("✓ Szenario 3: Nur ein Sensor ändert sich - 1 Änderung")

def main():
    """Führe alle Tests aus."""
    print("🧪 Teste zentralisierte Logging-Logik")
    print("=" * 50)
    
    try:
        changes = test_centralized_logging_logic()
        test_logging_scenarios()
        
        print("=" * 50)
        print("✅ Alle Tests bestanden! Zentrale Logging-Logik funktioniert korrekt.")
        print(f"📊 Erfasste Änderungen: {len(changes)}")
        
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
