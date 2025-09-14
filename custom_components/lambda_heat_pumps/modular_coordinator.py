"""
Erweiterte Lambda Heat Pump Coordinator mit modularer Auto-Discovery.

Diese Klasse erweitert den bestehenden Coordinator um automatische Erkennung
aller verfügbaren Module basierend auf der CSV-Dokumentation und dem Hardware-Scan.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.config_entries import ConfigEntry

from .modular_registry import lambda_registry, RegisterTemplate
from .modbus_utils import AsyncModbusTcpClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class LambdaModularCoordinator(DataUpdateCoordinator):
    """Erweiterte Coordinator mit automatischer Modul-Erkennung."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        scan_file_path: str | None = None,
    ) -> None:
        """Initialize the modular coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} Modular",
            update_interval=timedelta(seconds=30),
        )

        self.config_entry = config_entry
        self.host = config_entry.data["host"]
        self.port = config_entry.data["port"]
        self.slave_id = config_entry.data["slave_id"]

        # Modbus Client
        self.modbus_client: AsyncModbusTcpClient | None = None

        # Module Discovery
        self.available_modules: dict[str, bool] = {}
        self.active_registers: dict[int, RegisterTemplate] = {}
        self.module_configs: dict[str, list[dict[str, Any]]] = {}

        # System Overview
        self.system_overview: dict[str, Any] = {}

        # Initialize registry
        if scan_file_path:
            self._load_hardware_scan(scan_file_path)

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
        """Fetch data from all active registers."""
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

                # Read register
                result = await self.modbus_client.read_holding_registers(
                    register_addr, 1
                )

                if hasattr(result, "registers") and result.registers:
                    raw_value = result.registers[0]

                    # Apply scaling
                    scaled_value = raw_value * register_template.scale

                    # Store data with metadata
                    data[register_addr] = {
                        "value": scaled_value,
                        "raw_value": raw_value,
                        "name": register_template.name,
                        "unit": register_template.unit,
                        "documented": register_template.documented,
                        "timestamp": self.last_update_success_time,
                    }

                else:
                    _LOGGER.debug(
                        "No data received for register %d (%s)",
                        register_addr,
                        register_template.name,
                    )

            except Exception as e:
                _LOGGER.debug(
                    "Failed to read register %d (%s): %s",
                    register_addr,
                    register_template.name,
                    e,
                )
                # Keep previous value if available
                if register_addr in self.data:
                    data[register_addr] = self.data[register_addr]

        # Add system overview to data
        data["_system_overview"] = self.system_overview
        data["_available_modules"] = self.available_modules
        data["_register_count"] = len(self.active_registers)

        return data

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
) -> LambdaModularCoordinator:
    """Create and setup a modular coordinator."""
    coordinator = LambdaModularCoordinator(hass, config_entry, scan_file_path)

    if await coordinator.async_setup():
        return coordinator
    else:
        raise Exception("Failed to setup modular coordinator")
