"""Fixed Modbus utilities for Lambda Heat Pumps integration - HA Compatible."""

import logging
import asyncio
import random
from typing import Any

_LOGGER = logging.getLogger(__name__)

# Import Lambda-specific constants
from .const import (
    LAMBDA_MODBUS_TIMEOUT,
    LAMBDA_MODBUS_UNIT_ID,
    LAMBDA_MAX_RETRIES,
    LAMBDA_RETRY_DELAY,
    LAMBDA_REGISTER_TIMEOUTS,
)


def _detect_pymodbus_api(client, method_name: str) -> str:
    """Detect pymodbus API version compatibility."""
    try:
        import inspect

        method = getattr(client, method_name, None)
        if not method:
            return "none"

        sig = inspect.signature(method)
        params = list(sig.parameters.keys())

        if "slave" in params:
            return "slave"  # pymodbus >= 3.0
        elif "unit" in params:
            return "unit"  # pymodbus 2.x
        else:
            return "none"  # pymodbus < 2.0
    except Exception:
        # Fallback based on version
        try:
            import pymodbus

            version = pymodbus.__version__
            if version.startswith("3"):
                return "slave"
            elif version.startswith("2"):
                return "unit"
            else:
                return "none"
        except ImportError:
            return "none"


async def async_read_holding_registers(
    client, address: int, count: int, slave_id: int = LAMBDA_MODBUS_UNIT_ID
) -> Any:
    """Read holding registers with Lambda-specific timeout and retry logic."""
    last_exception = None
    
    for attempt in range(LAMBDA_MAX_RETRIES):
        try:
            # For pymodbus 3.11.1, use only address as positional, rest as kwargs
            try:
                # Try with slave parameter (most common in 3.x)
                return await asyncio.wait_for(
                    client.read_holding_registers(address, count=count, slave=slave_id),
                    timeout=LAMBDA_MODBUS_TIMEOUT
                )
            except (TypeError, AttributeError):
                try:
                    # Try with unit parameter
                    return await asyncio.wait_for(
                        client.read_holding_registers(address, count=count, unit=slave_id),
                        timeout=LAMBDA_MODBUS_TIMEOUT
                    )
                except (TypeError, AttributeError):
                    try:
                        # Try without slave/unit parameter
                        return await asyncio.wait_for(
                            client.read_holding_registers(address, count=count),
                            timeout=LAMBDA_MODBUS_TIMEOUT
                        )
                    except TypeError:
                        # Last resort: only address and count as positional
                        return await asyncio.wait_for(
                            client.read_holding_registers(address, count),
                            timeout=LAMBDA_MODBUS_TIMEOUT
                        )
        except asyncio.TimeoutError as e:
            last_exception = e
            if attempt < LAMBDA_MAX_RETRIES - 1:
                # Exponential backoff mit Jitter
                base_delay = LAMBDA_RETRY_DELAY * (2 ** attempt)
                max_delay = 30  # Maximum 30 Sekunden
                delay = min(base_delay, max_delay)
                
                # Jitter hinzufügen (±20% Zufallsschwankung)
                jitter = random.uniform(-0.2, 0.2) * delay
                final_delay = max(1, delay + jitter)  # Minimum 1 Sekunde
                
                _LOGGER.debug(
                    "Modbus read timeout at address %d (attempt %d/%d): %s, retrying in %.1fs",
                    address, attempt + 1, LAMBDA_MAX_RETRIES, e, final_delay
                )
                await asyncio.sleep(final_delay)
            else:
                _LOGGER.warning(
                    "Modbus read timeout at address %d after %d attempts",
                    address, LAMBDA_MAX_RETRIES
                )
        except Exception as e:
            last_exception = e
            if attempt < LAMBDA_MAX_RETRIES - 1:
                # Exponential backoff mit Jitter
                base_delay = LAMBDA_RETRY_DELAY * (2 ** attempt)
                max_delay = 30  # Maximum 30 Sekunden
                delay = min(base_delay, max_delay)
                
                # Jitter hinzufügen (±20% Zufallsschwankung)
                jitter = random.uniform(-0.2, 0.2) * delay
                final_delay = max(1, delay + jitter)  # Minimum 1 Sekunde
                
                _LOGGER.debug(
                    "Modbus read error at address %d (attempt %d/%d): %s, retrying in %.1fs",
                    address, attempt + 1, LAMBDA_MAX_RETRIES, e, final_delay
                )
                await asyncio.sleep(final_delay)
            else:
                break
    
    # If we get here, all retries failed
    if last_exception:
        # Don't log as error if Home Assistant is stopping
        if "Home Assistant is stopping" in str(last_exception) or "CancelledError" in str(last_exception):
            _LOGGER.debug("Modbus read cancelled at address %d (HA stopping): %s", address, last_exception)
        else:
            _LOGGER.exception("Modbus read error at address %d: %s", address, last_exception)
        raise last_exception


