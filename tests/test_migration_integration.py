"""Integrationstest für die neue Migration in __init__.py."""

import pytest
from unittest.mock import Mock, AsyncMock

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.lambda_heat_pumps.__init__ import async_migrate_entry


class TestMigrationIntegration:
    """Test-Klasse für die Migration-Integration in __init__.py."""
    
    @pytest.fixture
    def mock_hass(self):
        """Erstelle einen Mock für Home Assistant."""
        hass = Mock(spec=HomeAssistant)
        hass.async_add_executor_job = AsyncMock()
        return hass
    
    @pytest.fixture
    def mock_config_entry(self):
        """Erstelle einen Mock für Config Entry."""
        entry = Mock(spec=ConfigEntry)
        entry.entry_id = "test_entry_456"
        entry.version = 1
        return entry
    
    @pytest.mark.asyncio
    async def test_async_migrate_entry_function_exists(self):
        """Test: async_migrate_entry Funktion existiert und kann importiert werden."""
        assert callable(async_migrate_entry)
        assert async_migrate_entry.__name__ == "async_migrate_entry"
    
    @pytest.mark.asyncio
    async def test_async_migrate_entry_calls_structured_migration(
        self, mock_hass, mock_config_entry
    ):
        """Test: async_migrate_entry ruft die strukturierte Migration auf."""
        # Mock für die Migration-Funktion
        with pytest.MonkeyPatch().context() as m:
            # Mock der perform_structured_migration Funktion
            mock_migration = AsyncMock(return_value=True)
            m.setattr(
                "custom_components.lambda_heat_pumps.migration"
                ".perform_structured_migration",
                mock_migration
            )
            
            # Funktion aufrufen
            result = await async_migrate_entry(mock_hass, mock_config_entry)
            
            # Prüfen dass die Migration aufgerufen wurde
            mock_migration.assert_called_once_with(mock_hass, mock_config_entry)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_async_migrate_entry_handles_migration_failure(
        self, mock_hass, mock_config_entry
    ):
        """Test: async_migrate_entry behandelt Migrationsfehler korrekt."""
        # Mock für die Migration-Funktion die fehlschlägt
        with pytest.MonkeyPatch().context() as m:
            # Mock der perform_structured_migration Funktion
            mock_migration = AsyncMock(return_value=False)
            m.setattr(
                "custom_components.lambda_heat_pumps.migration"
                ".perform_structured_migration",
                mock_migration
            )
            
            # Funktion aufrufen
            result = await async_migrate_entry(mock_hass, mock_config_entry)
            
            # Prüfen dass die Migration aufgerufen wurde
            mock_migration.assert_called_once_with(mock_hass, mock_config_entry)
            assert result is False
    
    @pytest.mark.asyncio
    async def test_async_migrate_entry_handles_exceptions(
        self, mock_hass, mock_config_entry
    ):
        """Test: async_migrate_entry behandelt Exceptions korrekt."""
        # Mock für die Migration-Funktion die eine Exception wirft
        with pytest.MonkeyPatch().context() as m:
            # Mock der perform_structured_migration Funktion
            mock_migration = AsyncMock(side_effect=Exception("Test exception"))
            m.setattr(
                "custom_components.lambda_heat_pumps.migration"
                ".perform_structured_migration",
                mock_migration
            )
            
            # Funktion aufrufen
            result = await async_migrate_entry(mock_hass, mock_config_entry)
            
            # Prüfen dass die Migration aufgerufen wurde
            mock_migration.assert_called_once_with(mock_hass, mock_config_entry)
            assert result is False


if __name__ == "__main__":
    pytest.main([__file__])
