"""Circuit Breaker implementation for Lambda Heat Pumps integration."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

from .const import (
    LAMBDA_CIRCUIT_BREAKER_FAILURE_THRESHOLD,
    LAMBDA_CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class SmartCircuitBreaker:
    """Intelligent Circuit Breaker with error differentiation.
    
    This circuit breaker distinguishes between network errors and protocol errors:
    - Network errors (ConnectionError, TimeoutError): Normal circuit breaker behavior
    - Protocol errors (ModbusException): Immediate circuit opening (force_open)
    """
    
    def __init__(
        self,
        failure_threshold: int = LAMBDA_CIRCUIT_BREAKER_FAILURE_THRESHOLD,
        recovery_timeout: int = LAMBDA_CIRCUIT_BREAKER_RECOVERY_TIMEOUT
    ):
        """Initialize the circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time in seconds before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.is_open = False
        self.force_open = False  # For protocol errors
    
    def can_execute(self) -> bool:
        """Check if execution is allowed.
        
        Returns:
            True if execution is allowed, False otherwise
        """
        if not self.is_open:
            return True
        
        # Check if recovery timeout has passed
        if (self.last_failure_time and 
            time.time() - self.last_failure_time > self.recovery_timeout):
            self.is_open = False
            self.failure_count = 0
            self.force_open = False  # Reset force_open after recovery timeout
            _LOGGER.info("Circuit breaker reset - attempting connection again")
            return True
        
        return False
    
    def record_success(self) -> None:
        """Record successful execution."""
        was_open = self.is_open
        
        self.failure_count = 0
        self.is_open = False
        self.force_open = False
        
        if was_open:
            _LOGGER.info("Verbindung wieder erfolgreich aufgebaut - Circuit Breaker geschlossen")
    
    def record_failure(self, exception: Exception) -> None:
        """Record failed execution with intelligent error handling.
        
        Args:
            exception: The exception that occurred
        """
        if isinstance(exception, (ConnectionError, asyncio.TimeoutError)):
            # Network errors - immediate circuit opening for faster HA response
            self.failure_count = 1
            self.last_failure_time = time.time()
            self.is_open = True
            
            _LOGGER.warning(
                "Network error detected: %s - Circuit breaker OPENED immediately for faster HA response",
                exception
            )
                
        elif self._is_modbus_exception(exception):
            # Protocol errors - immediate circuit opening
            self.is_open = True
            self.force_open = True
            self.failure_count = 999  # Mark as critical
            self.last_failure_time = time.time()
            _LOGGER.warning(
                "Circuit breaker FORCE OPENED due to Modbus protocol error: %s",
                exception
            )
        else:
            # Other errors - normal circuit breaker behavior
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.is_open = True
                _LOGGER.warning(
                    "Circuit breaker OPENED after %d failures: %s",
                    self.failure_count, exception
                )
    
    def _is_modbus_exception(self, exception: Exception) -> bool:
        """Check if exception is a Modbus protocol error.
        
        Args:
            exception: Exception to check
            
        Returns:
            True if it's a Modbus protocol error
        """
        try:
            from pymodbus.exceptions import ModbusException
            return isinstance(exception, ModbusException)
        except ImportError:
            # Fallback: check by exception name
            return "ModbusException" in str(type(exception))
    
    def get_status(self) -> dict[str, Any]:
        """Get current circuit breaker status.
        
        Returns:
            Dictionary with status information
        """
        return {
            "is_open": self.is_open,
            "force_open": self.force_open,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "state": "open" if self.is_open else "closed",
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
        }
    
    def reset(self) -> None:
        """Manually reset the circuit breaker."""
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False
        self.force_open = False
        _LOGGER.info("Circuit breaker manually reset")
