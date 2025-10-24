"""Fixed Modbus utilities for Lambda Heat Pumps integration - HA Compatible."""

import logging
import asyncio
from typing import Any

_LOGGER = logging.getLogger(__name__)

# Import Lambda-specific constants
try:
    from .const import (
        LAMBDA_MODBUS_TIMEOUT,
        LAMBDA_MODBUS_UNIT_ID,
        LAMBDA_MAX_RETRIES,
        LAMBDA_RETRY_DELAY,
    )
except ImportError:
    # Fallback values if const import fails
    LAMBDA_MODBUS_TIMEOUT = 60
    LAMBDA_MODBUS_UNIT_ID = 1
    LAMBDA_MAX_RETRIES = 3
    LAMBDA_RETRY_DELAY = 5


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
    
    # Check if client exists and is connected
    if not client:
        raise Exception("Modbus client is None - connection lost")
    
    if not hasattr(client, 'connected') or not client.connected:
        raise Exception("Modbus client not connected")
    
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
                _LOGGER.debug(
                    "Modbus read timeout at address %d (attempt %d/%d), retrying in %ds",
                    address, attempt + 1, LAMBDA_MAX_RETRIES, LAMBDA_RETRY_DELAY
                )
                await asyncio.sleep(LAMBDA_RETRY_DELAY)
            else:
                _LOGGER.warning(
                    "Modbus read timeout at address %d after %d attempts",
                    address, LAMBDA_MAX_RETRIES
                )
        except Exception as e:
            last_exception = e
            if attempt < LAMBDA_MAX_RETRIES - 1:
                _LOGGER.debug(
                    "Modbus read error at address %d (attempt %d/%d): %s, retrying in %ds",
                    address, attempt + 1, LAMBDA_MAX_RETRIES, e, LAMBDA_RETRY_DELAY
                )
                await asyncio.sleep(LAMBDA_RETRY_DELAY)
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


# =============================================================================
# INT32 ENDIANNESS SUPPORT (Issue #22)
# =============================================================================

async def get_int32_byte_order(hass) -> str:
    """
    Lädt Endianness-Konfiguration aus lambda_wp_config.yaml.
    
    Args:
        hass: Home Assistant Instanz
    
    Returns:
        str: "big" oder "little" (Standard: "big")
    """
    try:
        from .utils import load_lambda_config
        config = await load_lambda_config(hass)
        modbus_config = config.get("modbus", {})
        
        # Hole explizite Einstellung (Standard: "big")
        byte_order = modbus_config.get("int32_byte_order", "big")
        
        # Validiere Wert
        if byte_order not in ["big", "little"]:
            _LOGGER.warning("Ungültige int32_byte_order: %s, verwende 'big'", byte_order)
            return "big"
            
        return byte_order
        
    except Exception as e:
        _LOGGER.warning("Fehler beim Laden der Endianness-Konfiguration: %s", e)
        return "big"  # Sicherer Fallback auf aktuelles Verhalten


def combine_int32_registers(registers: list, byte_order: str = "big") -> int:
    """
    Kombiniert zwei 16-Bit-Register zu einem 32-Bit-Wert.
    
    Args:
        registers: Liste mit 2 Register-Werten
        byte_order: "big" oder "little"
    
    Returns:
        int: 32-Bit-Wert
        
    Raises:
        ValueError: Wenn weniger als 2 Register vorhanden sind
    """
    if len(registers) < 2:
        raise ValueError("Mindestens 2 Register erforderlich für int32")
    
    if byte_order == "little":
        # Little-Endian: Niedrigere Bits zuerst
        return (registers[1] << 16) | registers[0]
    else:  # big-endian (Standard)
        # Big-Endian: Höhere Bits zuerst (aktuelle Implementierung)
        return (registers[0] << 16) | registers[1]
