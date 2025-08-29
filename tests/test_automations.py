"""Test the automations module."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch
from datetime import datetime

import pytest
from homeassistant.core import HomeAssistant

from custom_components.lambda_heat_pumps.automations import (
    setup_cycling_automations,
    cleanup_cycling_automations,
    SIGNAL_UPDATE_YESTERDAY,
    SIGNAL_UPDATE_2H,
    SIGNAL_UPDATE_4H,
)


@pytest.fixture
def mock_hass():
    """Create a mock hass object."""
    hass = Mock()
    hass.data = {}
    hass.helpers = Mock()
    hass.helpers.event = Mock()
    hass.helpers.event.async_track_time_change = Mock()
    return hass


@pytest.fixture
def mock_entry():
    """Create a mock config entry."""
    entry = Mock()
    entry.entry_id = "test_entry"
    return entry


@patch('custom_components.lambda_heat_pumps.automations.async_track_time_change')
def test_setup_cycling_automations(mock_track_time_change, mock_hass, mock_entry):
    """Test setup_cycling_automations function."""
    # Mock async_track_time_change to return a mock listener
    mock_listener = Mock()
    mock_track_time_change.return_value = mock_listener
    
    # Call the function
    setup_cycling_automations(mock_hass, mock_entry.entry_id)
    
    # Verify that async_track_time_change was called 3 times (yesterday, 2h, 4h)
    assert mock_track_time_change.call_count == 3
    
    # Verify the calls
    calls = mock_track_time_change.call_args_list
    
    # First call should be for yesterday (midnight)
    yesterday_call = calls[0]
    assert yesterday_call[1]["hour"] == 0
    assert yesterday_call[1]["minute"] == 0
    assert yesterday_call[1]["second"] == 0
    
    # Second call should be for 2h updates
    two_hour_call = calls[1]
    assert two_hour_call[1]["hour"] == [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
    assert two_hour_call[1]["minute"] == 0
    assert two_hour_call[1]["second"] == 0
    
    # Third call should be for 4h updates
    four_hour_call = calls[2]
    assert four_hour_call[1]["hour"] == [0, 4, 8, 12, 16, 20]
    assert four_hour_call[1]["minute"] == 0
    assert four_hour_call[1]["second"] == 0
    
    # Verify that listeners are stored in hass.data
    assert "lambda_heat_pumps" in mock_hass.data
    assert mock_entry.entry_id in mock_hass.data["lambda_heat_pumps"]
    entry_data = mock_hass.data["lambda_heat_pumps"][mock_entry.entry_id]
    assert "yesterday_listener" in entry_data
    assert "two_hour_listener" in entry_data
    assert "four_hour_listener" in entry_data


def test_cleanup_cycling_automations(mock_hass, mock_entry):
    """Test cleanup_cycling_automations function."""
    # Setup mock data with listeners
    mock_listener1 = Mock()
    mock_listener2 = Mock()
    mock_listener3 = Mock()
    
    mock_hass.data = {
        "lambda_heat_pumps": {
            mock_entry.entry_id: {
                "yesterday_listener": mock_listener1,
                "two_hour_listener": mock_listener2,
                "four_hour_listener": mock_listener3,
            }
        }
    }
    
    # Call cleanup function
    cleanup_cycling_automations(mock_hass, mock_entry.entry_id)
    
    # Verify that all listeners were called (to unsubscribe)
    mock_listener1.assert_called_once()
    mock_listener2.assert_called_once()
    mock_listener3.assert_called_once()
    
    # Verify that listeners were removed from data
    entry_data = mock_hass.data["lambda_heat_pumps"][mock_entry.entry_id]
    assert "yesterday_listener" not in entry_data
    assert "two_hour_listener" not in entry_data
    assert "four_hour_listener" not in entry_data


def test_cleanup_cycling_automations_no_data(mock_hass, mock_entry):
    """Test cleanup_cycling_automations when no data exists."""
    # Call cleanup function with no data
    cleanup_cycling_automations(mock_hass, mock_entry.entry_id)
    
    # Should not raise any exceptions
    assert True


def test_cleanup_cycling_automations_no_entry(mock_hass, mock_entry):
    """Test cleanup_cycling_automations when entry doesn't exist."""
    # Setup data but without the entry
    mock_hass.data = {"lambda_heat_pumps": {}}
    
    # Call cleanup function
    cleanup_cycling_automations(mock_hass, mock_entry.entry_id)
    
    # Should not raise any exceptions
    assert True


def test_cleanup_cycling_automations_no_listeners(mock_hass, mock_entry):
    """Test cleanup_cycling_automations when listeners don't exist."""
    # Setup data but without listeners
    mock_hass.data = {
        "lambda_heat_pumps": {
            mock_entry.entry_id: {}
        }
    }
    
    # Call cleanup function
    cleanup_cycling_automations(mock_hass, mock_entry.entry_id)
    
    # Should not raise any exceptions
    assert True


@patch('custom_components.lambda_heat_pumps.automations.async_track_time_change')
def test_yesterday_update_callback(mock_track_time_change, mock_hass, mock_entry):
    """Test the yesterday update callback function."""
    from homeassistant.helpers.dispatcher import async_dispatcher_send
    
    # Mock async_track_time_change to return a mock listener
    mock_listener = Mock()
    mock_track_time_change.return_value = mock_listener
    
    # Setup automations
    setup_cycling_automations(mock_hass, mock_entry.entry_id)
    
    # Get the callback function from the first call
    yesterday_callback = mock_track_time_change.call_args_list[0][0][1]
    
    # Mock async_dispatcher_send
    with patch('custom_components.lambda_heat_pumps.automations.async_dispatcher_send') as mock_send:
        # Call the callback
        yesterday_callback(datetime.now())
        
        # Verify that the signal was sent
        mock_send.assert_called_once_with(mock_hass, SIGNAL_UPDATE_YESTERDAY, mock_entry.entry_id)


