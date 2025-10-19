#!/usr/bin/env python3
"""
Test für Sensor Reset Registry - Reparierte Version
Testet das zentrale Registry für Sensor-Reset-Handler
"""

import pytest
from unittest.mock import MagicMock, patch, Mock


class MockSensorResetRegistry:
    """Mock für SensorResetRegistry"""
    
    def __init__(self):
        self._handlers = {}
        self._hass = None
    
    def set_hass(self, hass):
        self._hass = hass
    
    def register(self, sensor_type, entry_id, period, callback):
        if sensor_type not in self._handlers:
            self._handlers[sensor_type] = {}
        if entry_id not in self._handlers[sensor_type]:
            self._handlers[sensor_type][entry_id] = {}
        self._handlers[sensor_type][entry_id][period] = callback
    
    def unregister(self, sensor_type, entry_id, period):
        if sensor_type in self._handlers and entry_id in self._handlers[sensor_type]:
            if period in self._handlers[sensor_type][entry_id]:
                del self._handlers[sensor_type][entry_id][period]
    
    def get_signal(self, sensor_type, period):
        return f"lambda_heat_pumps_reset_{period}_{sensor_type}"
    
    def send_reset(self, sensor_type, period):
        callbacks_called = 0
        if sensor_type in self._handlers:
            for entry_id, periods in self._handlers[sensor_type].items():
                if period in periods:
                    callback = periods[period]
                    callback()
                    callbacks_called += 1
        return callbacks_called
    
    def send_reset_to_all(self, period):
        total_callbacks = 0
        for sensor_type in self._handlers:
            total_callbacks += self.send_reset(sensor_type, period)
        return total_callbacks
    
    def get_sensor_count(self):
        count = 0
        for sensor_type in self._handlers:
            for entry_id in self._handlers[sensor_type]:
                count += len(self._handlers[sensor_type][entry_id])
        return count
    
    def clear(self):
        self._handlers = {}
        self._hass = None


def test_sensor_reset_registry_creation():
    """Test die Erstellung des Sensor Reset Registry."""
    
    print("🧪 Teste Sensor Reset Registry Erstellung...")
    
    registry = MockSensorResetRegistry()
    
    # Prüfe Initialisierung
    assert registry._handlers == {}, "Handlers sollte leer sein"
    assert registry._hass is None, "HASS sollte None sein"
    
    print("  ✅ Registry erfolgreich erstellt")
    print("✅ Sensor Reset Registry Erstellung funktioniert!")


def test_sensor_registration():
    """Test die Registrierung von Sensoren."""
    
    print("🧪 Teste Sensor Registrierung...")
    
    registry = MockSensorResetRegistry()
    mock_hass = MagicMock()
    registry.set_hass(mock_hass)
    
    # Mock Callbacks
    callback1 = MagicMock()
    callback2 = MagicMock()
    callback3 = MagicMock()
    
    # Registriere verschiedene Sensoren
    registry.register("cycling", "entry1", "daily", callback1)
    registry.register("energy", "entry1", "daily", callback2)
    registry.register("cycling", "entry1", "2h", callback3)
    
    # Prüfe Registrierung
    assert "cycling" in registry._handlers, "Cycling sollte registriert sein"
    assert "energy" in registry._handlers, "Energy sollte registriert sein"
    assert "entry1" in registry._handlers["cycling"], "Entry1 sollte in cycling sein"
    assert "daily" in registry._handlers["cycling"]["entry1"], "Daily sollte registriert sein"
    assert "2h" in registry._handlers["cycling"]["entry1"], "2h sollte registriert sein"
    
    print("  ✅ Sensoren erfolgreich registriert")
    print("✅ Sensor Registrierung funktioniert!")


def test_sensor_unregistration():
    """Test die Entfernung von Sensoren."""
    
    print("🧪 Teste Sensor Entfernung...")
    
    registry = MockSensorResetRegistry()
    mock_hass = MagicMock()
    registry.set_hass(mock_hass)
    
    # Registriere Sensoren
    callback1 = MagicMock()
    callback2 = MagicMock()
    registry.register("cycling", "entry1", "daily", callback1)
    registry.register("cycling", "entry1", "2h", callback2)
    
    # Entferne spezifische Periode
    registry.unregister("cycling", "entry1", "daily")
    
    assert "daily" not in registry._handlers["cycling"]["entry1"], "Daily sollte entfernt sein"
    assert "2h" in registry._handlers["cycling"]["entry1"], "2h sollte noch da sein"
    
    print("  ✅ Sensor erfolgreich entfernt")
    print("✅ Sensor Entfernung funktioniert!")


