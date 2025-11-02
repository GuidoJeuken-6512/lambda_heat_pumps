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
        _LOGGER.info("❌ MODBUS READ: Connection not healthy for address %d", address)
        raise Exception("Modbus client is None - connection lost")
    
    if not hasattr(client, 'connected') or not client.connected:
        _LOGGER.info("❌ MODBUS READ: Connection not healthy for address %d", address)
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
            _LOGGER.info(
                "❌ MODBUS READ FAILED: address=%d, retries=%d, error=%s, caller=async_read_holding_registers",
                address, LAMBDA_MAX_RETRIES, last_exception
            )
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
            _LOGGER.info(
                "❌ MODBUS WRITE FAILED: address=%d, value=%d, error=%s, caller=async_write_register",
                address, value, e
            )
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
            _LOGGER.info(
                "❌ MODBUS WRITE FAILED: address=%d, values=%s, error=%s, caller=async_write_registers",
                address, values, e
            )
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
# INT32 REGISTER ORDER SUPPORT (Issue #22)
# =============================================================================

async def get_int32_register_order(hass) -> str:
    """
    Lädt Register-Reihenfolge-Konfiguration aus lambda_wp_config.yaml.
    
    Es handelt sich um die Reihenfolge der 16-Bit-Register bei 32-Bit-Werten
    (Register/Word Order), nicht um Byte-Endianness innerhalb eines Registers.
    
    Args:
        hass: Home Assistant Instanz
    
    Returns:
        str: "high_first" oder "low_first" (Standard: "high_first")
        
    Note:
        "high_first" = Höherwertiges Register zuerst (Register[0] << 16 | Register[1])
        "low_first" = Niedrigwertiges Register zuerst (Register[1] << 16 | Register[0])
        
        Rückwärtskompatibilität: "big" wird zu "high_first", "little" zu "low_first" konvertiert
    """
    try:
        from .utils import load_lambda_config
        config = await load_lambda_config(hass)
        modbus_config = config.get("modbus", {})
        
        # Prüfe zuerst neue Config, dann alte (für Rückwärtskompatibilität)
        register_order = modbus_config.get("int32_register_order")
        if register_order is None:
            # Rückwärtskompatibilität: Alte Config migrieren
            old_byte_order = modbus_config.get("int32_byte_order")
            if old_byte_order is not None:
                _LOGGER.info(
                    "Migration: int32_byte_order gefunden, verwende Wert für int32_register_order. "
                    "Bitte migrieren Sie Ihre Config zu modbus.int32_register_order"
                )
                register_order = old_byte_order
            else:
                register_order = "high_first"  # Standard
        
        # Rückwärtskompatibilität: Konvertiere alte Werte
        if register_order == "big":
            register_order = "high_first"
            _LOGGER.info(
                "Veralteter Wert 'big' verwendet. Bitte aktualisieren Sie Ihre Config auf 'high_first'"
            )
        elif register_order == "little":
            register_order = "low_first"
            _LOGGER.info(
                "Veralteter Wert 'little' verwendet. Bitte aktualisieren Sie Ihre Config auf 'low_first'"
            )
        
        # Validiere Wert
        if register_order not in ["high_first", "low_first"]:
            _LOGGER.warning("Ungültige int32_register_order: %s, verwende 'high_first'", register_order)
            return "high_first"
            
        return register_order
        
    except Exception as e:
        _LOGGER.warning("Fehler beim Laden der Register-Reihenfolge-Konfiguration: %s", e)
        return "high_first"  # Sicherer Fallback auf aktuelles Verhalten


