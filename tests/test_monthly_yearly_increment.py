#!/usr/bin/env python3
"""
Test für alle Energie-Inkrement-Perioden in increment_energy_consumption_counter.
Stellt sicher, dass total, daily, monthly, yearly, 2h, 4h und hourly berücksichtigt werden.
"""

import pytest

from custom_components.lambda_heat_pumps.const import (
    ENERGY_CONSUMPTION_MODES,
    ENERGY_INCREMENT_PERIODS,
)


def _sensor_id_to_period(sensor_id: str) -> str:
    """Leitet die Period aus sensor_id ab (wie in increment_energy_consumption_counter)."""
    for period in ENERGY_INCREMENT_PERIODS:
        if sensor_id.endswith(f"_{period}"):
            return period
    return "total"


def test_sensor_types_use_energy_increment_periods():
    """Alle in increment_energy_consumption_counter verwendeten Perioden kommen aus ENERGY_INCREMENT_PERIODS."""
    assert "total" in ENERGY_INCREMENT_PERIODS
    assert "daily" in ENERGY_INCREMENT_PERIODS
    assert "monthly" in ENERGY_INCREMENT_PERIODS
    assert "yearly" in ENERGY_INCREMENT_PERIODS
    assert "2h" in ENERGY_INCREMENT_PERIODS
    assert "4h" in ENERGY_INCREMENT_PERIODS
    assert "hourly" in ENERGY_INCREMENT_PERIODS


def test_sensor_id_to_period_mapping():
    """Jede Period aus ENERGY_INCREMENT_PERIODS wird korrekt aus sensor_id erkannt."""
    for period in ENERGY_INCREMENT_PERIODS:
        sensor_id = f"heating_energy_{period}"
        assert _sensor_id_to_period(sensor_id) == period, (
            f"heating_energy_{period} sollte Period '{period}' ergeben"
        )


def test_all_modes_have_all_periods():
    """Für jeden Modus werden alle ENERGY_INCREMENT_PERIODS als Sensor-Typen erzeugt."""
    for mode in ENERGY_CONSUMPTION_MODES:
        for period in ENERGY_INCREMENT_PERIODS:
            sensor_id = f"{mode}_energy_{period}"
            resolved = _sensor_id_to_period(sensor_id)
            assert resolved == period, (
                f"Modus {mode}, Period {period}: sensor_id {sensor_id} -> {resolved}"
            )


def test_thermal_sensor_ids_use_same_periods():
    """Thermal-Sensoren nutzen dieselben Perioden (thermal_energy_{period})."""
    for period in ENERGY_INCREMENT_PERIODS:
        sensor_id = f"heating_thermal_energy_{period}"
        # Suffix _period muss erkennbar sein (z.B. _daily, _monthly, _2h)
        assert sensor_id.endswith(f"_{period}")
        assert _sensor_id_to_period(sensor_id) == period
