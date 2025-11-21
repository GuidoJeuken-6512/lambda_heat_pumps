"""Template sensor platform for Lambda WP integration."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.template import Template
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.template import TemplateError
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CALCULATED_SENSOR_TEMPLATES,
    HC_HEATING_CURVE_NUMBER_CONFIG,
    HC_ROOM_THERMOSTAT_NUMBER_CONFIG,
)
from .coordinator import LambdaDataUpdateCoordinator
from .utils import (
    build_device_info,
    build_subdevice_info,
    extract_device_info_from_sensor_id,
    generate_sensor_names,
    generate_template_entity_prefix,
    load_sensor_translations,
    load_lambda_config,
    get_firmware_version_int,
    get_compatible_sensors,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Lambda Template sensors."""
    _LOGGER.debug("Setting up Lambda template sensors for entry %s", entry.entry_id)

    # Get coordinator from hass.data
    coordinator_data = hass.data[DOMAIN][entry.entry_id]
    if not coordinator_data or "coordinator" not in coordinator_data:
        _LOGGER.error("No coordinator found for entry %s", entry.entry_id)
        return

    coordinator = coordinator_data["coordinator"]
    _LOGGER.debug("Found coordinator: %s", coordinator)

    # Get device counts from config
    num_hps = entry.data.get("num_hps", 1)
    num_boil = entry.data.get("num_boil", 1)
    num_buff = entry.data.get("num_buff", 0)
    num_sol = entry.data.get("num_sol", 0)
    num_hc = entry.data.get("num_hc", 1)

    # Hole den Legacy-Modbus-Namen-Switch aus der Config
    use_legacy_modbus_names = entry.data.get("use_legacy_modbus_names", True)
    name_prefix = entry.data.get("name", "").lower().replace(" ", "")
    room_thermostat_enabled = entry.options.get("room_thermostat_control", False)
    sensor_translations = await load_sensor_translations(hass)

    # Lade cycling_offsets aus der Konfiguration
    lambda_config = await load_lambda_config(hass)
    cycling_offsets = lambda_config.get("cycling_offsets", {})

    # Get firmware version and filter compatible sensors
    fw_version = get_firmware_version_int(entry)
    _LOGGER.debug(
        "Filtering template sensors for firmware version (numeric: %d)",
        fw_version,
    )

    # Filter compatible template sensors
    compatible_templates = get_compatible_sensors(
        CALCULATED_SENSOR_TEMPLATES, fw_version
    )

    # Create template sensors for each device type
    template_sensors = []

    # Device type mapping
    DEVICE_COUNTS = {
        "hp": num_hps,
        "boil": num_boil,
        "buff": num_buff,
        "sol": num_sol,
        "hc": num_hc,
    }

    # Create template sensors for each device type
    for device_type, count in DEVICE_COUNTS.items():
        for idx in range(1, count + 1):
            device_prefix = f"{device_type}{idx}"
            # Nur Template-Sensoren mit "template"-Feld erzeugen
            # (ausschließlich Daily-Sensoren)
            for sensor_id, sensor_info in compatible_templates.items():
                if (
                    sensor_info.get("device_type") == device_type
                    and "template" in sensor_info
                    and not sensor_id.endswith("_cycling_total")
                    and not sensor_id.endswith("_cycling_yesterday")
                ):
                    # Generate consistent names using centralized function
                    naming = generate_sensor_names(
                        device_prefix=device_prefix,
                        sensor_name=sensor_info["name"],
                        sensor_id=sensor_id,
                        name_prefix=name_prefix,
                        use_legacy_modbus_names=use_legacy_modbus_names,
                        translations=sensor_translations,
                    )
                    # Generate entity prefix for template
                    full_entity_prefix = generate_template_entity_prefix(
                        device_prefix=device_prefix,
                        name_prefix=name_prefix,
                        use_legacy_modbus_names=use_legacy_modbus_names,
                    )
                    # Offset bestimmen
                    cycling_offset = 0
                    if sensor_id.endswith("_cycling_total"):
                        device_offsets = cycling_offsets.get(device_prefix, {})
                        cycling_offset = device_offsets.get(sensor_id, 0)
                    # Template immer mit cycling_offset formatieren
                    format_kwargs = {
                        "full_entity_prefix": full_entity_prefix,
                        "cycling_offset": cycling_offset,
                    }
                    if "format_params" in sensor_info and isinstance(
                        sensor_info["format_params"], dict
                    ):
                        format_kwargs.update(sensor_info["format_params"])
                    is_heating_curve = (
                        sensor_id == "heating_curve_flow_line_temperature_calc"
                    )
                    if is_heating_curve:
                        ambient_suffix = "ambient_temperature_calculated"
                        if use_legacy_modbus_names and name_prefix:
                            ambient_sensor_entity = (
                                f"sensor.{name_prefix}_{ambient_suffix}"
                            )
                        else:
                            ambient_sensor_entity = f"sensor.{ambient_suffix}"
                        format_kwargs["ambient_sensor"] = ambient_sensor_entity

                        number_entities = {}
                        defaults = {}
                        for key in [
                            "heating_curve_cold_outside_temp",
                            "heating_curve_mid_outside_temp",
                            "heating_curve_warm_outside_temp",
                        ]:
                            number_spec = HC_HEATING_CURVE_NUMBER_CONFIG[key]
                            number_names = generate_sensor_names(
                                device_prefix=device_prefix,
                                sensor_name=number_spec["name"],
                                sensor_id=key,
                                name_prefix=name_prefix,
                                use_legacy_modbus_names=use_legacy_modbus_names,
                                translations=sensor_translations,
                            )
                            number_entity_id = number_names["entity_id"].replace(
                                "sensor.", "number.", 1
                            )
                            number_entities[key] = number_entity_id
                            defaults[key] = number_spec["default"]

                        if room_thermostat_enabled:
                            for key, number_spec in HC_ROOM_THERMOSTAT_NUMBER_CONFIG.items():
                                number_names = generate_sensor_names(
                                    device_prefix=device_prefix,
                                    sensor_name=number_spec["name"],
                                    sensor_id=key,
                                    name_prefix=name_prefix,
                                    use_legacy_modbus_names=use_legacy_modbus_names,
                                    translations=sensor_translations,
                                )
                                base_entity_id = number_names["entity_id"]
                                if base_entity_id.startswith("sensor."):
                                    number_entity_id = base_entity_id.replace(
                                        "sensor.", "number.", 1
                                    )
                                elif "." in base_entity_id:
                                    number_entity_id = (
                                        f"number.{base_entity_id.split('.', 1)[1]}"
                                    )
                                else:
                                    number_entity_id = f"number.{base_entity_id}"
                                number_entities[key] = number_entity_id
                                defaults[key] = number_spec["default"]

                        template_sensors.append(
                            LambdaHeatingCurveCalcSensor(
                                coordinator=coordinator,
                                entry=entry,
                                sensor_id=f"{device_prefix}_{sensor_id}",
                                name=naming["name"],
                                unit=sensor_info.get("unit", ""),
                                state_class=sensor_info.get("state_class", ""),
                                device_class=sensor_info.get("device_class"),
                                device_type=device_type,
                                precision=sensor_info.get("precision"),
                                entity_id=naming["entity_id"],
                                unique_id=naming["unique_id"],
                                ambient_sensor=ambient_sensor_entity,
                                number_entities=number_entities,
                                temp_points={
                                    "cold": format_kwargs.get("cold_point"),
                                    "mid": format_kwargs.get("mid_point"),
                                    "warm": format_kwargs.get("warm_point"),
                                },
                                defaults=defaults,
                                room_thermostat_enabled=room_thermostat_enabled,
                            )
                        )
                        _LOGGER.info(
                            "Heizkurven-Berechnung für %s nutzt ambient_sensor=%s, stützpunkte=[%s, %s, %s]",
                            naming["entity_id"],
                            ambient_sensor_entity,
                            format_kwargs.get("cold_point"),
                            format_kwargs.get("mid_point"),
                            format_kwargs.get("warm_point"),
                        )
                        continue

                    template_str = sensor_info["template"].format(**format_kwargs)
                    _LOGGER.debug(
                        "Creating template sensor %s with template: %s",
                        naming["entity_id"],
                        template_str,
                    )
                    template_sensors.append(
                        LambdaTemplateSensor(
                            coordinator=coordinator,
                            entry=entry,
                            sensor_id=f"{device_prefix}_{sensor_id}",
                            name=naming["name"],
                            unit=sensor_info.get("unit", ""),
                            state_class=sensor_info.get("state_class", ""),
                            device_class=sensor_info.get("device_class"),
                            device_type=device_type,
                            precision=sensor_info.get("precision"),
                            entity_id=naming["entity_id"],
                            unique_id=naming["unique_id"],
                            template_str=template_str,
                        )
                    )

    if template_sensors:
        async_add_entities(template_sensors)
        _LOGGER.debug("Added %d template sensors", len(template_sensors))


class LambdaTemplateSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Lambda template sensor."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: LambdaDataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_id: str,
        name: str,
        unit: str,
        state_class: str,
        device_class: SensorDeviceClass,
        device_type: str,
        precision: int | float | None = None,
        entity_id: str | None = None,
        unique_id: str | None = None,
        template_str: str = "",
    ) -> None:
        """Initialize the template sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._entry = entry
        self._sensor_id = sensor_id
        self._name = name
        self._unit = unit
        self._state_class = state_class
        self._device_class = device_class
        parsed_type, parsed_index = extract_device_info_from_sensor_id(sensor_id)
        self._device_type = (device_type or parsed_type or "").lower()
        self._device_index = parsed_index
        self._precision = precision
        self._entity_id = entity_id
        self._unique_id = unique_id
        self._template_str = template_str
        self._template = None  # Will be set in async_added_to_hass
        self._state = None
        self._last_warning = None

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._unique_id

    @property
    def native_value(self) -> float | str | None:
        """Return the state of the sensor."""
        return self._state

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of the sensor."""
        return self._unit

    @property
    def state_class(self) -> SensorStateClass | None:
        """Return the state class of the sensor."""
        if self._state_class == "measurement":
            return SensorStateClass.MEASUREMENT
        elif self._state_class == "total":
            return SensorStateClass.TOTAL
        elif self._state_class == "total_increasing":
            return SensorStateClass.TOTAL_INCREASING
        return None

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the device class of the sensor."""
        if self._device_class == "temperature":
            return SensorDeviceClass.TEMPERATURE
        elif self._device_class == "power":
            return SensorDeviceClass.POWER
        elif self._device_class == "energy":
            return SensorDeviceClass.ENERGY
        return None

    @property
    def device_info(self):
        """Return device info."""
        parsed_type, parsed_index = extract_device_info_from_sensor_id(self._sensor_id)
        device_type = self._device_type or parsed_type
        device_index = self._device_index or parsed_index
        if device_type and device_index:
            return build_subdevice_info(self._entry, device_type, device_index)
        return build_device_info(self._entry)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self._template is None:
            return

        try:
            # Render the template
            self._state = self._template.async_render()

            _LOGGER.debug(
                "Template sensor %s rendered state: %s (template: %s)",
                self._sensor_id,
                self._state,
                self._template_str,
            )

            # Handle unavailable or None states
            if (
                self._state is None
                or self._state == "unavailable"
                or self._state == "unknown"
            ):
                self._state = None
                self.async_write_ha_state()
                return

            # Convert to appropriate type and apply precision
            if isinstance(self._state, str):
                # Try to convert string to float
                try:
                    float_value = float(self._state)
                    if self._precision is not None:
                        if self._precision == 0:
                            # For precision 0, convert to integer
                            self._state = int(round(float_value, 0))
                        else:
                            self._state = round(float_value, self._precision)
                    else:
                        self._state = float_value
                except (ValueError, TypeError):
                    # Keep as string if conversion fails
                    pass
            elif isinstance(self._state, (int, float)):
                # Apply precision to numeric values
                if self._precision is not None:
                    if self._precision == 0:
                        self._state = int(round(self._state, 0))
                    else:
                        self._state = round(self._state, self._precision)

        except TemplateError as err:
            _LOGGER.warning(
                "Template error for sensor %s: %s (template: %s)",
                self._sensor_id,
                err,
                self._template_str,
            )
            self._state = None
        except Exception as err:
            _LOGGER.error(
                "Unexpected error in template sensor %s: %s (template: %s)",
                self._sensor_id,
                err,
                self._template_str,
            )
            self._state = None

        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()

        # Initialize the template now that we have access to hass
        self._template = Template(self._template_str, self.hass)

        self._handle_coordinator_update()


class LambdaHeatingCurveCalcSensor(CoordinatorEntity, SensorEntity):
    """Berechnet die Heizkurven-Vorlauftemperatur pro HC."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: LambdaDataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_id: str,
        name: str,
        unit: str,
        state_class: str,
        device_class: SensorDeviceClass,
        device_type: str,
        precision: int | float | None,
        entity_id: str,
        unique_id: str,
        ambient_sensor: str,
        number_entities: dict[str, str],
        temp_points: dict[str, float],
        defaults: dict[str, float],
        room_thermostat_enabled: bool,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._sensor_id = sensor_id
        self._name = name
        self._unit = unit
        self._state_class = state_class
        self._device_class = device_class
        self._device_type = device_type
        self._precision = precision
        self._entity_id = entity_id
        self._unique_id = unique_id
        self.entity_id = entity_id
        self._ambient_sensor = ambient_sensor
        self._number_entities = number_entities
        self._temp_points = temp_points
        self._defaults = defaults
        self._state = None
        self._last_warning = None
        self._room_thermostat_enabled = room_thermostat_enabled
        self._last_adjustment = 0.0
        self._last_rt_delta = None
        self._last_flow_offset = 0.0

        parsed_type, parsed_index = extract_device_info_from_sensor_id(sensor_id)
        self._device_type = (device_type or parsed_type or "").lower()
        self._device_index = parsed_index

        if state_class == "measurement":
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif state_class == "total":
            self._attr_state_class = SensorStateClass.TOTAL
        elif state_class == "total_increasing":
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        else:
            self._attr_state_class = None

        if device_class == "temperature":
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
        elif device_class == "power":
            self._attr_device_class = SensorDeviceClass.POWER
        elif device_class == "energy":
            self._attr_device_class = SensorDeviceClass.ENERGY
        else:
            self._attr_device_class = None

        self._attr_native_unit_of_measurement = unit
        if precision is not None:
            try:
                self._attr_suggested_display_precision = int(precision)
            except (TypeError, ValueError):
                pass

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def native_value(self):
        return self._state

    @property
    def device_info(self):
        parsed_type, parsed_index = extract_device_info_from_sensor_id(self._sensor_id)
        device_type = self._device_type or parsed_type
        device_index = self._device_index or parsed_index
        if device_type and device_index:
            return build_subdevice_info(self._entry, device_type, device_index)
        return build_device_info(self._entry)

    @property
    def extra_state_attributes(self):
        return {
            "ambient_sensor": self._ambient_sensor,
            "room_thermostat_enabled": self._room_thermostat_enabled,
            "room_thermostat_adjustment": self._last_adjustment,
            "room_thermostat_delta": self._last_rt_delta,
            "flow_line_offset": self._last_flow_offset,
        }

    def _get_float_state(self, entity_id: str, default: float | None) -> float | None:
        state_obj = self.hass.states.get(entity_id)
        if not state_obj or state_obj.state in (None, "unknown", "unavailable"):
            return default
        try:
            return float(state_obj.state)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _lerp(x: float, x_a: float, y_a: float, x_b: float, y_b: float) -> float:
        if x_b == x_a:
            return y_a
        return y_a + (x - x_a) * (y_b - y_a) / (x_b - x_a)

    @callback
    def _handle_coordinator_update(self) -> None:
        self._last_adjustment = 0.0
        self._last_rt_delta = None
        self._last_flow_offset = 0.0
        ambient = self._get_float_state(self._ambient_sensor, None)
        if ambient is None:
            self._state = None
            self.async_write_ha_state()
            return

        cold_entity = self._number_entities["heating_curve_cold_outside_temp"]
        mid_entity = self._number_entities["heating_curve_mid_outside_temp"]
        warm_entity = self._number_entities["heating_curve_warm_outside_temp"]

        y_cold = self._get_float_state(
            cold_entity,
            self._defaults["heating_curve_cold_outside_temp"],
        )
        y_mid = self._get_float_state(mid_entity, self._defaults["heating_curve_mid_outside_temp"])
        y_warm = self._get_float_state(
            warm_entity,
            self._defaults["heating_curve_warm_outside_temp"],
        )

        warnings: list[str] = []
        if y_cold is not None and y_mid is not None and y_cold <= y_mid:
            warnings.append(f"Heizkurve: cold ({y_cold}) <= mid ({y_mid})")
        elif y_mid is not None and y_warm is not None and y_mid <= y_warm:
            warnings.append(f"Heizkurve: mid ({y_mid}) <= warm ({y_warm})")

        if warnings:
            warning_text = "; ".join(warnings)
            if warning_text != self._last_warning:
                _LOGGER.warning(
                    "%s — Werte unplausibel: %s (Entities: cold=%s, mid=%s, warm=%s)",
                    self.entity_id,
                    warning_text,
                    cold_entity,
                    mid_entity,
                    warm_entity,
                )
                self._last_warning = warning_text
            self._state = None
            self.async_write_ha_state()
            return
        self._last_warning = None

        x_cold = self._temp_points.get("cold", -22.0)
        x_mid = self._temp_points.get("mid", 0.0)
        x_warm = self._temp_points.get("warm", 22.0)

        result: float
        if ambient >= x_warm:
            result = y_warm
        elif ambient > x_mid:
            result = self._lerp(ambient, x_mid, y_mid, x_warm, y_warm)
        elif ambient > x_cold:
            result = self._lerp(ambient, x_cold, y_cold, x_mid, y_mid)
        else:
            result = y_cold

        adjustment = 0.0
        rt_delta = None
        offset_value = None
        factor_value = None

        if self._room_thermostat_enabled:
            offset_entity = self._number_entities.get("room_thermostat_offset")
            factor_entity = self._number_entities.get("room_thermostat_factor")

            if offset_entity and factor_entity:
                offset_value = self._get_float_state(
                    offset_entity, self._defaults.get("room_thermostat_offset", 0.0)
                )
                factor_value = self._get_float_state(
                    factor_entity, self._defaults.get("room_thermostat_factor", 1.0)
                )

                if offset_value is None or factor_value is None:
                    _LOGGER.warning(
                        "%s — Raumthermostat-Werte fehlen (offset=%s, factor=%s), keine Verschiebung angewandt.",
                        self.entity_id,
                        offset_value,
                        factor_value,
                    )
                elif factor_value <= 0:
                    _LOGGER.warning(
                        "%s — Raumthermostat-Faktor unplausibel (%.2f), keine Verschiebung angewandt.",
                        self.entity_id,
                        factor_value,
                    )
                else:
                    data = self.coordinator.data or {}
                    idx = self._device_index
                    current_temp = (
                        data.get(f"hc{idx}_room_device_temperature") if idx else None
                    )
                    target_temp = (
                        data.get(f"hc{idx}_target_room_temperature") if idx else None
                    )

                    if current_temp is None or target_temp is None:
                        _LOGGER.debug(
                            "%s — Raumthermostatwerte fehlen im Coordinator (current=%s, target=%s)",
                            self.entity_id,
                            current_temp,
                            target_temp,
                        )
                    else:
                        try:
                            rt_delta = float(target_temp) - float(current_temp)
                            adjustment = (rt_delta - float(offset_value)) * float(
                                factor_value
                            )
                            result += adjustment
                        except (TypeError, ValueError):
                            _LOGGER.warning(
                                "%s — Raumthermostatberechnung fehlgeschlagen (delta=%s, offset=%s, factor=%s)",
                                self.entity_id,
                                rt_delta,
                                offset_value,
                                factor_value,
                            )

        flow_line_offset = 0.0
        data = self.coordinator.data or {}
        idx = self._device_index
        if idx is not None:
            offset_key = f"hc{idx}_set_flow_line_offset_temperature"
            raw_offset = data.get(offset_key)
            if raw_offset is not None:
                try:
                    flow_line_offset = float(raw_offset)
                    result += flow_line_offset
                except (TypeError, ValueError):
                    _LOGGER.warning(
                        "%s — Flow-Line-Offset (%s) konnte nicht verarbeitet werden: %s",
                        self.entity_id,
                        offset_key,
                        raw_offset,
                    )

        if self._precision is not None:
            result = round(result, int(self._precision))

        self._state = result
        self._last_adjustment = adjustment
        self._last_rt_delta = rt_delta
        self._last_flow_offset = flow_line_offset
        def _fmt(value: float | None) -> str:
            return f"{value:.2f}" if value is not None else "n/a"

        _LOGGER.info(
            "Heizkurven-Wert %s: ambient=%.2f°C, y_cold=%s°C, y_mid=%s°C, y_warm=%s°C, flow_offset=%.2f°C, rt_enabled=%s, delta=%s, offset=%s, factor=%s, adjustment=%.2f°C -> %.2f°C",
            self.entity_id,
            ambient,
            _fmt(y_cold),
            _fmt(y_mid),
            _fmt(y_warm),
            flow_line_offset,
            self._room_thermostat_enabled,
            _fmt(rt_delta),
            _fmt(offset_value),
            _fmt(factor_value),
            adjustment,
            result,
        )

        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._handle_coordinator_update()
