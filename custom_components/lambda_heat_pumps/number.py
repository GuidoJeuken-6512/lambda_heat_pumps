from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode, RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    HC_HEATING_CURVE_NUMBER_CONFIG,
    HC_ROOM_THERMOSTAT_NUMBER_CONFIG,
    HC_FLOW_LINE_OFFSET_NUMBER_CONFIG,
    HC_ECO_TEMP_REDUCTION_NUMBER_CONFIG,
)
from .utils import (
    build_device_info,
    build_subdevice_info,
    generate_sensor_names,
    get_entity_icon,
    load_sensor_translations,
    normalize_name_prefix,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lambda Heat Pump number entities."""
    coordinator_data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator_data is None:
        _LOGGER.error("No coordinator data found for entry %s", entry.entry_id)
        return

    num_hc = entry.data.get("num_hc", 1)
    use_legacy_modbus_names = entry.data.get("use_legacy_modbus_names", True)
    name_prefix = normalize_name_prefix(entry.data.get("name", ""))
    room_thermostat_enabled = entry.options.get("room_thermostat_control", False)
    sensor_translations = await load_sensor_translations(hass)

    coordinator = coordinator_data.get("coordinator")
    if not coordinator:
        _LOGGER.error("Coordinator not found for entry %s", entry.entry_id)
        return

    number_entities: list[LambdaHeatingCurveNumber | LambdaFlowLineOffsetNumber | LambdaEcoTempReductionNumber] = []

    for hc_index in range(1, num_hc + 1):
        device_prefix = f"hc{hc_index}"
        for sensor_id, spec in HC_HEATING_CURVE_NUMBER_CONFIG.items():
            names = generate_sensor_names(
                device_prefix,
                spec["name"],
                sensor_id,
                name_prefix,
                use_legacy_modbus_names,
                translations=sensor_translations,
            )

            base_entity_id = names["entity_id"]
            if base_entity_id.startswith("sensor."):
                entity_id = base_entity_id.replace("sensor.", "number.", 1)
            elif "." in base_entity_id:
                entity_id = f"number.{base_entity_id.split('.', 1)[1]}"
            else:
                entity_id = f"number.{base_entity_id}"
            unique_id = f"{names['unique_id']}_number"

            number_entities.append(
                LambdaHeatingCurveNumber(
                    entry=entry,
                    hc_index=hc_index,
                    sensor_id=sensor_id,
                    name=names["name"],
                    entity_id=entity_id,
                    unique_id=unique_id,
                    spec=spec,
                )
            )

        if room_thermostat_enabled:
            for sensor_id, spec in HC_ROOM_THERMOSTAT_NUMBER_CONFIG.items():
                names = generate_sensor_names(
                    device_prefix,
                    spec["name"],
                    sensor_id,
                    name_prefix,
                    use_legacy_modbus_names,
                    translations=sensor_translations,
                )

                base_entity_id = names["entity_id"]
                if base_entity_id.startswith("sensor."):
                    entity_id = base_entity_id.replace("sensor.", "number.", 1)
                elif "." in base_entity_id:
                    entity_id = f"number.{base_entity_id.split('.', 1)[1]}"
                else:
                    entity_id = f"number.{base_entity_id}"
                unique_id = f"{names['unique_id']}_number"

                number_entities.append(
                    LambdaHeatingCurveNumber(
                        entry=entry,
                        hc_index=hc_index,
                        sensor_id=sensor_id,
                        name=names["name"],
                        entity_id=entity_id,
                        unique_id=unique_id,
                        spec=spec,
                    )
                )

        # Flow-Line-Offset Number Entities für jeden HC
        for sensor_id, spec in HC_FLOW_LINE_OFFSET_NUMBER_CONFIG.items():
            names = generate_sensor_names(
                device_prefix,
                spec["name"],
                sensor_id,
                name_prefix,
                use_legacy_modbus_names,
                translations=sensor_translations,
            )

            base_entity_id = names["entity_id"]
            if base_entity_id.startswith("sensor."):
                entity_id = base_entity_id.replace("sensor.", "number.", 1)
            elif "." in base_entity_id:
                entity_id = f"number.{base_entity_id.split('.', 1)[1]}"
            else:
                entity_id = f"number.{base_entity_id}"
            unique_id = f"{names['unique_id']}_number"

            number_entities.append(
                LambdaFlowLineOffsetNumber(
                    coordinator=coordinator,
                    entry=entry,
                    hc_index=hc_index,
                    name=names["name"],
                    entity_id=entity_id,
                    unique_id=unique_id,
                    spec=spec,
                )
            )

        # Eco Temperature Reduction Number Entities für jeden HC
        for sensor_id, spec in HC_ECO_TEMP_REDUCTION_NUMBER_CONFIG.items():
            names = generate_sensor_names(
                device_prefix,
                spec["name"],
                sensor_id,
                name_prefix,
                use_legacy_modbus_names,
                translations=sensor_translations,
            )

            base_entity_id = names["entity_id"]
            if base_entity_id.startswith("sensor."):
                entity_id = base_entity_id.replace("sensor.", "number.", 1)
            elif "." in base_entity_id:
                entity_id = f"number.{base_entity_id.split('.', 1)[1]}"
            else:
                entity_id = f"number.{base_entity_id}"
            unique_id = f"{names['unique_id']}_number"

            number_entities.append(
                LambdaEcoTempReductionNumber(
                    entry=entry,
                    hc_index=hc_index,
                    name=names["name"],
                    entity_id=entity_id,
                    unique_id=unique_id,
                    spec=spec,
                )
            )

    if not number_entities:
        _LOGGER.debug("No heating curve numbers created for entry %s", entry.entry_id)
        return

    _LOGGER.info(
        "Created %d number entities (heating curve, room thermostat, flow line offset, eco temp reduction) for %d heating circuits",
        len(number_entities),
        num_hc,
    )
    async_add_entities(number_entities)


class LambdaHeatingCurveNumber(RestoreNumber, NumberEntity):
    """Number entity representing a heating curve support point."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        hc_index: int,
        sensor_id: str,
        name: str,
        entity_id: str,
        unique_id: str,
        spec: dict[str, Any],
    ) -> None:
        self._entry = entry
        self._hc_index = hc_index
        self._sensor_id = sensor_id
        self.entity_id = entity_id
        self._attr_name = name
        self._attr_unique_id = unique_id

        self._attr_native_unit_of_measurement = spec.get("unit")
        self._attr_native_min_value = spec.get("min_value")
        self._attr_native_max_value = spec.get("max_value")
        self._attr_native_step = spec.get("step")
        self._attr_mode = NumberMode.BOX
        
        # Setze Icon aus der Config (zentrale Steuerung)
        self._attr_icon = get_entity_icon(spec, default_icon="mdi:chart-bell-curve-cumulative")
        
        self._outside_temp_point = spec.get("outside_temp_point")

        default_value = spec.get("default", 0.0)
        self._attr_native_value = float(default_value)
        precision = spec.get("precision")
        if precision is not None:
            self._attr_suggested_display_precision = precision

    async def async_added_to_hass(self) -> None:
        """Restore the previous state when added to Home Assistant."""
        await super().async_added_to_hass()
        last_number_data = await self.async_get_last_number_data()
        if last_number_data and last_number_data.native_value is not None:
            self._attr_native_value = float(last_number_data.native_value)
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Persist the newly set value."""
        self._attr_native_value = float(value)
        self.async_write_ha_state()

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information for this number entity."""
        if self._hc_index:
            return build_subdevice_info(self._entry, "hc", self._hc_index)
        return build_device_info(self._entry)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes for diagnostics."""
        return {
            "sensor_id": self._sensor_id,
            "hc_index": self._hc_index,
            "outside_temp_point": self._outside_temp_point,
        }


class LambdaFlowLineOffsetNumber(CoordinatorEntity, RestoreNumber, NumberEntity):
    """Number entity für Flow-Line-Offset mit bidirektionaler Modbus-Synchronisation."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        hc_index: int,
        name: str,
        entity_id: str,
        unique_id: str,
        spec: dict[str, Any],
    ) -> None:
        # CoordinatorEntity initialisieren (MUSS zuerst sein!)
        CoordinatorEntity.__init__(self, coordinator)
        # RestoreNumber initialisieren
        RestoreNumber.__init__(self)

        self._entry = entry
        self._hc_index = hc_index
        self.entity_id = entity_id
        self._attr_name = name
        self._attr_unique_id = unique_id

        # NumberEntity Properties
        self._attr_native_unit_of_measurement = spec.get("unit")
        self._attr_native_min_value = spec.get("min_value")
        self._attr_native_max_value = spec.get("max_value")
        self._attr_native_step = spec.get("step")
        self._attr_mode = NumberMode.BOX

        # Modbus-spezifische Properties
        self._relative_address = spec.get("relative_address", 50)
        self._scale = spec.get("scale", 0.1)

        # Icon
        self._attr_icon = get_entity_icon(spec, default_icon="mdi:thermometer-adjust")

        # Precision
        precision = spec.get("precision")
        if precision is not None:
            self._attr_suggested_display_precision = precision

        # Initialer Wert (wird später aus Coordinator oder RestoreState geladen)
        default_value = spec.get("default", 0.0)
        self._attr_native_value = float(default_value)

        # Key für Coordinator-Cache
        self._coordinator_key = f"hc{self._hc_index}_set_flow_line_offset_temperature"

    @property
    def native_value(self) -> float | None:
        """Lese Wert aus Coordinator-Cache (Modbus) oder RestoreState."""
        # 1. Versuche aus Coordinator zu lesen (aktueller Modbus-Wert)
        if self.coordinator.data:
            value = self.coordinator.data.get(self._coordinator_key)
            if value is not None:
                try:
                    # Coordinator speichert Werte bereits mit Scale konvertiert (in °C)
                    # Siehe coordinator.py Zeile 980-981: value = value * sensor_info["scale"]
                    converted_value = float(value)
                    # Aktualisiere lokalen State für Konsistenz
                    self._attr_native_value = converted_value
                    return converted_value
                except (TypeError, ValueError):
                    _LOGGER.warning(
                        "Invalid flow line offset value in coordinator: %s",
                        value,
                    )

        # 2. Fallback: Lokaler State (RestoreState oder Default)
        return self._attr_native_value

    async def async_added_to_hass(self) -> None:
        """Restore the previous state when added to Home Assistant."""
        await super().async_added_to_hass()

        # 1. Versuche RestoreState zu laden
        last_number_data = await self.async_get_last_number_data()
        if last_number_data and last_number_data.native_value is not None:
            self._attr_native_value = float(last_number_data.native_value)

        # 2. Versuche aus Coordinator zu lesen (hat Priorität)
        if self.coordinator.data:
            value = self.coordinator.data.get(self._coordinator_key)
            if value is not None:
                try:
                    # Coordinator speichert Werte bereits mit Scale konvertiert (in °C)
                    self._attr_native_value = float(value)
                except (TypeError, ValueError):
                    pass

        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Schreibe Wert auf Modbus und aktualisiere lokalen State."""
        _LOGGER.info(
            "🔄 FLOW_LINE_OFFSET: async_set_native_value called for %s with value %.1f°C",
            self.entity_id,
            value,
        )

        # 1. Validierung
        if value < self._attr_native_min_value or value > self._attr_native_max_value:
            _LOGGER.warning(
                "Value %s out of range [%s, %s] for %s",
                value,
                self._attr_native_min_value,
                self._attr_native_max_value,
                self.entity_id,
            )
            return

        # 2. Prüfe ob Coordinator-Client verfügbar ist
        if not self.coordinator.client:
            _LOGGER.error(
                "❌ FLOW_LINE_OFFSET: Modbus client not available for %s",
                self.entity_id,
            )
            return

        # 3. Konvertiere zu Modbus-Format
        raw_value = int(round(value / self._scale))  # z.B. 2.5°C -> 25
        
        # Konvertiere signed int16 zu unsigned für Modbus (Two's Complement)
        # Das Register ist als int16 definiert, daher müssen
        # negative Werte als Two's Complement kodiert werden
        # Modbus-Register sind physisch unsigned (0-65535), aber das Gerät interpretiert
        # sie als signed int16 (-32768 bis 32767)
        from .utils import clamp_to_int16
        
        # Clamp auf int16-Bereich und konvertiere zu unsigned mit Two's Complement
        raw_value = clamp_to_int16(raw_value, context="Flow Line Offset") & 0xFFFF
        
        _LOGGER.debug(
            "🔄 FLOW_LINE_OFFSET: Converted %.1f°C to raw value %d (scale=%.1f, signed->unsigned)",
            value,
            raw_value,
            self._scale,
        )

        # 4. Berechne Register-Adresse
        # WICHTIG: base_addresses verwendet numerische Keys (1, 2, 3), nicht "hc1", "hc2"
        # Siehe utils.py generate_base_addresses() und climate.py hc_addresses[idx]
        if not hasattr(self.coordinator, "base_addresses") or not self.coordinator.base_addresses:
            _LOGGER.error(
                "❌ FLOW_LINE_OFFSET: Coordinator base_addresses not available for %s",
                self.entity_id,
            )
            return

        base_address = self.coordinator.base_addresses.get(self._hc_index)

        if base_address is None:
            _LOGGER.error(
                "❌ FLOW_LINE_OFFSET: Base address not found for hc_index=%d (available keys: %s)",
                self._hc_index,
                list(self.coordinator.base_addresses.keys()),
            )
            return

        register_address = base_address + self._relative_address
        # z.B. HC1: 5000 + 50 = 5050, HC2: 5100 + 50 = 5150

        # 5. Hole slave_id (konsistent mit climate.py)
        slave_id = self._entry.data.get("slave_id", 1)

        _LOGGER.info(
            "✍️ FLOW_LINE_OFFSET: Writing to HC%d, base_address=%d, relative_address=%d, "
            "register_address=%d, raw_value=%d (%.1f°C), slave_id=%d",
            self._hc_index,
            base_address,
            self._relative_address,
            register_address,
            raw_value,
            value,
            slave_id,
        )

        # 6. Schreibe auf Modbus
        from .modbus_utils import async_write_registers

        try:
            result = await async_write_registers(
                self.coordinator.client,
                register_address,
                [raw_value],
                slave_id,
            )

            if hasattr(result, "isError") and result.isError():
                _LOGGER.error(
                    "❌ FLOW_LINE_OFFSET: Failed to write to HC%d (address=%d): %s",
                    self._hc_index,
                    register_address,
                    result,
                )
                return

            _LOGGER.info(
                "✅ FLOW_LINE_OFFSET: Successfully wrote to HC%d (address=%d, value=%d, %.1f°C)",
                self._hc_index,
                register_address,
                raw_value,
                value,
            )

        except Exception as ex:
            _LOGGER.error(
                "❌ FLOW_LINE_OFFSET: Exception writing to HC%d (address=%d): %s",
                self._hc_index,
                register_address,
                ex,
                exc_info=True,
            )
            return

        # 7. Aktualisiere lokalen State
        self._attr_native_value = float(value)

        # 8. Aktualisiere Coordinator-Cache (damit native_value sofort den neuen Wert zeigt)
        # WICHTIG: Coordinator speichert Werte bereits mit Scale konvertiert (in °C)
        # Daher speichern wir den konvertierten Wert, nicht den raw Modbus-Wert
        if self.coordinator.data:
            self.coordinator.data[self._coordinator_key] = value
            _LOGGER.debug(
                "🔄 FLOW_LINE_OFFSET: Updated coordinator cache: %s = %.1f°C",
                self._coordinator_key,
                value,
            )

        # 9. UI aktualisieren
        self.async_write_ha_state()

        _LOGGER.info(
            "✅ FLOW_LINE_OFFSET: Completed write for HC%d = %.1f°C",
            self._hc_index,
            value,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Wird automatisch aufgerufen, wenn Coordinator Daten aktualisiert."""
        # Aktualisiere UI, wenn Modbus-Wert sich geändert hat
        self.async_write_ha_state()

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information for this number entity."""
        return build_subdevice_info(self._entry, "hc", self._hc_index)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes for diagnostics."""
        return {
            "hc_index": self._hc_index,
            "relative_address": self._relative_address,
            "register_address": (
                self.coordinator.base_addresses.get(self._hc_index, 0)
                + self._relative_address
                if hasattr(self.coordinator, "base_addresses")
                and self.coordinator.base_addresses
                else None
            ),
        }


