"""Tests für das Cycling-Offset-Tracking-System."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.lambda_heat_pumps.sensor import LambdaCyclingSensor


class TestCyclingOffsetTracking:
    """Test-Klasse für das Cycling-Offset-Tracking-System."""

    @pytest.fixture
    def mock_hass(self):
        """Mock Home Assistant instance."""
        hass = Mock(spec=HomeAssistant)
        hass.data = {}
        return hass

    @pytest.fixture
    def mock_entry(self):
        """Mock ConfigEntry."""
        entry = Mock(spec=ConfigEntry)
        entry.entry_id = "test_entry"
        return entry

    @pytest.fixture
    def cycling_sensor(self, mock_hass, mock_entry):
        """Erstelle einen LambdaCyclingSensor für Tests."""
        sensor = LambdaCyclingSensor(
            hass=mock_hass,
            entry=mock_entry,
            sensor_id="heating_cycling_total",
            name="Test Heating Cycling Total",
            entity_id="sensor.test_heating_cycling_total",
            unique_id="test_heating_cycling_total",
            unit="cycles",
            state_class="total_increasing",
            device_class=None,
            device_type="HP",
            hp_index=1,
        )
        return sensor

    @pytest.mark.asyncio
    async def test_first_time_offset_application(self, cycling_sensor, mock_hass):
        """Test: Erste Anwendung eines Offsets."""
        # Setup: Kein vorheriger Offset angewendet
        cycling_sensor._cycling_value = 0
        cycling_sensor._applied_offset = 0
        
        # Mock der Konfiguration
        mock_config = {
            "cycling_offsets": {
                "hp1": {
                    "heating_cycling_total": 30
                }
            }
        }
        
        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", 
                   return_value=mock_config):
            await cycling_sensor._apply_cycling_offset()
        
        # Assertions
        assert cycling_sensor._cycling_value == 30
        assert cycling_sensor._applied_offset == 30

    @pytest.mark.asyncio
    async def test_offset_increase(self, cycling_sensor, mock_hass):
        """Test: Erhöhung eines bestehenden Offsets."""
        # Setup: Offset bereits angewendet
        cycling_sensor._cycling_value = 100
        cycling_sensor._applied_offset = 30
        
        # Mock der Konfiguration - Offset wird von 30 auf 50 erhöht
        mock_config = {
            "cycling_offsets": {
                "hp1": {
                    "heating_cycling_total": 50
                }
            }
        }
        
        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", 
                   return_value=mock_config):
            await cycling_sensor._apply_cycling_offset()
        
        # Assertions: Nur die Differenz (20) wird addiert
        assert cycling_sensor._cycling_value == 120  # 100 + (50-30)
        assert cycling_sensor._applied_offset == 50

    @pytest.mark.asyncio
    async def test_offset_decrease(self, cycling_sensor, mock_hass):
        """Test: Verringerung eines bestehenden Offsets."""
        # Setup: Offset bereits angewendet
        cycling_sensor._cycling_value = 100
        cycling_sensor._applied_offset = 50
        
        # Mock der Konfiguration - Offset wird von 50 auf 30 verringert
        mock_config = {
            "cycling_offsets": {
                "hp1": {
                    "heating_cycling_total": 30
                }
            }
        }
        
        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", 
                   return_value=mock_config):
            await cycling_sensor._apply_cycling_offset()
        
        # Assertions: Die Differenz (-20) wird subtrahiert
        assert cycling_sensor._cycling_value == 80  # 100 + (30-50)
        assert cycling_sensor._applied_offset == 30

    @pytest.mark.asyncio
    async def test_offset_removal(self, cycling_sensor, mock_hass):
        """Test: Komplette Entfernung eines Offsets."""
        # Setup: Offset bereits angewendet
        cycling_sensor._cycling_value = 100
        cycling_sensor._applied_offset = 30
        
        # Mock der Konfiguration - Offset wird auf 0 gesetzt
        mock_config = {
            "cycling_offsets": {
                "hp1": {
                    "heating_cycling_total": 0
                }
            }
        }
        
        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", 
                   return_value=mock_config):
            await cycling_sensor._apply_cycling_offset()
        
        # Assertions: Der komplette Offset wird entfernt
        assert cycling_sensor._cycling_value == 70  # 100 + (0-30)
        assert cycling_sensor._applied_offset == 0

    @pytest.mark.asyncio
    async def test_no_offset_change(self, cycling_sensor, mock_hass):
        """Test: Keine Änderung des Offsets."""
        # Setup: Offset bereits angewendet
        cycling_sensor._cycling_value = 100
        cycling_sensor._applied_offset = 30
        
        # Mock der Konfiguration - Offset bleibt gleich
        mock_config = {
            "cycling_offsets": {
                "hp1": {
                    "heating_cycling_total": 30
                }
            }
        }
        
        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", 
                   return_value=mock_config):
            await cycling_sensor._apply_cycling_offset()
        
        # Assertions: Keine Änderung
        assert cycling_sensor._cycling_value == 100
        assert cycling_sensor._applied_offset == 30

    @pytest.mark.asyncio
    async def test_no_offset_configuration(self, cycling_sensor, mock_hass):
        """Test: Keine Offset-Konfiguration vorhanden."""
        # Setup: Offset bereits angewendet
        cycling_sensor._cycling_value = 100
        cycling_sensor._applied_offset = 30
        
        # Mock der Konfiguration - Keine Offsets
        mock_config = {
            "cycling_offsets": {}
        }
        
        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", 
                   return_value=mock_config):
            await cycling_sensor._apply_cycling_offset()
        
        # Assertions: Keine Änderung, da keine Konfiguration
        assert cycling_sensor._cycling_value == 100
        assert cycling_sensor._applied_offset == 30

    @pytest.mark.asyncio
    async def test_restore_state_with_applied_offset(self, cycling_sensor, mock_hass):
        """Test: Wiederherstellung des States mit angewendetem Offset."""
        # Mock des letzten States mit angewendetem Offset
        mock_last_state = Mock()
        mock_last_state.state = "100"
        mock_last_state.attributes = {"applied_offset": 30}
        
        # Mock der Konfiguration
        mock_config = {
            "cycling_offsets": {
                "hp1": {
                    "heating_cycling_total": 30
                }
            }
        }
        
        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", 
                   return_value=mock_config):
            await cycling_sensor.restore_state(mock_last_state)
        
        # Assertions
        assert cycling_sensor._cycling_value == 100
        assert cycling_sensor._applied_offset == 30

    @pytest.mark.asyncio
    async def test_restore_state_with_offset_change(self, cycling_sensor, mock_hass):
        """Test: Wiederherstellung des States mit Offset-Änderung."""
        # Mock des letzten States mit altem Offset
        mock_last_state = Mock()
        mock_last_state.state = "100"
        mock_last_state.attributes = {"applied_offset": 20}
        
        # Mock der Konfiguration - Neuer Offset
        mock_config = {
            "cycling_offsets": {
                "hp1": {
                    "heating_cycling_total": 50
                }
            }
        }
        
        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", 
                   return_value=mock_config):
            await cycling_sensor.restore_state(mock_last_state)
        
        # Assertions: Offset-Differenz wird angewendet
        assert cycling_sensor._cycling_value == 130  # 100 + (50-20)
        assert cycling_sensor._applied_offset == 50

    def test_extra_state_attributes_includes_applied_offset(self, cycling_sensor):
        """Test: Extra State Attributes enthalten den angewendeten Offset."""
        # Setup: Offset angewendet
        cycling_sensor._applied_offset = 30
        
        # Hole die Attribute
        attrs = cycling_sensor.extra_state_attributes
        
        # Assertions
        assert "applied_offset" in attrs
        assert attrs["applied_offset"] == 30

    def test_extra_state_attributes_no_offset_for_non_total_sensors(self, mock_hass, mock_entry):
        """Test: Kein applied_offset Attribut für Nicht-Total-Sensoren."""
        # Erstelle einen Daily-Sensor (nicht Total)
        daily_sensor = LambdaCyclingSensor(
            hass=mock_hass,
            entry=mock_entry,
            sensor_id="heating_cycling_daily",
            name="Test Heating Cycling Daily",
            entity_id="sensor.test_heating_cycling_daily",
            unique_id="test_heating_cycling_daily",
            unit="cycles",
            state_class="total",
            device_class=None,
            device_type="HP",
            hp_index=1,
        )
        
        # Hole die Attribute
        attrs = daily_sensor.extra_state_attributes
        
        # Assertions: applied_offset sollte nicht enthalten sein
        assert "applied_offset" not in attrs

    @pytest.mark.asyncio
    async def test_error_handling_in_offset_application(self, cycling_sensor, mock_hass):
        """Test: Fehlerbehandlung bei der Offset-Anwendung."""
        # Setup
        cycling_sensor._cycling_value = 100
        cycling_sensor._applied_offset = 30
        
        # Mock der Konfiguration mit Fehler
        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", 
                   side_effect=Exception("Config error")):
            await cycling_sensor._apply_cycling_offset()
        
        # Assertions: Keine Änderung bei Fehler
        assert cycling_sensor._cycling_value == 100
        assert cycling_sensor._applied_offset == 30


class TestCyclingOffsetIntegration:
    """Integrationstests für das Cycling-Offset-System."""

    @pytest.mark.asyncio
    async def test_complete_offset_workflow(self):
        """Test: Kompletter Workflow mit mehreren Offset-Änderungen."""
        # Setup
        mock_hass = Mock(spec=HomeAssistant)
        mock_entry = Mock(spec=ConfigEntry)
        mock_entry.entry_id = "test_entry"
        
        sensor = LambdaCyclingSensor(
            hass=mock_hass,
            entry=mock_entry,
            sensor_id="heating_cycling_total",
            name="Test Heating Cycling Total",
            entity_id="sensor.test_heating_cycling_total",
            unique_id="test_heating_cycling_total",
            unit="cycles",
            state_class="total_increasing",
            device_class=None,
            device_type="HP",
            hp_index=1,
        )
        
        # Schritt 1: Erste Anwendung (Offset: 30)
        mock_config_1 = {
            "cycling_offsets": {
                "hp1": {"heating_cycling_total": 30}
            }
        }
        
        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", 
                   return_value=mock_config_1):
            await sensor._apply_cycling_offset()
        
        assert sensor._cycling_value == 30
        assert sensor._applied_offset == 30
        
        # Schritt 2: Offset erhöhen (30 → 50)
        sensor._cycling_value = 100  # Simuliere Inkremente
        mock_config_2 = {
            "cycling_offsets": {
                "hp1": {"heating_cycling_total": 50}
            }
        }
        
        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", 
                   return_value=mock_config_2):
            await sensor._apply_cycling_offset()
        
        assert sensor._cycling_value == 120  # 100 + (50-30)
        assert sensor._applied_offset == 50
        
        # Schritt 3: Offset verringern (50 → 20)
        sensor._cycling_value = 150  # Simuliere weitere Inkremente
        mock_config_3 = {
            "cycling_offsets": {
                "hp1": {"heating_cycling_total": 20}
            }
        }
        
        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", 
                   return_value=mock_config_3):
            await sensor._apply_cycling_offset()
        
        assert sensor._cycling_value == 120  # 150 + (20-50)
        assert sensor._applied_offset == 20
        
        # Schritt 4: Offset entfernen (20 → 0)
        sensor._cycling_value = 200  # Simuliere weitere Inkremente
        mock_config_4 = {
            "cycling_offsets": {
                "hp1": {"heating_cycling_total": 0}
            }
        }
        
        with patch("custom_components.lambda_heat_pumps.utils.load_lambda_config", 
                   return_value=mock_config_4):
            await sensor._apply_cycling_offset()
        
        assert sensor._cycling_value == 180  # 200 + (0-20)
        assert sensor._applied_offset == 0