@patch('custom_components.lambda_heat_pumps.automations.async_track_time_change')
def test_2h_update_callback(mock_track_time_change, mock_hass, mock_entry):
    """Test the 2h update callback function."""
    from homeassistant.helpers.dispatcher import async_dispatcher_send
    
    # Mock async_track_time_change to return a mock listener
    mock_listener = Mock()
    mock_track_time_change.return_value = mock_listener
    
    # Setup automations
    setup_cycling_automations(mock_hass, mock_entry.entry_id)
    
    # Get the callback function from the second call
    two_hour_callback = mock_track_time_change.call_args_list[1][0][1]
    
    # Mock async_dispatcher_send
    with patch('custom_components.lambda_heat_pumps.automations.async_dispatcher_send') as mock_send:
        # Call the callback
        two_hour_callback(datetime.now())
        
        # Verify that the signal was sent
        mock_send.assert_called_once_with(mock_hass, SIGNAL_UPDATE_2H, mock_entry.entry_id)


@patch('custom_components.lambda_heat_pumps.automations.async_track_time_change')
def test_4h_update_callback(mock_track_time_change, mock_hass, mock_entry):
    """Test the 4h update callback function."""
    from homeassistant.helpers.dispatcher import async_dispatcher_send
    
    # Mock async_track_time_change to return a mock listener
    mock_listener = Mock()
    mock_track_time_change.return_value = mock_listener
    
    # Setup automations
    setup_cycling_automations(mock_hass, mock_entry.entry_id)
    
    # Get the callback function from the third call
    four_hour_callback = mock_track_time_change.call_args_list[2][0][1]
    
    # Mock async_dispatcher_send
    with patch('custom_components.lambda_heat_pumps.automations.async_dispatcher_send') as mock_send:
        # Call the callback
        four_hour_callback(datetime.now())
        
        # Verify that the signal was sent
        mock_send.assert_called_once_with(mock_hass, SIGNAL_UPDATE_4H, mock_entry.entry_id)


def test_signal_constants():
    """Test that signal constants are defined correctly."""
    assert SIGNAL_UPDATE_YESTERDAY == "lambda_heat_pumps_update_yesterday"
    assert SIGNAL_UPDATE_2H == "lambda_heat_pumps_update_2h"
    assert SIGNAL_UPDATE_4H == "lambda_heat_pumps_update_4h"


@patch('custom_components.lambda_heat_pumps.automations.async_track_time_change')
def test_multiple_entries_setup(mock_track_time_change, mock_hass):
    """Test setting up automations for multiple entries."""
    entry1 = Mock()
    entry1.entry_id = "entry1"
    entry2 = Mock()
    entry2.entry_id = "entry2"
    
    # Mock async_track_time_change to return a mock listener
    mock_listener = Mock()
    mock_track_time_change.return_value = mock_listener
    
    # Setup automations for both entries
    setup_cycling_automations(mock_hass, entry1.entry_id)
    setup_cycling_automations(mock_hass, entry2.entry_id)
    
    # Verify that both entries have their data stored
    assert "lambda_heat_pumps" in mock_hass.data
    assert entry1.entry_id in mock_hass.data["lambda_heat_pumps"]
    assert entry2.entry_id in mock_hass.data["lambda_heat_pumps"]
    
    # Verify that async_track_time_change was called 6 times (3 per entry)
    assert mock_track_time_change.call_count == 6


def test_multiple_entries_cleanup(mock_hass):
    """Test cleaning up automations for multiple entries."""
    entry1 = Mock()
    entry1.entry_id = "entry1"
    entry2 = Mock()
    entry2.entry_id = "entry2"
    
    # Setup mock data with listeners for both entries
    mock_listener1 = Mock()
    mock_listener2 = Mock()
    mock_listener3 = Mock()
    mock_listener4 = Mock()
    mock_listener5 = Mock()
    mock_listener6 = Mock()
    
    mock_hass.data = {
        "lambda_heat_pumps": {
            entry1.entry_id: {
                "yesterday_listener": mock_listener1,
                "two_hour_listener": mock_listener2,
                "four_hour_listener": mock_listener3,
            },
            entry2.entry_id: {
                "yesterday_listener": mock_listener4,
                "two_hour_listener": mock_listener5,
                "four_hour_listener": mock_listener6,
            }
        }
    }
    
    # Cleanup only entry1
    cleanup_cycling_automations(mock_hass, entry1.entry_id)
    
    # Verify that only entry1 listeners were called
    mock_listener1.assert_called_once()
    mock_listener2.assert_called_once()
    mock_listener3.assert_called_once()
    mock_listener4.assert_not_called()
    mock_listener5.assert_not_called()
    mock_listener6.assert_not_called()
    
    # Verify that entry1 data was removed but entry2 remains
    # Note: The cleanup function only removes the listeners, not the entire entry
    entry1_data = mock_hass.data["lambda_heat_pumps"][entry1.entry_id]
    entry2_data = mock_hass.data["lambda_heat_pumps"][entry2.entry_id]
    assert "yesterday_listener" not in entry1_data
    assert "two_hour_listener" not in entry1_data
    assert "four_hour_listener" not in entry1_data
    assert "yesterday_listener" in entry2_data
    assert "two_hour_listener" in entry2_data
    assert "four_hour_listener" in entry2_data
