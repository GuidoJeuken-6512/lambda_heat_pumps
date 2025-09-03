"""Offline data manager for Lambda Heat Pumps integration."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from .const import LAMBDA_MAX_OFFLINE_DURATION

_LOGGER = logging.getLogger(__name__)


class HACompatibleOfflineManager:
    """HA-compatible offline data manager.
    
    This manager preserves device_class, state_class, and last_reset
    attributes when providing offline data to maintain HA compatibility.
    """
    
    def __init__(self, max_offline_duration: int = LAMBDA_MAX_OFFLINE_DURATION):
        """Initialize the offline manager.
        
        Args:
            max_offline_duration: Maximum offline duration in seconds
        """
        self.max_offline_duration = max_offline_duration
        self.last_known_data: Dict[str, Any] = {}
        self.offline_since: Optional[float] = None
    
    def update_data(self, data: Dict[str, Any]) -> None:
        """Update last known data.
        
        Args:
            data: Dictionary with sensor data
        """
        self.last_known_data = data.copy()
        self.offline_since = None
        _LOGGER.debug("Offline manager updated with fresh data")
    
    def get_offline_data(self) -> Dict[str, Any]:
        """Get last known data when offline - HA-compatible.
        
        Returns:
            Dictionary with offline data preserving HA attributes
        """
        if not self.offline_since:
            self.offline_since = time.time()
        
        # Check if offline duration is too long
        if time.time() - self.offline_since > self.max_offline_duration:
            _LOGGER.info("Offline duration exceeded %d seconds - returning empty data", 
                         self.max_offline_duration)
            return {}  # Too long offline = unavailable
        
        # Important: preserve device_class and state_class
        offline_data = self._preserve_ha_attributes(self.last_known_data)
        
        _LOGGER.info("Returning offline data for %d sensors", len(offline_data))
        return offline_data
    
    def _preserve_ha_attributes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Preserve HA-specific attributes in offline data.
        
        Args:
            data: Original sensor data
            
        Returns:
            Data with preserved HA attributes
        """
        preserved_data = {}
        
        for sensor_id, sensor_data in data.items():
            if isinstance(sensor_data, dict):
                # Create a copy to preserve original data
                preserved_sensor_data = sensor_data.copy()
                
                # Preserve HA-specific attributes
                ha_attributes = [
                    'device_class',
                    'state_class', 
                    'last_reset',
                    'unit_of_measurement',
                    'friendly_name',
                    'icon'
                ]
                
                for attr in ha_attributes:
                    if attr in sensor_data:
                        # Ensure attribute is preserved
                        preserved_sensor_data[attr] = sensor_data[attr]
                
                # For energy sensors, preserve last_reset especially
                if 'state_class' in sensor_data and sensor_data['state_class'] == 'total_increasing':
                    if 'last_reset' in sensor_data:
                        preserved_sensor_data['last_reset'] = sensor_data['last_reset']
                        _LOGGER.debug("Preserved last_reset for energy sensor %s", sensor_id)
                
                preserved_data[sensor_id] = preserved_sensor_data
            else:
                # Non-dict data (simple values)
                preserved_data[sensor_id] = sensor_data
        
        return preserved_data
    
    def is_offline(self) -> bool:
        """Check if currently offline.
        
        Returns:
            True if offline, False otherwise
        """
        return self.offline_since is not None
    
    def get_offline_duration(self) -> Optional[float]:
        """Get current offline duration in seconds.
        
        Returns:
            Offline duration in seconds, or None if not offline
        """
        if self.offline_since:
            return time.time() - self.offline_since
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get offline manager status.
        
        Returns:
            Dictionary with status information
        """
        return {
            "is_offline": self.is_offline(),
            "offline_duration": self.get_offline_duration(),
            "max_offline_duration": self.max_offline_duration,
            "sensor_count": len(self.last_known_data),
            "offline_since": self.offline_since,
        }
    
    def clear_data(self) -> None:
        """Clear all stored data."""
        self.last_known_data = {}
        self.offline_since = None
        _LOGGER.debug("Offline manager data cleared")
