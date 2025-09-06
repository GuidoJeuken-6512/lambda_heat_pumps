"""
Erweiterte Lambda Heat Pump Coordinator mit modularer Auto-Discovery.

Diese Klasse erweitert den bestehenden Coordinator um automatische Erkennung
aller verfügbaren Module basierend auf der CSV-Dokumentation und dem Hardware-Scan.
"""

from __future__ import annotations

import asyncio
import logging
import random
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.config_entries import ConfigEntry

from .modular_registry import lambda_registry, RegisterTemplate
from .modbus_utils import AsyncModbusTcpClient
from .const import (
    DOMAIN,
    LAMBDA_MODBUS_TIMEOUT,
    LAMBDA_MAX_RETRIES,
    LAMBDA_RETRY_DELAY,
    LAMBDA_CIRCUIT_BREAKER_ENABLED,
    LAMBDA_MAX_OFFLINE_DURATION,
    # Multi-client Anti-Synchronisation
    LAMBDA_MULTI_CLIENT_SUPPORT,
    LAMBDA_BASE_UPDATE_INTERVAL,
    LAMBDA_RANDOM_INTERVAL_RANGE,
    LAMBDA_MIN_INTERVAL,
    LAMBDA_MAX_INTERVAL,
    LAMBDA_ANTI_SYNC_ENABLED,
    LAMBDA_ANTI_SYNC_FACTOR,
    # Register-spezifische Timeouts
    LAMBDA_REGISTER_TIMEOUTS,
    LAMBDA_INDIVIDUAL_READ_REGISTERS,
    LAMBDA_LOW_PRIORITY_REGISTERS,
)
from .circuit_breaker import SmartCircuitBreaker
from .offline_manager import HACompatibleOfflineManager
from .utils import async_read_holding_registers_with_backoff
from .modbus_utils import async_read_modbus_with_robustness, check_dynamic_individual_read

_LOGGER = logging.getLogger(__name__)


