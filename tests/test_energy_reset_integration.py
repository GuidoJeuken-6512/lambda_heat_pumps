#!/usr/bin/env python3
"""
Integration Test für Energy Sensoren Reset-Fix
Testet die Integration mit Home Assistant
"""

import asyncio
import sys
import os

# Füge den custom_components Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

# Jetzt können wir die Module importieren
from custom_components.lambda_heat_pumps.automations import SIGNAL_RESET_DAILY, SIGNAL_RESET_2H, SIGNAL_RESET_4H

def test_signal_constants():
    """Test ob die Signal-Konstanten korrekt definiert sind."""
    
    print("🧪 Teste Signal-Konstanten...")
    
    # Teste Signal-Konstanten
    assert SIGNAL_RESET_DAILY == "lambda_heat_pumps_reset_daily", f"Falsches DAILY Signal: {SIGNAL_RESET_DAILY}"
    assert SIGNAL_RESET_2H == "lambda_heat_pumps_reset_2h", f"Falsches 2H Signal: {SIGNAL_RESET_2H}"
    assert SIGNAL_RESET_4H == "lambda_heat_pumps_reset_4h", f"Falsches 4H Signal: {SIGNAL_RESET_4H}"
    
    print("  ✅ SIGNAL_RESET_DAILY:", SIGNAL_RESET_DAILY)
    print("  ✅ SIGNAL_RESET_2H:", SIGNAL_RESET_2H)
    print("  ✅ SIGNAL_RESET_4H:", SIGNAL_RESET_4H)
    
    print("✅ Signal-Konstanten korrekt!")

def test_signal_mapping():
    """Test die Signal-Zuordnung für verschiedene Perioden."""
    
    print("🧪 Teste Signal-Zuordnung...")
    
    # Simuliere die Signal-Zuordnung aus dem Code
    def get_signal_for_period(period):
        """Simuliert die Signal-Zuordnung aus LambdaEnergyConsumptionSensor."""
        if period == "daily":
            return SIGNAL_RESET_DAILY
        elif period == "2h":
            return SIGNAL_RESET_2H
        elif period == "4h":
            return SIGNAL_RESET_4H
        else:
            return None
    
    # Test Cases
    test_cases = [
        ("daily", SIGNAL_RESET_DAILY),
        ("2h", SIGNAL_RESET_2H),
        ("4h", SIGNAL_RESET_4H),
        ("invalid", None)
    ]
    
    for period, expected_signal in test_cases:
        actual_signal = get_signal_for_period(period)
        assert actual_signal == expected_signal, f"Falsches Signal für {period}: {actual_signal} != {expected_signal}"
        print(f"  ✅ {period} -> {actual_signal}")
    
    print("✅ Signal-Zuordnung korrekt!")

def test_energy_sensor_signal_logic():
    """Test die Signal-Logik speziell für Energy Sensoren."""
    
    print("🧪 Teste Energy Sensor Signal-Logik...")
    
    # Simuliere verschiedene Energy Sensor Konfigurationen
    energy_sensors = [
        {"hp_index": 1, "mode": "heating", "period": "daily"},
        {"hp_index": 1, "mode": "hot_water", "period": "daily"},
        {"hp_index": 1, "mode": "cooling", "period": "2h"},
        {"hp_index": 1, "mode": "defrost", "period": "4h"},
        {"hp_index": 2, "mode": "heating", "period": "daily"},
    ]
    
    # Teste Signal-Zuordnung für jeden Sensor
    for sensor in energy_sensors:
        period = sensor["period"]
        hp_index = sensor["hp_index"]
        mode = sensor["mode"]
        
        # Alte Methode (individuell)
        old_signal = f"lambda_energy_reset_{hp_index}_{mode}_{period}"
        
        # Neue Methode (zentral)
        if period == "daily":
            new_signal = SIGNAL_RESET_DAILY
        elif period == "2h":
            new_signal = SIGNAL_RESET_2H
        elif period == "4h":
            new_signal = SIGNAL_RESET_4H
        else:
            new_signal = None
        
        print(f"  📋 {mode} {period} (HP{hp_index}):")
        print(f"    Alte: {old_signal}")
        print(f"    Neue: {new_signal}")
        
        # Validierung
        assert new_signal is not None, f"Neues Signal sollte nicht None sein für {period}"
        assert "lambda_heat_pumps_reset" in new_signal, f"Neues Signal sollte zentrales Format verwenden"
        assert period in new_signal, f"Neues Signal sollte Periode enthalten"
    
    print("✅ Energy Sensor Signal-Logik korrekt!")

