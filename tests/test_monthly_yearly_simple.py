#!/usr/bin/env python3
"""
Einfacher Test für Monthly und Yearly Energy Consumption Sensoren
Erstellt: 2025-01-14
Zweck: Testet die korrekte Logik der monthly und yearly Sensoren
"""

def test_monthly_yearly_logic():
    """Test der Monthly und Yearly Sensor-Logik."""
    
    print("🧪 Teste Monthly und Yearly Sensor-Logik...")
    
    # Simuliere Monthly Sensor
    class MockMonthlySensor:
        def __init__(self):
            self._energy_value = 0.0
            self._previous_monthly_value = 0.0
            self._reset_interval = "monthly"
            
        def set_energy_value(self, value):
            self._energy_value = value
            
        def native_value(self):
            return max(0.0, self._energy_value - self._previous_monthly_value)
            
        def handle_reset(self):
            # Speichere aktuellen Wert vor Reset
            self._previous_monthly_value = self._energy_value
            print(f"Monthly sensor: Saved previous value {self._previous_monthly_value:.2f} kWh")
            # Monthly sensor resettet NICHT den energy_value
    
    # Simuliere Yearly Sensor
    class MockYearlySensor:
        def __init__(self):
            self._energy_value = 0.0
            self._previous_yearly_value = 0.0
            self._reset_interval = "yearly"
            
        def set_energy_value(self, value):
            self._energy_value = value
            
        def native_value(self):
            return max(0.0, self._energy_value - self._previous_yearly_value)
            
        def handle_reset(self):
            # Speichere aktuellen Wert vor Reset
            self._previous_yearly_value = self._energy_value
            print(f"Yearly sensor: Saved previous value {self._previous_yearly_value:.2f} kWh")
            # Yearly sensor resettet NICHT den energy_value
    
    # Test Monthly Sensor
    print("\n📅 Teste Monthly Sensor:")
    monthly_sensor = MockMonthlySensor()
    
    # Simuliere Energie-Verbrauch über Zeit
    monthly_sensor.set_energy_value(100.0)
    print(f"Energy Value: {monthly_sensor._energy_value:.2f} kWh")
    print(f"Previous Monthly: {monthly_sensor._previous_monthly_value:.2f} kWh")
    print(f"Monthly Value: {monthly_sensor.native_value():.2f} kWh")
    
    # Simuliere Reset (1. des Monats)
    monthly_sensor.handle_reset()
    print(f"Nach Reset - Energy Value: {monthly_sensor._energy_value:.2f} kWh")
    print(f"Nach Reset - Previous Monthly: {monthly_sensor._previous_monthly_value:.2f} kWh")
    print(f"Nach Reset - Monthly Value: {monthly_sensor.native_value():.2f} kWh")
    
    # Simuliere weiteren Verbrauch
    monthly_sensor.set_energy_value(150.0)
    print(f"Neuer Energy Value: {monthly_sensor._energy_value:.2f} kWh")
    print(f"Monthly Value: {monthly_sensor.native_value():.2f} kWh")
    
    # Test Yearly Sensor
    print("\n📅 Teste Yearly Sensor:")
    yearly_sensor = MockYearlySensor()
    
    # Simuliere Energie-Verbrauch über Zeit
    yearly_sensor.set_energy_value(1000.0)
    print(f"Energy Value: {yearly_sensor._energy_value:.2f} kWh")
    print(f"Previous Yearly: {yearly_sensor._previous_yearly_value:.2f} kWh")
    print(f"Yearly Value: {yearly_sensor.native_value():.2f} kWh")
    
    # Simuliere Reset (1. Januar)
    yearly_sensor.handle_reset()
    print(f"Nach Reset - Energy Value: {yearly_sensor._energy_value:.2f} kWh")
    print(f"Nach Reset - Previous Yearly: {yearly_sensor._previous_yearly_value:.2f} kWh")
    print(f"Nach Reset - Yearly Value: {yearly_sensor.native_value():.2f} kWh")
    
    # Simuliere weiteren Verbrauch
    yearly_sensor.set_energy_value(1200.0)
    print(f"Neuer Energy Value: {yearly_sensor._energy_value:.2f} kWh")
    print(f"Yearly Value: {yearly_sensor.native_value():.2f} kWh")
    
    print("\n✅ Tests abgeschlossen!")
    print("\n📊 Erwartetes Verhalten:")
    print("- Monthly/Yearly Sensoren speichern den aktuellen Wert vor Reset")
    print("- Sie resettet NICHT den energy_value (nur daily/2h/4h tun das)")
    print("- Der native_value wird als Differenz berechnet: energy_value - previous_value")
    print("- Nach Reset sollte der native_value bei 0 starten und dann ansteigen")

if __name__ == "__main__":
    test_monthly_yearly_logic()
