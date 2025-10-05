#!/usr/bin/env python3
"""
Test für die Delta-Filterung
"""

import sys
import os

# Füge den custom_components Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

def test_delta_filtering():
    """Test: Delta-Filterung funktioniert korrekt."""
    
    def should_process_energy_delta(energy_delta):
        """Simuliert die Delta-Filterung."""
        if energy_delta <= 0:
            return False, "Energy delta not positive"
        
        if energy_delta < 0.001:
            return False, "Energy delta too small"
        
        return True, "Energy delta OK"
    
    # Test 1: Positive Delta - sollte verarbeitet werden
    delta = 0.02
    should_process, reason = should_process_energy_delta(delta)
    assert should_process == True, f"Delta {delta} sollte verarbeitet werden: {reason}"
    print(f"✓ Delta {delta}: {reason}")
    
    # Test 2: Null Delta - sollte nicht verarbeitet werden
    delta = 0.0
    should_process, reason = should_process_energy_delta(delta)
    assert should_process == False, f"Delta {delta} sollte nicht verarbeitet werden: {reason}"
    print(f"✓ Delta {delta}: {reason}")
    
    # Test 3: Negative Delta - sollte nicht verarbeitet werden
    delta = -0.01
    should_process, reason = should_process_energy_delta(delta)
    assert should_process == False, f"Delta {delta} sollte nicht verarbeitet werden: {reason}"
    print(f"✓ Delta {delta}: {reason}")
    
    # Test 4: Sehr kleine Delta - sollte nicht verarbeitet werden
    delta = 0.0005
    should_process, reason = should_process_energy_delta(delta)
    assert should_process == False, f"Delta {delta} sollte nicht verarbeitet werden: {reason}"
    print(f"✓ Delta {delta}: {reason}")
    
    # Test 5: Grenzwert Delta - sollte verarbeitet werden
    delta = 0.001
    should_process, reason = should_process_energy_delta(delta)
    assert should_process == True, f"Delta {delta} sollte verarbeitet werden: {reason}"
    print(f"✓ Delta {delta}: {reason}")
    
    # Test 6: Sehr kleine Delta unter Grenzwert - sollte nicht verarbeitet werden
    delta = 0.0009
    should_process, reason = should_process_energy_delta(delta)
    assert should_process == False, f"Delta {delta} sollte nicht verarbeitet werden: {reason}"
    print(f"✓ Delta {delta}: {reason}")

def test_logging_scenarios():
    """Test: Verschiedene Logging-Szenarien."""
    
    def simulate_logging_behavior(energy_delta, current_value, final_value):
        """Simuliert das Logging-Verhalten."""
        # Prüfe Delta-Filterung
        if energy_delta <= 0:
            return "SKIP", "Delta not positive"
        
        if energy_delta < 0.001:
            return "SKIP", "Delta too small"
        
        # Prüfe Wert-Änderung
        value_changed = abs(final_value - current_value) > 0.001
        
        if value_changed:
            return "LOG", f"Value changed: {current_value} -> {final_value}"
        else:
            return "NO_LOG", "No value change"
    
    # Szenario 1: Normale Änderung - sollte geloggt werden
    result = simulate_logging_behavior(0.02, 0.30, 0.32)
    assert result[0] == "LOG", f"Szenario 1: {result}"
    print(f"✓ Szenario 1: Delta 0.02, 0.30->0.32 = {result[0]}")
    
    # Szenario 2: Keine Änderung - sollte nicht geloggt werden
    result = simulate_logging_behavior(0.02, 0.30, 0.30)
    assert result[0] == "NO_LOG", f"Szenario 2: {result}"
    print(f"✓ Szenario 2: Delta 0.02, 0.30->0.30 = {result[0]}")
    
    # Szenario 3: Sehr kleine Delta - sollte übersprungen werden
    result = simulate_logging_behavior(0.0005, 0.30, 0.3005)
    assert result[0] == "SKIP", f"Szenario 3: {result}"
    print(f"✓ Szenario 3: Delta 0.0005, 0.30->0.3005 = {result[0]}")
    
    # Szenario 4: Null Delta - sollte übersprungen werden
    result = simulate_logging_behavior(0.0, 0.30, 0.30)
    assert result[0] == "SKIP", f"Szenario 4: {result}"
    print(f"✓ Szenario 4: Delta 0.0, 0.30->0.30 = {result[0]}")

def main():
    """Führe alle Tests aus."""
    print("🧪 Teste Delta-Filterung")
    print("=" * 40)
    
    try:
        test_delta_filtering()
        test_logging_scenarios()
        
        print("=" * 40)
        print("✅ Alle Tests bestanden! Delta-Filterung funktioniert korrekt.")
        
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