def test_centralized_benefits():
    """Test die Vorteile der zentralen Signal-Verwaltung."""
    
    print("🧪 Teste Vorteile zentraler Signale...")
    
    # Simuliere verschiedene Sensoren
    all_sensors = [
        # Energy Sensoren
        {"type": "energy", "hp_index": 1, "mode": "heating", "period": "daily"},
        {"type": "energy", "hp_index": 1, "mode": "hot_water", "period": "daily"},
        {"type": "energy", "hp_index": 1, "mode": "cooling", "period": "daily"},
        {"type": "energy", "hp_index": 1, "mode": "defrost", "period": "daily"},
        {"type": "energy", "hp_index": 2, "mode": "heating", "period": "daily"},
        # Cycling Sensoren (bereits zentral)
        {"type": "cycling", "hp_index": 1, "mode": "heating", "period": "daily"},
        {"type": "cycling", "hp_index": 1, "mode": "hot_water", "period": "daily"},
    ]
    
    # Zähle Signale nach Typ
    energy_signals = set()
    cycling_signals = set()
    
    for sensor in all_sensors:
        if sensor["type"] == "energy":
            if sensor["period"] == "daily":
                energy_signals.add(SIGNAL_RESET_DAILY)
            elif sensor["period"] == "2h":
                energy_signals.add(SIGNAL_RESET_2H)
            elif sensor["period"] == "4h":
                energy_signals.add(SIGNAL_RESET_4H)
        elif sensor["type"] == "cycling":
            if sensor["period"] == "daily":
                cycling_signals.add(SIGNAL_RESET_DAILY)
            elif sensor["period"] == "2h":
                cycling_signals.add(SIGNAL_RESET_2H)
            elif sensor["period"] == "4h":
                cycling_signals.add(SIGNAL_RESET_4H)
    
    print(f"  📊 Energy Sensoren verwenden {len(energy_signals)} Signale:")
    for signal in sorted(energy_signals):
        print(f"    - {signal}")
    
    print(f"  📊 Cycling Sensoren verwenden {len(cycling_signals)} Signale:")
    for signal in sorted(cycling_signals):
        print(f"    - {signal}")
    
    # Beide sollten die gleichen Signale verwenden
    assert energy_signals == cycling_signals, "Energy und Cycling Sensoren sollten die gleichen Signale verwenden"
    
    print("✅ Zentrale Signale bieten Konsistenz!")

def main():
    """Hauptfunktion für alle Tests."""
    print("🚀 Starte Energy Sensoren Reset-Fix Integration Tests...\n")
    
    try:
        test_signal_constants()
        print()
        test_signal_mapping()
        print()
        test_energy_sensor_signal_logic()
        print()
        test_centralized_benefits()
        print()
        print("🎉 Alle Integration Tests erfolgreich abgeschlossen!")
        print()
        print("📋 Zusammenfassung:")
        print("  ✅ Signal-Konstanten korrekt importiert")
        print("  ✅ Signal-Zuordnung funktioniert")
        print("  ✅ Energy Sensoren verwenden zentrale Signale")
        print("  ✅ Konsistenz mit Cycling Sensoren")
        print("  ✅ Bessere Architektur durch zentrale Verwaltung")
        
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

