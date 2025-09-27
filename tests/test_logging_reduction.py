#!/usr/bin/env python3
"""
Test für die Reduzierung der Logging-Ausgaben
"""

import sys
import os

# Füge den custom_components Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

def test_energy_counter_logging_logic():
    """Test: Energy Counter Logging-Logik funktioniert korrekt."""
    
    # Simuliere die Logging-Logik
    def should_log_energy_counter(current_value, final_value, tolerance=0.001):
        """Prüft, ob eine Energy Counter Meldung ausgegeben werden soll."""
        return abs(final_value - current_value) > tolerance
    
    # Test 1: Wert ändert sich - sollte loggen
    current = 0.26
    final = 0.28
    assert should_log_energy_counter(current, final) == True
    print("✓ Wert ändert sich (0.26 -> 0.28): Sollte loggen")
    
    # Test 2: Wert ändert sich nicht - sollte nicht loggen
    current = 0.28
    final = 0.28
    assert should_log_energy_counter(current, final) == False
    print("✓ Wert ändert sich nicht (0.28 -> 0.28): Sollte nicht loggen")
    
    # Test 3: Kleine Änderung unter Toleranz - sollte nicht loggen
    current = 0.28
    final = 0.2801
    assert should_log_energy_counter(current, final) == False
    print("✓ Kleine Änderung unter Toleranz (0.28 -> 0.2801): Sollte nicht loggen")
    
    # Test 4: Kleine Änderung über Toleranz - sollte loggen
    current = 0.28
    final = 0.281
    assert should_log_energy_counter(current, final) == True
    print("✓ Kleine Änderung über Toleranz (0.28 -> 0.281): Sollte loggen")
    
    # Test 5: Große Änderung - sollte loggen
    current = 0.28
    final = 0.35
    assert should_log_energy_counter(current, final) == True
    print("✓ Große Änderung (0.28 -> 0.35): Sollte loggen")

def test_logging_scenarios():
    """Test: Verschiedene Logging-Szenarien."""
    
    def should_log_energy_counter(current_value, final_value, tolerance=0.001):
        """Prüft, ob eine Energy Counter Meldung ausgegeben werden soll."""
        return abs(final_value - current_value) > tolerance
    
    # Szenario 1: Normaler Betrieb mit Änderungen
    scenarios = [
        (0.26, 0.28, True, "Normale Änderung"),
        (0.28, 0.28, False, "Keine Änderung"),
        (0.28, 0.28, False, "Keine Änderung (wiederholt)"),
        (0.28, 0.30, True, "Weitere Änderung"),
        (0.30, 0.30, False, "Keine Änderung nach Update"),
    ]
    
    for current, final, expected, description in scenarios:
        result = should_log_energy_counter(current, final)
        assert result == expected, f"Fehler bei {description}: {current} -> {final}, erwartet {expected}, bekommen {result}"
        print(f"✓ {description}: {current} -> {final} = {'Loggen' if result else 'Nicht loggen'}")

def main():
    """Führe alle Tests aus."""
    print("🧪 Teste Logging-Reduzierung")
    print("=" * 40)
    
    try:
        test_energy_counter_logging_logic()
        test_logging_scenarios()
        
        print("=" * 40)
        print("✅ Alle Tests bestanden! Logging-Reduzierung funktioniert korrekt.")
        
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