async def async_read_modbus_with_robustness(
    client: Any,
    address: int,
    count: int,
    slave_id: int,
    circuit_breaker: Any = None,
    sensor_info: dict = None,
    default_timeout: int = LAMBDA_MODBUS_TIMEOUT
) -> Any:
    """Read Modbus registers with robustness features.
    
    This is a shared function used by both Standard and Modular Coordinators
    to provide consistent robustness features including:
    - Circuit breaker integration
    - Sensor-specific timeouts
    - Exponential backoff with jitter
    - Error handling and logging
    
    Args:
        client: Modbus client instance
        address: Starting register address
        count: Number of registers to read
        slave_id: Modbus slave ID
        circuit_breaker: Circuit breaker instance (optional)
        sensor_info: Sensor information dict with relative_address (optional)
        default_timeout: Default timeout in seconds
        
    Returns:
        Modbus response object
        
    Raises:
        Exception: If all retry attempts failed or circuit breaker is open
    """
    # Check circuit breaker
    if circuit_breaker and not circuit_breaker.can_execute():
        _LOGGER.debug("Circuit breaker is OPEN - skipping Modbus read at address %d", address)
        raise Exception("Circuit breaker is OPEN")
    
    try:
        # Sensor-spezifische Timeouts basierend auf absoluter Adresse
        timeout = default_timeout
        if address in LAMBDA_REGISTER_TIMEOUTS:
            timeout = LAMBDA_REGISTER_TIMEOUTS[address]
            # Nur einmal pro Register loggen, wenn Timeout tatsächlich geändert wurde
            if not hasattr(async_read_modbus_with_robustness, '_timeout_logged'):
                async_read_modbus_with_robustness._timeout_logged = set()
            timeout_key = f"{address}_{timeout}"
            if timeout != default_timeout and timeout_key not in async_read_modbus_with_robustness._timeout_logged:
                _LOGGER.info(
                    f"⏱️ TIMEOUT-ADJUST: Using sensor-specific timeout {timeout}s for register {address} - reduced from default {default_timeout}s"
                )
                async_read_modbus_with_robustness._timeout_logged.add(timeout_key)
        
        # Use exponential backoff for retries
        from .utils import async_read_holding_registers_with_backoff
        result = await async_read_holding_registers_with_backoff(
            client, address, count, slave_id, timeout
        )
        
        # Record success in circuit breaker
        if circuit_breaker:
            circuit_breaker.record_success()
        
        return result
        
    except Exception as e:
        # Record failure in circuit breaker
        if circuit_breaker:
            circuit_breaker.record_failure(e)
        raise


async def async_read_input_registers(
    client, address: int, count: int, slave_id: int = LAMBDA_MODBUS_UNIT_ID
) -> Any:
    """Read input registers with full API compatibility."""
    try:
        # For pymodbus 3.11.1, use only address as positional, rest as kwargs
        try:
            # Try with slave parameter (most common in 3.x)
            return await client.read_input_registers(
                address, count=count, slave=slave_id
            )
        except (TypeError, AttributeError):
            try:
                # Try with unit parameter
                return await client.read_input_registers(
                    address, count=count, unit=slave_id
                )
            except (TypeError, AttributeError):
                try:
                    # Try without slave/unit parameter
                    return await client.read_input_registers(address, count=count)
                except TypeError:
                    # Last resort: only address and count as positional
                    return await client.read_input_registers(address, count)

    except Exception as e:
        # Don't log as error if Home Assistant is stopping
        if "Home Assistant is stopping" in str(e) or "CancelledError" in str(e):
            _LOGGER.debug("Modbus read cancelled at address %d (HA stopping): %s", address, e)
        else:
            _LOGGER.exception("Modbus read error at address %d: %s", address, e)
        raise


async def async_write_register(
    client, address: int, value: int, slave_id: int = LAMBDA_MODBUS_UNIT_ID
) -> Any:
    """Write single register with full API compatibility."""
    try:
        # For pymodbus 3.11.1, use address as positional, rest as kwargs
        try:
            # Try with slave parameter (most common in 3.x)
            return await client.write_register(address, value, slave=slave_id)
        except (TypeError, AttributeError):
            try:
                # Try with unit parameter
                return await client.write_register(address, value, unit=slave_id)
            except (TypeError, AttributeError):
                # Try without slave/unit parameter
                return await client.write_register(address, value)

    except Exception as e:
        # Don't log as error if Home Assistant is stopping
        if "Home Assistant is stopping" in str(e) or "CancelledError" in str(e):
            _LOGGER.debug("Modbus write cancelled at address %d (HA stopping): %s", address, e)
        else:
            _LOGGER.exception("Modbus write error at address %d: %s", address, e)
        raise


async def async_write_registers(
    client, address: int, values: list, slave_id: int = LAMBDA_MODBUS_UNIT_ID
) -> Any:
    """Write multiple registers with full API compatibility."""
    try:
        api_type = _detect_pymodbus_api(client, "write_registers")

        if api_type == "slave":
            return await client.write_registers(address, values, slave=slave_id)
        elif api_type == "unit":
            return await client.write_registers(address, values, unit=slave_id)
        else:
            return await client.write_registers(address, values)

    except Exception as e:
        # Don't log as error if Home Assistant is stopping
        if "Home Assistant is stopping" in str(e) or "CancelledError" in str(e):
            _LOGGER.debug("Modbus write cancelled at address %d (HA stopping): %s", address, e)
        else:
            _LOGGER.error("Modbus write error at address %d: %s", address, e)
        raise


