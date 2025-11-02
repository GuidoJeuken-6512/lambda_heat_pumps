"""Test the services module."""

import importlib
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from custom_components.lambda_heat_pumps.services import async_setup_services


class TestServices:
    """Test the services module."""

    def test_service_schemas(self):
        """Test that service schemas are properly defined."""
        try:
            from custom_components.lambda_heat_pumps.services import SERVICE_SCHEMAS

            assert isinstance(SERVICE_SCHEMAS, dict)
            assert len(SERVICE_SCHEMAS) > 0
        except ImportError:
            pytest.skip("SERVICE_SCHEMAS nicht vorhanden")

        # Check that each service has required fields
        for service_name, schema in SERVICE_SCHEMAS.items():
            assert "name" in schema
            assert "description" in schema
            assert "fields" in schema


@pytest.mark.asyncio
async def test_setup_services_async(mock_hass):
    """Test async setup services."""
    from unittest.mock import MagicMock
    
    # Ensure hass.data is a dictionary (iterable)
    if not isinstance(mock_hass.data, dict):
        mock_hass.data = {}
    
    mock_hass.loop = Mock()
    mock_hass.loop.time = Mock(return_value=1000.0)
    mock_hass.services = MagicMock()
    mock_hass.services.async_register = AsyncMock()

    with patch(
        "custom_components.lambda_heat_pumps.services.async_track_time_interval"
    ) as mock_track:
        await async_setup_services(mock_hass)

        mock_hass.services.async_register.assert_called()
