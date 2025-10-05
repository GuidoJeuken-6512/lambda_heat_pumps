"""Test Energy Consumption Migration functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, mock_open
import yaml
import os

from custom_components.lambda_heat_pumps.migration import migrate_to_energy_consumption
from custom_components.lambda_heat_pumps.const_migration import (
    MigrationVersion,
    DEFAULT_ENERGY_CONSUMPTION_SENSORS,
    DEFAULT_ENERGY_CONSUMPTION_OFFSETS,
)


class TestEnergyConsumptionMigration:
    """Test energy consumption migration functionality."""

    @pytest.fixture
    def mock_hass(self):
        """Mock Home Assistant instance."""
        hass = Mock()
        hass.config.config_dir = "/config"
        hass.async_add_executor_job = AsyncMock()
        return hass

    @pytest.fixture
    def mock_config_entry(self):
        """Mock ConfigEntry instance."""
        entry = Mock()
        entry.entry_id = "test_entry_id"
        return entry

    @pytest.fixture
    def existing_config_content(self):
        """Existing lambda_wp_config.yaml content."""
        return """
disabled_registers:
  - 100000

sensors_names_override:
  - id: name_of_the_sensor_to_override_example
    override_name: new_name_of_the_sensor_example

cycling_offsets:
  hp1:
    heating_cycling_total: 0
    hot_water_cycling_total: 0
    cooling_cycling_total: 0
    defrost_cycling_total: 0