class LambdaEcoTempReductionNumber(RestoreNumber, NumberEntity):
    """Number entity representing eco temperature reduction for heating circuit."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        hc_index: int,
        name: str,
        entity_id: str,
        unique_id: str,
        spec: dict[str, Any],
    ) -> None:
        self._entry = entry
        self._hc_index = hc_index
        self.entity_id = entity_id
        self._attr_name = name
        self._attr_unique_id = unique_id

        self._attr_native_unit_of_measurement = spec.get("unit")
        self._attr_native_min_value = spec.get("min_value")
        self._attr_native_max_value = spec.get("max_value")
        self._attr_native_step = spec.get("step")
        self._attr_mode = NumberMode.BOX

        # Setze Icon aus der Config
        self._attr_icon = get_entity_icon(spec, default_icon="mdi:thermometer-minus")

        default_value = spec.get("default", -1.0)
        self._attr_native_value = float(default_value)
        precision = spec.get("precision")
        if precision is not None:
            self._attr_suggested_display_precision = precision

    async def async_added_to_hass(self) -> None:
        """Restore the previous state when added to Home Assistant."""
        await super().async_added_to_hass()
        last_number_data = await self.async_get_last_number_data()
        if last_number_data and last_number_data.native_value is not None:
            self._attr_native_value = float(last_number_data.native_value)
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Persist the newly set value."""
        self._attr_native_value = float(value)
        self.async_write_ha_state()

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information for this number entity."""
        if self._hc_index:
            return build_subdevice_info(self._entry, "hc", self._hc_index)
        return build_device_info(self._entry)

