#!/usr/bin/env python3
"""
Test für vollständige Cycling Reset Funktionalität
Prüft, dass Daily Cycling Sensoren korrekt zurückgesetzt werden und Yesterday-Sensoren aktualisiert werden.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'custom_components', 'lambda_heat_pumps'))

def test_cycling_reset_complete():
    """Teste die vollständige Cycling Reset Funktionalität."""
    print("=== Test: Cycling Reset Funktionalität ===\n")
    
    # Lese sensor.py
    with open('custom_components/lambda_heat_pumps/sensor.py', 'r') as f:
        sensor_content = f.read()
    
    # Lese automations.py
    with open('custom_components/lambda_heat_pumps/automations.py', 'r') as f:
        automation_content = f.read()
    
    # 1. Prüfe Cycling Reset Handler
    print("1. Cycling Reset Handler:")
    
    # Suche nach _handle_daily_reset
    if 'def _handle_daily_reset(self, entry_id: str):' in sensor_content:
        print("  ✅ _handle_daily_reset akzeptiert entry_id Parameter")
    else:
        print("  ❌ _handle_daily_reset fehlt oder hat falsche Signatur")
    
    # Suche nach _handle_2h_reset
    if 'def _handle_2h_reset(self, entry_id: str):' in sensor_content:
        print("  ✅ _handle_2h_reset akzeptiert entry_id Parameter")
    else:
        print("  ❌ _handle_2h_reset fehlt oder hat falsche Signatur")
    
    # Suche nach _handle_4h_reset
    if 'def _handle_4h_reset(self, entry_id: str):' in sensor_content:
        print("  ✅ _handle_4h_reset akzeptiert entry_id Parameter")
    else:
        print("  ❌ _handle_4h_reset fehlt oder hat falsche Signatur")
    
    print()
    
    # 2. Prüfe Yesterday-Wert Übertragung
    print("2. Yesterday-Wert Übertragung:")
    
    # Suche nach update_yesterday_value
    if 'def update_yesterday_value(self):' in sensor_content:
        print("  ✅ update_yesterday_value Methode vorhanden")
    else:
        print("  ❌ update_yesterday_value Methode fehlt")
    
    # Suche nach _update_yesterday_sensors
    if 'def _update_yesterday_sensors(' in automation_content:
        print("  ✅ _update_yesterday_sensors Funktion vorhanden")
    else:
        print("  ❌ _update_yesterday_sensors Funktion fehlt")
    
    # Suche nach Yesterday-Sensor Update in reset_daily_sensors
    if '_update_yesterday_sensors(hass, entry_id)' in automation_content:
        print("  ✅ Yesterday-Sensoren werden vor Reset aktualisiert")
    else:
        print("  ❌ Yesterday-Sensoren werden nicht vor Reset aktualisiert")
    
    print()
    
    # 3. Prüfe Reset-Sequenz
    print("3. Reset-Sequenz:")
    
    # Suche nach der korrekten Reihenfolge
    reset_daily_pos = automation_content.find('def reset_daily_sensors')
    update_yesterday_pos = automation_content.find('_update_yesterday_sensors(hass, entry_id)')
    send_signal_pos = automation_content.find('async_dispatcher_send(hass, SIGNAL_RESET_DAILY, entry_id)')
    
    if reset_daily_pos < update_yesterday_pos < send_signal_pos:
        print("  ✅ Korrekte Reihenfolge: reset_daily_sensors -> _update_yesterday_sensors -> async_dispatcher_send")
    else:
        print("  ❌ Falsche Reihenfolge in reset_daily_sensors")
    
    print()
    
    # 4. Prüfe Yesterday-Sensor Implementierung
    print("4. Yesterday-Sensor Implementierung:")
    
    # Suche nach set_cycling_value
    if 'def set_cycling_value(self, value):' in sensor_content:
        print("  ✅ set_cycling_value Methode vorhanden")
    else:
        print("  ❌ set_cycling_value Methode fehlt")
    
    # Suche nach Yesterday-Sensor Entity-Klasse
    if 'class LambdaYesterdaySensor' in sensor_content:
        print("  ✅ LambdaYesterdaySensor Klasse vorhanden")
    else:
        print("  ❌ LambdaYesterdaySensor Klasse fehlt")
    
    print()
    
    # 5. Prüfe Daily-Berechnung
    print("5. Daily-Berechnung:")
    
    # Suche nach Daily-Wert Berechnung
    if 'return max(0.0, self._energy_value - self._yesterday_value)' in sensor_content:
        print("  ✅ Daily-Wert = Total - Yesterday (Energy)")
    else:
        print("  ❌ Daily-Wert Berechnung fehlt (Energy)")
    
    # Cycling Sensoren zeigen immer Total-Wert (korrekt)
    if 'return int(value)' in sensor_content and 'cycling_value' in sensor_content:
        print("  ✅ Cycling Sensoren zeigen Total-Wert (korrekt)")
    else:
        print("  ❌ Cycling Sensoren native_value fehlt")
    
    print("\n=== Test abgeschlossen ===")

if __name__ == "__main__":
    test_cycling_reset_complete()
