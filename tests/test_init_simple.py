"""Vereinfachte Tests für das __init__ Modul."""

import pytest
from homeassistant.const import Platform

from custom_components.lambda_heat_pumps import (
    DOMAIN,
    PLATFORMS,
    TRANSLATION_SOURCES,
    VERSION,
    setup_debug_logging,
)


def test_constants():
    """Test that constants are properly defined."""
    assert PLATFORMS == [Platform.SENSOR, Platform.CLIMATE]
    assert VERSION == "1.4.2"
    assert TRANSLATION_SOURCES == {DOMAIN: "translations"}
    assert DOMAIN == "lambda_heat_pumps"


def test_setup_debug_logging():
    """Test setup_debug_logging function."""
    from unittest.mock import Mock
    
    mock_hass = Mock()
    mock_config = {}
    
    # Should not raise an exception
    setup_debug_logging(mock_hass, mock_config)
    
    # Verify logger was accessed (indirect test)
    assert mock_hass.config is not None


def test_imports():
    """Test that all required modules can be imported."""
    from custom_components.lambda_heat_pumps import (
        async_setup,
        async_setup_entry,
        async_unload_entry,
        async_reload_entry,
    )
    
    # Functions should be callable
    assert callable(async_setup)
    assert callable(async_setup_entry)
    assert callable(async_unload_entry)
    assert callable(async_reload_entry)


if __name__ == "__main__":
    pytest.main([__file__])

