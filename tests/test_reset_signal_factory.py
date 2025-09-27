#!/usr/bin/env python3
"""
Test für Reset-Signal Factory
Testet die neuen Factory-Funktionen für Reset-Signale
"""

import sys
import os

# Füge den custom_components Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

from lambda_heat_pumps.utils import (
    create_reset_signal,
    get_reset_signal_for_period,
    get_all_reset_signals,
    validate_reset_signal
)

def test_create_reset_signal():
    """Test die create_reset_signal Funktion."""
    
    print("🧪 Teste create_reset_signal...")
    
    # Test Cases
    test_cases = [
        ("cycling", "daily", "lambda_heat_pumps_reset_daily_cycling"),
        ("energy", "daily", "lambda_heat_pumps_reset_daily_energy"),
        ("general", "daily", "lambda_heat_pumps_reset_daily_general"),
        ("cycling", "2h", "lambda_heat_pumps_reset_2h_cycling"),
        ("energy", "2h", "lambda_heat_pumps_reset_2h_energy"),
        ("general", "2h", "lambda_heat_pumps_reset_2h_general"),
        ("cycling", "4h", "lambda_heat_pumps_reset_4h_cycling"),
        ("energy", "4h", "lambda_heat_pumps_reset_4h_energy"),
        ("general", "4h", "lambda_heat_pumps_reset_4h_general"),
    ]
    
    for sensor_type, period, expected in test_cases:
        actual = create_reset_signal(sensor_type, period)
        assert actual == expected, f"Falsches Signal für {sensor_type} {period}: {actual} != {expected}"
        print(f"  ✅ {sensor_type} {period} -> {actual}")
    
    # Test ungültige Parameter
    try:
        create_reset_signal("invalid", "daily")
        assert False, "Sollte ValueError werfen für ungültigen sensor_type"
    except ValueError as e:
        print(f"  ✅ Korrekte Fehlerbehandlung für ungültigen sensor_type: {e}")
    
    try:
        create_reset_signal("cycling", "invalid")
        assert False, "Sollte ValueError werfen für ungültige period"
    except ValueError as e:
        print(f"  ✅ Korrekte Fehlerbehandlung für ungültige period: {e}")
    
    print("✅ create_reset_signal funktioniert!")

def test_get_reset_signal_for_period():
    """Test die get_reset_signal_for_period Funktion (rückwärtskompatibel)."""
    
    print("🧪 Teste get_reset_signal_for_period...")
    
    # Test Cases
    test_cases = [
        ("daily", "lambda_heat_pumps_reset_daily"),
        ("2h", "lambda_heat_pumps_reset_2h"),
        ("4h", "lambda_heat_pumps_reset_4h"),
    ]
    
    for period, expected in test_cases:
        actual = get_reset_signal_for_period(period)
        assert actual == expected, f"Falsches Signal für {period}: {actual} != {expected}"
        print(f"  ✅ {period} -> {actual}")
    
    # Test ungültige Parameter
    try:
        get_reset_signal_for_period("invalid")
        assert False, "Sollte ValueError werfen für ungültige period"
    except ValueError as e:
        print(f"  ✅ Korrekte Fehlerbehandlung für ungültige period: {e}")
    
    print("✅ get_reset_signal_for_period funktioniert!")

def test_get_all_reset_signals():
    """Test die get_all_reset_signals Funktion."""
    
    print("🧪 Teste get_all_reset_signals...")
    
    signals = get_all_reset_signals()
    
    # Prüfe Struktur
    assert isinstance(signals, dict), "Signals sollte ein Dictionary sein"
    assert len(signals) == 3, "Sollte 3 Sensor-Typen haben"
    
    sensor_types = ['cycling', 'energy', 'general']
    periods = ['daily', '2h', '4h']
    
    for sensor_type in sensor_types:
        assert sensor_type in signals, f"Sensor-Typ {sensor_type} fehlt"
        assert isinstance(signals[sensor_type], dict), f"Signals[{sensor_type}] sollte ein Dictionary sein"
        assert len(signals[sensor_type]) == 3, f"Sollte 3 Perioden für {sensor_type} haben"
        
        for period in periods:
            assert period in signals[sensor_type], f"Periode {period} fehlt für {sensor_type}"
            expected = create_reset_signal(sensor_type, period)
            actual = signals[sensor_type][period]
            assert actual == expected, f"Falsches Signal für {sensor_type} {period}: {actual} != {expected}"
            print(f"  ✅ {sensor_type} {period} -> {actual}")
    
    print("✅ get_all_reset_signals funktioniert!")