"""

    @pytest.fixture
    def config_with_energy_consumption(self):
        """Config that already has energy consumption sections."""
        return {
            "disabled_registers": [100000],
            "sensors_names_override": [],
            "cycling_offsets": {
                "hp1": {
                    "heating_cycling_total": 0,
                    "hot_water_cycling_total": 0,
                    "cooling_cycling_total": 0,
                    "defrost_cycling_total": 0,
                }
            },
            "energy_consumption_sensors": {
                "hp1": {
                    "sensor_entity_id": "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
                }
            },
            "energy_consumption_offsets": {
                "hp1": {
                    "heating_energy_total": 0,
                    "hot_water_energy_total": 0,
                    "cooling_energy_total": 0,
                    "defrost_energy_total": 0,
                }
            }
        }

    @pytest.mark.asyncio
    async def test_migration_with_existing_config(self, mock_hass, mock_config_entry, existing_config_content):
        """Test migration with existing configuration file."""
        # Setup mocks
        mock_hass.async_add_executor_job.side_effect = [
            True,  # os.path.exists returns True
            existing_config_content,  # File content
            None,  # File write operation
        ]
        
        with patch('os.path.exists', return_value=True):
            with patch('yaml.safe_load', return_value=yaml.safe_load(existing_config_content)):
                result = await migrate_to_energy_consumption(mock_hass, mock_config_entry)
        
        assert result is True
        # Verify that async_add_executor_job was called for file operations
        assert mock_hass.async_add_executor_job.call_count >= 2

    @pytest.mark.asyncio
    async def test_migration_with_no_existing_config(self, mock_hass, mock_config_entry):
        """Test migration with no existing configuration file."""
        # Setup mocks
        mock_hass.async_add_executor_job.side_effect = [
            False,  # os.path.exists returns False
            None,  # File write operation
        ]
        
        with patch('os.path.exists', return_value=False):
            result = await migrate_to_energy_consumption(mock_hass, mock_config_entry)
        
        assert result is True
        # Verify that async_add_executor_job was called for file operations
        assert mock_hass.async_add_executor_job.call_count >= 1

    @pytest.mark.asyncio
    async def test_migration_with_existing_energy_consumption(self, mock_hass, mock_config_entry, config_with_energy_consumption):
        """Test migration when energy consumption sections already exist."""
        # Setup mocks
        mock_hass.async_add_executor_job.side_effect = [
            True,  # os.path.exists returns True
            yaml.dump(config_with_energy_consumption),  # File content
        ]
        
        with patch('os.path.exists', return_value=True):
            with patch('yaml.safe_load', return_value=config_with_energy_consumption):
                result = await migrate_to_energy_consumption(mock_hass, mock_config_entry)
        
        assert result is True
        # Should not write file since sections already exist
        assert mock_hass.async_add_executor_job.call_count == 2

    @pytest.mark.asyncio
    async def test_migration_error_handling(self, mock_hass, mock_config_entry):
        """Test migration error handling."""
        # Setup mocks to raise an exception
        mock_hass.async_add_executor_job.side_effect = Exception("Test error")
        
        with patch('os.path.exists', return_value=True):
            result = await migrate_to_energy_consumption(mock_hass, mock_config_entry)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_migration_adds_energy_consumption_sensors(self, mock_hass, mock_config_entry, existing_config_content):
        """Test that migration adds energy consumption sensors section."""
        # Setup mocks
        config_data = yaml.safe_load(existing_config_content)
        mock_hass.async_add_executor_job.side_effect = [
            True,  # os.path.exists returns True
            existing_config_content,  # File content
            None,  # File write operation
        ]
        
        with patch('os.path.exists', return_value=True):
            with patch('yaml.safe_load', return_value=config_data):
                with patch('yaml.dump') as mock_yaml_dump:
                    result = await migrate_to_energy_consumption(mock_hass, mock_config_entry)
        
        assert result is True
        
        # Verify that yaml.dump was called with updated config
        call_args = mock_yaml_dump.call_args[0][0]
        assert "energy_consumption_sensors" in call_args
        assert "energy_consumption_offsets" in call_args
        assert call_args["energy_consumption_sensors"] == DEFAULT_ENERGY_CONSUMPTION_SENSORS
        assert call_args["energy_consumption_offsets"] == DEFAULT_ENERGY_CONSUMPTION_OFFSETS

    @pytest.mark.asyncio
    async def test_migration_adds_energy_consumption_offsets(self, mock_hass, mock_config_entry, existing_config_content):
        """Test that migration adds energy consumption offsets section."""
        # Setup mocks
        config_data = yaml.safe_load(existing_config_content)
        mock_hass.async_add_executor_job.side_effect = [
            True,  # os.path.exists returns True
            existing_config_content,  # File content
            None,  # File write operation
        ]
        
        with patch('os.path.exists', return_value=True):
            with patch('yaml.safe_load', return_value=config_data):
                with patch('yaml.dump') as mock_yaml_dump:
                    result = await migrate_to_energy_consumption(mock_hass, mock_config_entry)
        
        assert result is True
        
        # Verify that yaml.dump was called with updated config
        call_args = mock_yaml_dump.call_args[0][0]
        assert "energy_consumption_offsets" in call_args
        assert call_args["energy_consumption_offsets"] == DEFAULT_ENERGY_CONSUMPTION_OFFSETS

    def test_default_energy_consumption_sensors(self):
        """Test default energy consumption sensors configuration."""
        expected = {
            "hp1": {
                "sensor_entity_id": "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
            }
        }
        assert DEFAULT_ENERGY_CONSUMPTION_SENSORS == expected

    def test_default_energy_consumption_offsets(self):
        """Test default energy consumption offsets configuration."""
        expected = {
            "hp1": {
                "heating_energy_total": 0,
                "hot_water_energy_total": 0,
                "cooling_energy_total": 0,
                "defrost_energy_total": 0,
            }
        }
        assert DEFAULT_ENERGY_CONSUMPTION_OFFSETS == expected

    def test_migration_version_constant(self):
        """Test that energy consumption migration version is defined."""
        assert hasattr(MigrationVersion, 'ENERGY_CONSUMPTION')
        assert MigrationVersion.ENERGY_CONSUMPTION == 4

    @pytest.mark.asyncio
    async def test_migration_preserves_existing_config(self, mock_hass, mock_config_entry, existing_config_content):
        """Test that migration preserves existing configuration."""
        # Setup mocks
        config_data = yaml.safe_load(existing_config_content)
        mock_hass.async_add_executor_job.side_effect = [
            True,  # os.path.exists returns True
            existing_config_content,  # File content
            None,  # File write operation
        ]
        
        with patch('os.path.exists', return_value=True):
            with patch('yaml.safe_load', return_value=config_data):
                with patch('yaml.dump') as mock_yaml_dump:
                    result = await migrate_to_energy_consumption(mock_hass, mock_config_entry)
        
        assert result is True
        
        # Verify that existing config is preserved
        call_args = mock_yaml_dump.call_args[0][0]
        assert "disabled_registers" in call_args
        assert "sensors_names_override" in call_args
        assert "cycling_offsets" in call_args
        assert call_args["disabled_registers"] == [100000]
        assert call_args["cycling_offsets"]["hp1"]["heating_cycling_total"] == 0

    @pytest.mark.asyncio
    async def test_migration_with_empty_config(self, mock_hass, mock_config_entry):
        """Test migration with empty configuration file."""
        # Setup mocks
        mock_hass.async_add_executor_job.side_effect = [
            True,  # os.path.exists returns True
            "",  # Empty file content
            None,  # File write operation
        ]
        
        with patch('os.path.exists', return_value=True):
            with patch('yaml.safe_load', return_value=None):
                result = await migrate_to_energy_consumption(mock_hass, mock_config_entry)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_migration_with_invalid_yaml(self, mock_hass, mock_config_entry):
        """Test migration with invalid YAML content."""
        # Setup mocks
        mock_hass.async_add_executor_job.side_effect = [
            True,  # os.path.exists returns True
            "invalid yaml content",  # Invalid YAML
            None,  # File write operation
        ]
        
        with patch('os.path.exists', return_value=True):
            with patch('yaml.safe_load', return_value=None):
                result = await migrate_to_energy_consumption(mock_hass, mock_config_entry)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_migration_file_write_error(self, mock_hass, mock_config_entry, existing_config_content):
        """Test migration with file write error."""
        # Setup mocks
        config_data = yaml.safe_load(existing_config_content)
        mock_hass.async_add_executor_job.side_effect = [
            True,  # os.path.exists returns True
            existing_config_content,  # File content
            Exception("Write error"),  # File write operation fails
        ]
        
        with patch('os.path.exists', return_value=True):
            with patch('yaml.safe_load', return_value=config_data):
                result = await migrate_to_energy_consumption(mock_hass, mock_config_entry)
        
        assert result is False