# Synchronous versions for backward compatibility
def read_holding_registers(client, address: int, count: int, slave_id: int = 1) -> Any:
    """Synchronous read holding registers with compatibility."""
    try:
        api_type = _detect_pymodbus_api(client, "read_holding_registers")

        if api_type == "slave":
            try:
                return client.read_holding_registers(
                    address, count=count, slave=slave_id
                )
            except TypeError:
                return client.read_holding_registers(address, count, slave=slave_id)
        elif api_type == "unit":
            return client.read_holding_registers(address, count, unit=slave_id)
        else:
            return client.read_holding_registers(address, count)

    except Exception as e:
        _LOGGER.error("Modbus read error at address %d: %s", address, e)
        raise


def write_register(client, address: int, value: int, slave_id: int = 1) -> Any:
    """Synchronous write register with compatibility."""
    try:
        api_type = _detect_pymodbus_api(client, "write_register")

        if api_type == "slave":
            return client.write_register(address, value, slave=slave_id)
        elif api_type == "unit":
            return client.write_register(address, value, unit=slave_id)
        else:
            return client.write_register(address, value)

    except Exception as e:
        _LOGGER.error("Modbus write error at address %d: %s", address, e)
        raise


def write_registers(client, address: int, values: list, slave_id: int = 1) -> Any:
    """Synchronous write registers with compatibility."""
    try:
        api_type = _detect_pymodbus_api(client, "write_registers")

        if api_type == "slave":
            return client.write_registers(address, values, slave=slave_id)
        elif api_type == "unit":
            return client.write_registers(address, values, unit=slave_id)
        else:
            return client.write_registers(address, values)

    except Exception as e:
        _LOGGER.error("Modbus write error at address %d: %s", address, e)
        raise


def read_input_registers(client, address: int, count: int, slave_id: int = 1) -> Any:
    """Synchronous read input registers with compatibility."""
    try:
        api_type = _detect_pymodbus_api(client, "read_input_registers")

        if api_type == "slave":
            try:
                return client.read_input_registers(address, count=count, slave=slave_id)
            except TypeError:
                return client.read_input_registers(address, count, slave=slave_id)
        elif api_type == "unit":
            return client.read_input_registers(address, count, unit=slave_id)
        else:
            return client.read_input_registers(address, count)

    except Exception as e:
        _LOGGER.error("Modbus read error at address %d: %s", address, e)
        raise


def check_dynamic_individual_read(
    dynamic_individual_reads: set,
    register_timeout_counters: dict,
    register_failure_counters: dict,
    address: int,
    relative_addr: int,
    error_type: str,
    dynamic_timeout_threshold: int = 3,
    dynamic_failure_threshold: int = 5
) -> None:
    """Prüft ob ein Register dynamisch zu Individual-Reads hinzugefügt werden soll.
    
    Diese Funktion wird von beiden Coordinatoren (Standard und Modular) verwendet
    um Register zur Laufzeit zu Individual-Reads hinzuzufügen, wenn sie wiederholt
    Timeouts oder Fehler verursachen.
    
    Args:
        dynamic_individual_reads: Set der aktuellen Individual-Read-Register
        register_timeout_counters: Dict mit Timeout-Zählern pro Register
        register_failure_counters: Dict mit Fehler-Zählern pro Register
        address: Absolute Register-Adresse
        relative_addr: Relative Register-Adresse
        error_type: Art des Fehlers ("timeout" oder "failure")
        dynamic_timeout_threshold: Schwelle für Timeout-basierte Individual-Reads
        dynamic_failure_threshold: Schwelle für Fehler-basierte Individual-Reads
    """
    if relative_addr is None:
        return
        
    # Prüfe ob bereits in Individual-Reads (nur absolute Adressen)
    if address in dynamic_individual_reads:
        return
        
    # Prüfe Timeout-Schwelle
    if error_type == "timeout":
        timeout_count = register_timeout_counters.get(address, 0)
        if timeout_count >= dynamic_timeout_threshold:
            dynamic_individual_reads.add(address)  # Absolute Adresse verwenden
            _LOGGER.info(f"🔄 DYNAMIC-INDIVIDUAL: Register {address} added to Individual-Reads after {timeout_count} timeouts")
            return
            
    # Prüfe Fehler-Schwelle
    if error_type == "failure":
        failure_count = register_failure_counters.get(address, 0)
        if failure_count >= dynamic_failure_threshold:
            dynamic_individual_reads.add(address)  # Absolute Adresse verwenden
            _LOGGER.info(f"🔄 DYNAMIC-INDIVIDUAL: Register {address} added to Individual-Reads after {failure_count} failures")