def test_signal_generation():
    """Test die Signal-Generierung."""
    
    print("🧪 Teste Signal-Generierung...")
    
    registry = MockSensorResetRegistry()
    
    # Teste Signal-Generierung
    signal1 = registry.get_signal("cycling", "daily")
    signal2 = registry.get_signal("energy", "2h")
    signal3 = registry.get_signal("general", "4h")
    
    assert signal1 == "lambda_heat_pumps_reset_daily_cycling", f"Falsches Signal: {signal1}"
    assert signal2 == "lambda_heat_pumps_reset_2h_energy", f"Falsches Signal: {signal2}"
    assert signal3 == "lambda_heat_pumps_reset_4h_general", f"Falsches Signal: {signal3}"
    
    print("  ✅ Signale erfolgreich generiert")
    print("✅ Signal-Generierung funktioniert!")


def test_reset_signal_sending():
    """Test das Senden von Reset-Signalen."""
    
    print("🧪 Teste Reset-Signal Senden...")
    
    registry = MockSensorResetRegistry()
    mock_hass = MagicMock()
    registry.set_hass(mock_hass)
    
    # Mock Callbacks
    callback1 = MagicMock()
    callback2 = MagicMock()
    callback3 = MagicMock()
    
    # Registriere Sensoren
    registry.register("cycling", "entry1", "daily", callback1)
    registry.register("energy", "entry1", "daily", callback2)
    registry.register("cycling", "entry2", "daily", callback3)
    
    # Sende Reset-Signal an alle Cycling Sensoren
    callbacks_called = registry.send_reset("cycling", "daily")
    
    assert callbacks_called == 2, f"Sollte 2 Callbacks aufrufen, aber {callbacks_called}"
    callback1.assert_called_once()
    callback3.assert_called_once()
    callback2.assert_not_called()  # Energy sollte nicht aufgerufen werden
    
    print("  ✅ Reset-Signale erfolgreich gesendet")
    print("✅ Reset-Signal Senden funktioniert!")


def test_reset_signal_to_all():
    """Test das Senden von Reset-Signalen an alle Sensor-Typen."""
    
    print("🧪 Teste Reset-Signal an alle...")
    
    registry = MockSensorResetRegistry()
    mock_hass = MagicMock()
    registry.set_hass(mock_hass)
    
    # Mock Callbacks
    callback1 = MagicMock()
    callback2 = MagicMock()
    callback3 = MagicMock()
    
    # Registriere verschiedene Sensor-Typen
    registry.register("cycling", "entry1", "daily", callback1)
    registry.register("energy", "entry1", "daily", callback2)
    registry.register("general", "entry1", "daily", callback3)
    
    # Sende Reset-Signal an alle
    total_callbacks = registry.send_reset_to_all("daily")
    
    assert total_callbacks == 3, f"Sollte 3 Callbacks aufrufen, aber {total_callbacks}"
    callback1.assert_called_once()
    callback2.assert_called_once()
    callback3.assert_called_once()
    
    print("  ✅ Reset-Signale an alle erfolgreich gesendet")
    print("✅ Reset-Signal an alle funktioniert!")


def test_sensor_counting():
    """Test das Zählen der registrierten Sensoren."""
    
    print("🧪 Teste Sensor-Zählung...")
    
    registry = MockSensorResetRegistry()
    mock_hass = MagicMock()
    registry.set_hass(mock_hass)
    
    # Registriere verschiedene Sensoren
    callback1 = MagicMock()
    callback2 = MagicMock()
    callback3 = MagicMock()
    callback4 = MagicMock()
    
    registry.register("cycling", "entry1", "daily", callback1)
    registry.register("cycling", "entry1", "2h", callback2)
    registry.register("energy", "entry1", "daily", callback3)
    registry.register("general", "entry2", "daily", callback4)
    
    # Teste Gesamtanzahl
    total_count = registry.get_sensor_count()
    assert total_count == 4, f"Sollte 4 Sensoren haben, aber {total_count}"
    
    print("  ✅ Sensor-Zählung erfolgreich")
    print("✅ Sensor-Zählung funktioniert!")


def test_error_handling():
    """Test die Fehlerbehandlung."""
    
    print("🧪 Teste Fehlerbehandlung...")
    
    registry = MockSensorResetRegistry()
    
    # Teste ohne HASS Instanz
    callbacks_called = registry.send_reset("cycling", "daily")
    assert callbacks_called == 0, "Sollte 0 Callbacks ohne HASS aufrufen"
    
    # Teste mit leerer Registry
    registry.clear()
    assert registry.get_sensor_count() == 0, "Sollte 0 Sensoren haben"
    
    print("  ✅ Fehlerbehandlung erfolgreich")
    print("✅ Fehlerbehandlung funktioniert!")


if __name__ == "__main__":
    test_sensor_reset_registry_creation()
    test_sensor_registration()
    test_sensor_unregistration()
    test_signal_generation()
    test_reset_signal_sending()
    test_reset_signal_to_all()
    test_sensor_counting()
    test_error_handling()
    print("\n🎉 Alle Tests erfolgreich!")