def combine_int32_registers(registers: list, register_order: str = "high_first") -> int:
    """
    Kombiniert zwei 16-Bit-Register zu einem 32-Bit-Wert.
    
    Args:
        registers: Liste mit 2 Register-Werten
        register_order: "high_first" oder "low_first" - Reihenfolge der Register
                       "high_first" = Höherwertiges Register zuerst (Register[0] enthält MSW)
                       "low_first" = Niedrigwertiges Register zuerst (Register[0] enthält LSW)
    
    Returns:
        int: 32-Bit-Wert
        
    Raises:
        ValueError: Wenn weniger als 2 Register vorhanden sind
        
    Note:
        Dies betrifft die Register-Reihenfolge (Word Order), nicht die Byte-Endianness
        innerhalb eines Registers. Modbus verwendet standardmäßig Big-Endian für Bytes
        innerhalb eines Registers, aber die Reihenfolge mehrerer Register ist geräteabhängig.
        
        Rückwärtskompatibilität: "big" wird zu "high_first", "little" zu "low_first" behandelt
    """
    if len(registers) < 2:
        raise ValueError("Mindestens 2 Register erforderlich für int32")
    
    # Rückwärtskompatibilität für alte Werte
    if register_order == "big":
        register_order = "high_first"
    elif register_order == "little":
        register_order = "low_first"
    
    if register_order == "low_first":
        # Low-order register first: Niedrigwertiges Register zuerst
        # Register[0] = LSW, Register[1] = MSW
        return (registers[1] << 16) | registers[0]
    else:  # high_first (Standard)
        # High-order register first: Höherwertiges Register zuerst
        # Register[0] = MSW, Register[1] = LSW
        return (registers[0] << 16) | registers[1]


async def wait_for_stable_connection(coordinator) -> None:
    """Wait for stable Modbus connection before starting operations.
    
    Args:
        coordinator: LambdaDataUpdateCoordinator instance
        
    This function ensures the Modbus connection is stable before
    starting operations, preventing "Cancel send" errors.
    """
    max_attempts = 10
    attempt = 0
    
    _LOGGER.info("🔍 CONNECTION: Starting wait_for_stable_connection (coordinator_id=%s)", id(coordinator))
    
    while attempt < max_attempts:
        try:
            # Teste Verbindung mit eigenständiger Health-Check
            if await _test_connection_health(coordinator):
                _LOGGER.info("✅ CONNECTION: Connection stable after %d attempts", attempt + 1)
                return
            
            attempt += 1
            _LOGGER.info("⏳ CONNECTION: Connection not stable yet, attempt %d/%d", attempt, max_attempts)
            await asyncio.sleep(1)  # 1 Sekunde warten
            
        except Exception as e:
            attempt += 1
            _LOGGER.info("⏳ CONNECTION: Connection test failed (attempt %d/%d): %s", attempt, max_attempts, e)
            await asyncio.sleep(1)
    
    _LOGGER.warning("⚠️ CONNECTION: Connection not stable after %d attempts, proceeding anyway", max_attempts)


async def _test_connection_health(coordinator) -> bool:
    """Test if the Modbus connection is healthy with robust API compatibility."""
    if not coordinator.client:
        _LOGGER.info("🔍 CONNECTION: No client available (coordinator_id=%s)", id(coordinator))
        return False
    
    try:
        _LOGGER.info("🔍 CONNECTION: Testing connection health... (coordinator_id=%s)", id(coordinator))
        # Try a simple read to test connection health using robust API compatibility
        # Use register 0 (General Error Number) as a health check
        result = await asyncio.wait_for(
            _health_check_read(coordinator.client, coordinator.slave_id),
            timeout=2  # 2 Sekunden Timeout für schnellen Health Check
        )
        if result is not None:
            _LOGGER.info("✅ CONNECTION: Connection healthy (coordinator_id=%s)", id(coordinator))
            return True
        else:
            _LOGGER.info("❌ CONNECTION: Connection unhealthy - result is None (coordinator_id=%s)", id(coordinator))
            return False
    except Exception as e:
        _LOGGER.info("❌ CONNECTION: Connection unhealthy - error=%s (coordinator_id=%s)", e, id(coordinator))
        return False


async def _health_check_read(client, slave_id):
    """Robust health check read with API compatibility fallbacks."""
    try:
        # Try with slave parameter (most common in 3.x)
        return await client.read_holding_registers(0, count=1, slave=slave_id)
    except (TypeError, AttributeError):
        try:
            # Try with unit parameter
            return await client.read_holding_registers(0, count=1, unit=slave_id)
        except (TypeError, AttributeError):
            try:
                # Try without slave/unit parameter
                return await client.read_holding_registers(0, count=1)
            except TypeError:
                # Last resort: only address and count as positional
                return await client.read_holding_registers(0, 1)