class LambdaModularCoordinator(DataUpdateCoordinator):
    """Erweiterte Coordinator mit automatischer Modul-Erkennung."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        scan_file_path: str | None = None,
        modbus_timeout: int = None,
        max_retries: int = None,
        circuit_breaker_enabled: bool = None,
    ) -> None:
        """Initialize the modular coordinator."""
        # Multi-Client Anti-Synchronisation implementieren
        base_update_interval = 30  # Standard-Intervall
        if LAMBDA_ANTI_SYNC_ENABLED and LAMBDA_MULTI_CLIENT_SUPPORT:
            # Zufällige Abweichung für Anti-Synchronisation hinzufügen
            random_range = LAMBDA_RANDOM_INTERVAL_RANGE
            jitter = random.uniform(-random_range, random_range)
            adjusted_interval = max(
                LAMBDA_MIN_INTERVAL, 
                min(LAMBDA_MAX_INTERVAL, base_update_interval + jitter)
            )
            
            _LOGGER.info(
                f"Modular coordinator anti-sync: Base interval {base_update_interval}s, "
                f"adjusted to {adjusted_interval:.1f}s (jitter: {jitter:+.1f}s)"
            )
            update_interval = adjusted_interval
        else:
            update_interval = base_update_interval
        
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} Modular",
            update_interval=timedelta(seconds=update_interval),
        )

        self.config_entry = config_entry
        self.host = config_entry.data["host"]
        self.port = config_entry.data["port"]
        self.slave_id = config_entry.data["slave_id"]

        # Store expert options
        self._modbus_timeout = modbus_timeout or LAMBDA_MODBUS_TIMEOUT
        self._max_retries = max_retries or LAMBDA_MAX_RETRIES
        self._circuit_breaker_enabled = circuit_breaker_enabled if circuit_breaker_enabled is not None else LAMBDA_CIRCUIT_BREAKER_ENABLED

        # Modbus Client
        self.modbus_client: AsyncModbusTcpClient | None = None

        # Module Discovery
        self.available_modules: dict[str, bool] = {}
        self.active_registers: dict[int, RegisterTemplate] = {}
        self.module_configs: dict[str, list[dict[str, Any]]] = {}

        # System Overview
        self.system_overview: dict[str, Any] = {}

        # Robustheit-Features
        self._circuit_breaker = SmartCircuitBreaker() if self._circuit_breaker_enabled else None
        self._offline_manager = HACompatibleOfflineManager()
        
        # Dynamische Individual-Read-Verwaltung
        self._dynamic_individual_reads = set(LAMBDA_INDIVIDUAL_READ_REGISTERS)  # Kopie der statischen Liste
        self._register_timeout_counters = {}  # Zähler für Timeout-Häufigkeit pro Register
        self._register_failure_counters = {}  # Zähler für Fehler-Häufigkeit pro Register
        self._dynamic_timeout_threshold = 3  # Nach 3 Timeouts -> Individual-Read
        self._dynamic_failure_threshold = 5  # Nach 5 Fehlern -> Individual-Read
        
        _LOGGER.info(f"Modular coordinator robustness enabled - Dynamic Individual-Reads: Timeout threshold: {self._dynamic_timeout_threshold}, Failure threshold: {self._dynamic_failure_threshold}")

        # Initialize registry
        if scan_file_path:
            self._load_hardware_scan(scan_file_path)

    async def _read_modbus_with_robustness(
        self, 
        address: int, 
        count: int = 1,
        sensor_info: dict = None
    ) -> Any:
        """Read Modbus registers with robustness features using shared function."""
        return await async_read_modbus_with_robustness(
            client=self.modbus_client,
            address=address,
            count=count,
            slave_id=self.slave_id,
            circuit_breaker=self._circuit_breaker,
            sensor_info=sensor_info,
            default_timeout=self._modbus_timeout
        )

    def _load_hardware_scan(self, scan_file_path: str) -> None:
        """Load hardware scan results into the registry."""
        try:
            success = lambda_registry.load_hardware_scan(scan_file_path)
            if success:
                _LOGGER.info("Hardware scan loaded successfully")
                self._discover_modules()
            else:
                _LOGGER.warning("Failed to load hardware scan, using defaults")
        except Exception as e:
            _LOGGER.error("Error loading hardware scan: %s", e)

    def _discover_modules(self) -> None:
        """Discover available modules and setup active registers."""
        self.available_modules = lambda_registry.detect_available_modules()

        # Get all active registers
        self.active_registers = lambda_registry.get_all_available_registers(
            include_undocumented=True
        )

        # Generate sensor configs for each available module
        for module_name, is_available in self.available_modules.items():
            if is_available:
                self.module_configs[module_name] = (
                    lambda_registry.generate_sensor_config(module_name, 1)
                )

        # Generate system overview
        self.system_overview = lambda_registry.get_system_overview()

        _LOGGER.info(
            "Module discovery complete: %d modules available, %d registers active",
            sum(self.available_modules.values()),
            len(self.active_registers),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from all active registers with robustness features."""
        try:
            if not self.modbus_client:
                self.modbus_client = AsyncModbusTcpClient(
                    host=self.host, port=self.port, slave_id=self.slave_id
                )

            data = {}

            # Read all active registers
            for register_addr, register_template in self.active_registers.items():
                try:
                    # Connect if needed
                    if not self.modbus_client.is_connected():
                        await self.modbus_client.connect()

                    # Individual-Reads für problematische Register (z.B. error_state)
                    # Prüfe relative Adresse für Individual-Reads
                    relative_addr = getattr(register_template, 'relative_address', None)
                    
                    # Dynamische Individual-Read-Prüfung (absolute Adressen)
                    should_use_individual = register_addr in self._dynamic_individual_reads
                    
                    if should_use_individual:
                        # Nur einmal pro Register loggen
                        if not hasattr(self, '_individual_read_logged'):
                            self._individual_read_logged = set()
                        individual_key = f"{register_addr}_{relative_addr}"
                        if individual_key not in self._individual_read_logged:
                            _LOGGER.info(
                                f"🔧 MODULAR-INDIVIDUAL-READ: Using individual read for register {register_addr} "
                                f"(relative: {relative_addr}) - configured for individual reading"
                            )
                            self._individual_read_logged.add(individual_key)

                    # Read register with robustness features
                    sensor_info = {
                        "relative_address": relative_addr,
                        "data_type": getattr(register_template, 'data_type', 'uint16')
                    }
                    result = await self._read_modbus_with_robustness(
                        register_addr, 1, sensor_info
                    )

                    if hasattr(result, "registers") and result.registers:
                        raw_value = result.registers[0]

                        # Apply scaling
                        scaled_value = raw_value * register_template.scale

                        # Store data with metadata and HA compatibility
                        data[register_addr] = {
                            "value": scaled_value,
                            "raw_value": raw_value,
                            "name": register_template.name,
                            "unit": register_template.unit,
                            "documented": register_template.documented,
                            "timestamp": self.last_update_success_time,
                            # HA compatibility attributes
                            "device_class": getattr(register_template, 'device_class', None),
                            "state_class": getattr(register_template, 'state_class', None),
                        }

                    else:
                        _LOGGER.debug(
                            "No data received for register %d (%s)",
                            register_addr,
                            register_template.name,
                        )

                except asyncio.TimeoutError as e:
                    _LOGGER.debug(
                        "Timeout reading register %d (%s): %s",
                        register_addr,
                        register_template.name,
                        e,
                    )
                    # Zähler für Timeouts erhöhen
                    self._register_timeout_counters[register_addr] = self._register_timeout_counters.get(register_addr, 0) + 1
                    check_dynamic_individual_read(
                        self._dynamic_individual_reads,
                        self._register_timeout_counters,
                        self._register_failure_counters,
                        register_addr,
                        relative_addr,
                        "timeout",
                        self._dynamic_timeout_threshold,
                        self._dynamic_failure_threshold
                    )
                    # Keep previous value if available
                except Exception as e:
                    _LOGGER.debug(
                        "Failed to read register %d (%s): %s",
                        register_addr,
                        register_template.name,
                        e,
                    )
                    # Zähler für Fehler erhöhen
                    self._register_failure_counters[register_addr] = self._register_failure_counters.get(register_addr, 0) + 1
                    check_dynamic_individual_read(
                        self._dynamic_individual_reads,
                        self._register_timeout_counters,
                        self._register_failure_counters,
                        register_addr,
                        relative_addr,
                        "failure",
                        self._dynamic_timeout_threshold,
                        self._dynamic_failure_threshold
                    )
                    # Keep previous value if available
                    if register_addr in self.data:
                        data[register_addr] = self.data[register_addr]

            # Add system overview to data
            data["_system_overview"] = self.system_overview
            data["_available_modules"] = self.available_modules
            data["_register_count"] = len(self.active_registers)

            # Update offline manager with fresh data
            self._offline_manager.update_data(data)
            return data

        except Exception as ex:
            _LOGGER.error("Error updating modular coordinator data: %s", ex)
            
            # Try to return offline data if available
            offline_data = self._offline_manager.get_offline_data()
            if offline_data:
                _LOGGER.debug("Using last known data due to connection error: %s", ex)
                return offline_data
            
            # If no offline data available, return empty dict
            return {}

    async def async_setup(self) -> bool:
        """Set up the coordinator."""
        try:
            # Initial data fetch
            await self.async_config_entry_first_refresh()
            return True
        except Exception as e:
            _LOGGER.error("Failed to setup modular coordinator: %s", e)
            return False

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        if self.modbus_client and self.modbus_client.is_connected():
            await self.modbus_client.disconnect()

    def get_module_data(self, module_name: str) -> dict[int, Any]:
        """Get data for a specific module."""
        if module_name not in self.available_modules:
            return {}

        module_data = {}
        module_registers = lambda_registry.get_module_registers(module_name)

        for register_addr in module_registers:
            if register_addr in self.data:
                module_data[register_addr] = self.data[register_addr]

        return module_data

    def get_register_value(self, register_addr: int) -> Any | None:
        """Get scaled value for a specific register."""
        if register_addr in self.data:
            return self.data[register_addr].get("value")
        return None

    def get_register_raw_value(self, register_addr: int) -> Any | None:
        """Get raw (unscaled) value for a specific register."""
        if register_addr in self.data:
            return self.data[register_addr].get("raw_value")
        return None

    def is_module_available(self, module_name: str) -> bool:
        """Check if a module is available."""
        return self.available_modules.get(module_name, False)

    def get_available_modules(self) -> list[str]:
        """Get list of available module names."""
        return [
            module_name
            for module_name, available in self.available_modules.items()
            if available
        ]

    def get_module_sensor_configs(self, module_name: str) -> list[dict[str, Any]]:
        """Get sensor configurations for a module."""
        return self.module_configs.get(module_name, [])

    def get_system_info(self) -> dict[str, Any]:
        """Get comprehensive system information."""
        return {
            "available_modules": self.available_modules,
            "active_registers": len(self.active_registers),
            "system_overview": self.system_overview,
            "last_update": self.last_update_success_time,
            "connection_status": (
                self.modbus_client.is_connected() if self.modbus_client else False
            ),
            "circuit_breaker_status": self._circuit_breaker.get_status() if self._circuit_breaker else None,
            "offline_manager_status": self._offline_manager.get_status(),
        }

    def has_undocumented_features(self) -> bool:
        """Check if system has undocumented register features."""
        for register_template in self.active_registers.values():
            if not register_template.documented:
                return True
        return False

    def get_undocumented_registers(self) -> dict[int, RegisterTemplate]:
        """Get all undocumented registers."""
        return {
            addr: template
            for addr, template in self.active_registers.items()
            if not template.documented
        }

    async def async_write_register(self, register_addr: int, value: int) -> bool:
        """Write to a register if it's writeable."""
        if register_addr not in self.active_registers:
            _LOGGER.error("Register %d not found in active registers", register_addr)
            return False

        register_template = self.active_registers[register_addr]
        if not register_template.writeable:
            _LOGGER.error(
                "Register %d (%s) is not writeable",
                register_addr,
                register_template.name,
            )
            return False

        try:
            if not self.modbus_client:
                self.modbus_client = AsyncModbusTcpClient(
                    host=self.host, port=self.port, slave_id=self.slave_id
                )

            if not self.modbus_client.is_connected():
                await self.modbus_client.connect()

            # Convert scaled value back to raw value
            raw_value = int(value / register_template.scale)

            result = await self.modbus_client.write_single_register(
                register_addr, raw_value
            )

            if not hasattr(result, "function_code") or result.function_code > 0x80:
                _LOGGER.error("Failed to write register %d: %s", register_addr, result)
                return False

            _LOGGER.info(
                "Successfully wrote %d (raw: %d) to register %d (%s)",
                value,
                raw_value,
                register_addr,
                register_template.name,
            )

            # Request immediate data update
            await self.async_request_refresh()
            return True

        except Exception as e:
            _LOGGER.error("Error writing to register %d: %s", register_addr, e)
            return False


# Factory function for easy coordinator creation
async def create_modular_coordinator(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    scan_file_path: str | None = None,
    modbus_timeout: int = None,
    max_retries: int = None,
    circuit_breaker_enabled: bool = None,
) -> LambdaModularCoordinator:
    """Create and setup a modular coordinator with expert options."""
    coordinator = LambdaModularCoordinator(
        hass, 
        config_entry, 
        scan_file_path,
        modbus_timeout=modbus_timeout,
        max_retries=max_retries,
        circuit_breaker_enabled=circuit_breaker_enabled
    )

    if await coordinator.async_setup():
        return coordinator
    else:
        raise Exception("Failed to setup modular coordinator")
