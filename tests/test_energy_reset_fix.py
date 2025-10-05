#!/usr/bin/env python3
"""
Test für Energy Reset Fix
Prüft, dass _handle_reset den entry_id Parameter korrekt akzeptiert.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'custom_components', 'lambda_heat_pumps'))

def test_energy_reset_fix():
    """Teste, dass _handle_reset den entry_id Parameter akzeptiert."""
    print("=== Test: Energy Reset Fix ===\n")
    
    # Lese sensor.py
    with open('custom_components/lambda_heat_pumps/sensor.py', 'r') as f:
        content = f.read()
    
    # Suche nach _handle_reset Definition
    import re
    handle_reset_matches = re.findall(r'def _handle_reset\([^)]*\):', content)
    
    print(f"Gefundene _handle_reset Definitionen: {len(handle_reset_matches)}")
    for match in handle_reset_matches:
        print(f"  {match}")
    
    # Prüfe, ob entry_id Parameter vorhanden ist
    if 'def _handle_reset(self, entry_id: str):' in content:
        print("  ✅ _handle_reset akzeptiert entry_id Parameter")
    elif 'def _handle_reset(self):' in content:
        print("  ❌ _handle_reset akzeptiert keinen entry_id Parameter")
    else:
        print("  ⚠️  _handle_reset Definition nicht gefunden")
    
    # Prüfe, ob es mehrere _handle_reset Methoden gibt
    if len(handle_reset_matches) > 1:
        print(f"  ⚠️  {len(handle_reset_matches)} _handle_reset Methoden gefunden")
        for i, match in enumerate(handle_reset_matches):
            print(f"    {i+1}. {match}")
    
    print("\n=== Test abgeschlossen ===")

if __name__ == "__main__":
    test_energy_reset_fix()