def test_validate_reset_signal():
    """Test die validate_reset_signal Funktion."""
    
    print("🧪 Teste validate_reset_signal...")
    
    # Gültige Signale
    valid_signals = [
        "lambda_heat_pumps_reset_daily_cycling",
        "lambda_heat_pumps_reset_daily_energy",
        "lambda_heat_pumps_reset_daily_general",
        "lambda_heat_pumps_reset_2h_cycling",
        "lambda_heat_pumps_reset_2h_energy",
        "lambda_heat_pumps_reset_2h_general",
        "lambda_heat_pumps_reset_4h_cycling",
        "lambda_heat_pumps_reset_4h_energy",
        "lambda_heat_pumps_reset_4h_general",
        "lambda_heat_pumps_reset_daily",  # Allgemeine Signale
        "lambda_heat_pumps_reset_2h",
        "lambda_heat_pumps_reset_4h",
    ]
    
    for signal in valid_signals:
        assert validate_reset_signal(signal), f"Signal sollte gültig sein: {signal}"
        print(f"  ✅ Gültig: {signal}")
    
    # Ungültige Signale
    invalid_signals = [
        "invalid_signal",
        "lambda_heat_pumps_reset_invalid_cycling",
        "lambda_heat_pumps_reset_daily_invalid",
        "lambda_heat_pumps_reset",
        "lambda_heat_pumps_reset_daily_cycling_extra",
        "",
        None,
        123,
    ]
    
    for signal in invalid_signals:
        assert not validate_reset_signal(signal), f"Signal sollte ungültig sein: {signal}"
        print(f"  ✅ Ungültig: {signal}")
    
    print("✅ validate_reset_signal funktioniert!")

def test_factory_consistency():
    """Test die Konsistenz zwischen verschiedenen Factory-Funktionen."""
    
    print("🧪 Teste Factory-Konsistenz...")
    
    # Teste dass get_reset_signal_for_period mit create_reset_signal konsistent ist
    periods = ['daily', '2h', '4h']
    
    for period in periods:
        general_signal = get_reset_signal_for_period(period)
        cycling_signal = create_reset_signal('cycling', period)
        energy_signal = create_reset_signal('energy', period)
        
        # Allgemeines Signal sollte das gleiche Format haben
        expected_general = f"lambda_heat_pumps_reset_{period}"
        assert general_signal == expected_general, f"Allgemeines Signal falsch: {general_signal}"
        
        # Spezifische Signale sollten das erweiterte Format haben
        expected_cycling = f"lambda_heat_pumps_reset_{period}_cycling"
        expected_energy = f"lambda_heat_pumps_reset_{period}_energy"
        
        assert cycling_signal == expected_cycling, f"Cycling Signal falsch: {cycling_signal}"
        assert energy_signal == expected_energy, f"Energy Signal falsch: {energy_signal}"
        
        print(f"  ✅ {period}: {general_signal} | {cycling_signal} | {energy_signal}")
    
    print("✅ Factory-Konsistenz korrekt!")

def main():
    """Hauptfunktion für alle Tests."""
    print("🚀 Starte Reset-Signal Factory Tests...\n")
    
    try:
        test_create_reset_signal()
        print()
        test_get_reset_signal_for_period()
        print()
        test_get_all_reset_signals()
        print()
        test_validate_reset_signal()
        print()
        test_factory_consistency()
        print()
        print("🎉 Alle Reset-Signal Factory Tests erfolgreich abgeschlossen!")
        print()
        print("📋 Zusammenfassung:")
        print("  ✅ create_reset_signal funktioniert für alle Kombinationen")
        print("  ✅ get_reset_signal_for_period ist rückwärtskompatibel")
        print("  ✅ get_all_reset_signals gibt alle Signale zurück")
        print("  ✅ validate_reset_signal erkennt gültige/ungültige Signale")
        print("  ✅ Alle Factory-Funktionen sind konsistent")
        print("  ✅ Fehlerbehandlung funktioniert korrekt")
        
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
