"""The Lambda Cockpit: two dashboard cards and a dashboard, shipped with the integration.

The cards are served from the integration's `frontend/` folder and loaded into
every browser, whatever the dashboard option says, so they can be used on any
dashboard.

The dashboard itself is opt-in (`CONF_INSTALL_DASHBOARD`); switching the option
off again removes it. Home Assistant has no
API for an integration to create a dashboard, so it is written the way the
frontend would have saved it: its config to `.storage/lovelace.<id>` and its
entry to `.storage/lovelace_dashboards`. Lovelace reads that list only on
startup, so a new dashboard needs a restart to appear — which a repair issue
offers. A dashboard Lovelace already knows is updated in place instead, live.

Which entity ids the cards show is not guessed from the device name: each one is
looked up in the entity registry by its unique id, so renamed entities, `_2`
suffixes and legacy prefixes all resolve to what is really there.
"""

from __future__ import annotations

import hashlib
import inspect
import logging
from pathlib import Path
from typing import Any

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.storage import Store

from .const import (
    CONF_INSTALL_DASHBOARD,
    CONF_NAME_PREFIX,
    CONF_PV_POWER_SENSOR_ENTITY,
    CONF_PV_SURPLUS,
    CONF_ROOM_TEMPERATURE_ENTITY,
    CONF_ROOM_THERMOSTAT_CONTROL,
    CONF_USE_LEGACY_MODBUS_NAMES,
    DASHBOARD_LAYOUT_VERSION,
    DASHBOARD_URL_PATH,
    DOMAIN,
    ISSUE_DASHBOARD_RESTART,
)
from .coordinator import LambdaConfigEntry

_LOGGER = logging.getLogger(__name__)

FRONTEND_URL = f"/{DOMAIN}/frontend"
FRONTEND_CARDS = ("lambda-cockpit-card.js", "lambda-entities-card.js")
_FRONTEND_REGISTERED = f"{DOMAIN}_frontend_registered"

# Lovelace's own storage, as its dashboards collection writes it: the id is the
# slugified url path, and a storage dashboard's config lives under that id.
_DASHBOARD_ID = DASHBOARD_URL_PATH.replace("-", "_")
_DASHBOARD_CONFIG_KEY = f"lovelace.{_DASHBOARD_ID}"
_DASHBOARDS_KEY = "lovelace_dashboards"
_ENTITIES_PATH = f"{DASHBOARD_URL_PATH}-entities"

# Which layout each config entry's dashboard was written with, so a newer one is
# written once and an unchanged one is left alone. Kept apart from the entry's
# options, which the options flow replaces wholesale on every save.
_STATE_KEY = f"{DOMAIN}.dashboard"
_STATE_VERSION = 1

# What each of the cockpit's slots shows: (slot, domain, module, key). The
# unique id is built the way entity.py builds it; module None is the controller.
# The cards treat a slot that is missing as "not available" and hide what
# depends on it.
_SLOTS: tuple[tuple[str, str, str | None, str], ...] = (
    # Heat pump
    ("op", "sensor", "hp", "operating_state"),
    ("hpstate", "sensor", "hp", "state"),
    ("err", "sensor", "hp", "error_state"),
    ("errnum", "sensor", "hp", "error_number"),
    ("heizstab", "sensor", "hp", "relais_state_2nd_heating_stage"),
    ("vl", "sensor", "hp", "flow_line_temperature"),
    ("rl", "sensor", "hp", "return_line_temperature"),
    ("flow", "sensor", "hp", "volume_flow_heat_sink"),
    ("rating", "sensor", "hp", "compressor_unit_rating"),
    ("heat", "sensor", "hp", "actual_heating_capacity"),
    ("power", "sensor", "hp", "inverter_power_consumption"),
    ("cop", "sensor", "hp", "cop"),
    ("at", "sensor", "hp", "energy_source_inlet_temperature"),
    ("at1h", "sensor", None, "ambient_temperature_1h"),
    ("atcalc", "sensor", None, "ambient_temperature_calculated"),
    ("pv_surplus", "sensor", None, "emgr_actual_power"),
    # Hot water
    ("ww_top", "sensor", "boil", "actual_high_temperature"),
    ("ww_low", "sensor", "boil", "actual_low_temperature"),
    ("ww_set", "sensor", "boil", "target_high_temperature"),
    ("ww_state", "sensor", "boil", "operating_state"),
    ("ww_zirk", "sensor", "boil", "actual_circulation_temperature"),
    ("ww_zirk_pump", "sensor", "boil", "actual_circulation_pump_state"),
    ("ww_climate", "climate", "boil", "hot_water"),
    ("ww_pv_offset", "number", "boil", "pv_temperature_increase_number"),
    # Buffer
    ("buf_top", "sensor", "buff", "actual_high_temperature"),
    ("buf_low", "sensor", "buff", "actual_low_temperature"),
    ("buf_max", "number", "buff", "maximum_buffer_temp_number"),
    ("buf_state", "sensor", "buff", "operating_state"),
    ("buf_pv_offset", "number", "buff", "pv_temperature_increase_number"),
    # Heating circuit
    ("hc_vl", "sensor", "hc", "flow_line_temperature"),
    ("hc_rl", "sensor", "hc", "return_line_temperature"),
    ("hc_soll", "sensor", "hc", "target_temp_flow_line"),
    ("hc_soll_old", "sensor", "hc", "flow_line_temperature_setpoint"),
    ("hc_state", "sensor", "hc", "operating_state"),
    ("offset", "number", "hc", "flow_line_offset_temperature_number"),
    ("pv_offset", "number", "hc", "pv_temperature_increase_number"),
    ("room_set", "sensor", "hc", "target_room_temperature"),
    ("raum_soll", "number", "hc", "target_room_temperature_number"),
    ("curve_m22", "number", "hc", "heating_curve_cold_outside_temp_number"),
    ("curve_0", "number", "hc", "heating_curve_mid_outside_temp_number"),
    ("curve_p22", "number", "hc", "heating_curve_warm_outside_temp_number"),
    ("curve_calc", "sensor", "hc", "heating_curve_flow_line_temperature_calc"),
    ("wfp_at", "sensor", "hc", "schedule_outside_temperature_calc"),
    # Today
    ("strom_hz", "sensor", "hp", "heating_energy_daily"),
    ("strom_ww", "sensor", "hp", "hot_water_energy_daily"),
    ("strom_abt", "sensor", "hp", "defrost_energy_daily"),
    ("strom_kuehl", "sensor", "hp", "cooling_energy_daily"),
    ("strom_sb", "sensor", "hp", "stby_energy_daily"),
    ("waerme_hz", "sensor", "hp", "heating_thermal_energy_daily"),
    ("waerme_ww", "sensor", "hp", "hot_water_thermal_energy_daily"),
    ("waerme_abt", "sensor", "hp", "defrost_thermal_energy_daily"),
    ("waerme_kuehl", "sensor", "hp", "cooling_thermal_energy_daily"),
    ("starts_hz", "sensor", "hp", "heating_cycling_daily"),
    ("starts_ww", "sensor", "hp", "hot_water_cycling_daily"),
    ("umschalt", "sensor", "hp", "heating_to_hot_water_cycling_daily"),
    ("abtau_tag", "sensor", "hp", "defrost_cycling_daily"),
    ("lz_hz", "sensor", "hp", "heating_runtime_daily"),
    ("lz_ww", "sensor", "hp", "hot_water_runtime_daily"),
    ("lz_abt", "sensor", "hp", "defrost_runtime_daily"),
    ("lz_hs", "sensor", "hp", "heating_rod_runtime_daily"),
    # Lifetime
    ("e_in", "sensor", "hp", "compressor_power_consumption_accumulated"),
    ("e_out", "sensor", "hp", "compressor_thermal_energy_output_accumulated"),
    ("hz_in", "sensor", "hp", "heating_energy_total"),
    ("hz_out", "sensor", "hp", "heating_thermal_energy_total"),
    ("ww_in", "sensor", "hp", "hot_water_energy_total"),
    ("ww_out", "sensor", "hp", "hot_water_thermal_energy_total"),
    ("cnt_abtau", "sensor", "hp", "defrost_cycling_total"),
    # Settings the user copies from the display
    ("p_ww_ein", "number", "boil", "dhw_switch_on_hysteresis_number"),
    ("p_ww_aus", "number", "boil", "dhw_switch_off_hysteresis_number"),
    ("p_ww_max", "number", "boil", "dhw_maximum_temperature_number"),
    ("p_buf_ein25", "number", "buff", "buffer_switch_on_hysteresis_25_number"),
    ("p_buf_ein50", "number", "buff", "buffer_switch_on_hysteresis_50_number"),
    ("p_buf_aus", "number", "buff", "buffer_switch_off_hysteresis_number"),
    ("p_buf_off", "number", "buff", "buffer_setpoint_offset_number"),
    ("p_hk_ein", "number", "hc", "hc_switch_on_hysteresis_number"),
    ("p_hk_aus", "number", "hc", "hc_switch_off_hysteresis_number"),
    ("p_hk_spr", "number", "hc", "hc_temperature_spread_number"),
    ("p_hk_grenze", "number", "hc", "heating_limit_outside_temperature_number"),
    ("p_hk_max", "number", "hc", "hc_maximum_flow_temperature_number"),
)


async def async_register_frontend(hass: HomeAssistant) -> None:
    """Serve the cards and load them into every browser, once per Home Assistant run.

    A static path cannot be registered twice, and an entry that reloads would
    try to, so this is guarded for the life of the process.
    """
    if hass.data.get(_FRONTEND_REGISTERED):
        return
    # Always there in a real installation; a bare test instance has neither.
    if "frontend" not in hass.config.components or getattr(hass, "http", None) is None:
        return
    hass.data[_FRONTEND_REGISTERED] = True
    folder = Path(__file__).parent / "frontend"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(FRONTEND_URL, str(folder), cache_headers=False)]
    )
    keys = await hass.async_add_executor_job(_card_cache_keys, folder)
    for card in FRONTEND_CARDS:
        add_extra_js_url(hass, f"{FRONTEND_URL}/{card}?v={keys[card]}")


def _card_cache_keys(folder: Path) -> dict[str, str]:
    """A key per card from its content, so a browser fetches it again on any change.

    The integration's version stays the same between releases, so a browser
    kept an old card next to a newer integration and showed its values wrong.
    """
    return {
        card: hashlib.sha256((folder / card).read_bytes()).hexdigest()[:12]
        for card in FRONTEND_CARDS
    }


def _unique_id(entry: LambdaConfigEntry, module: str | None, index: int, key: str) -> str:
    """The unique id entity.py gives an entity, see LambdaEntity."""
    prefix = entry.data[CONF_NAME_PREFIX].lower().replace(" ", "")
    legacy = f"{prefix}_" if entry.data[CONF_USE_LEGACY_MODBUS_NAMES] else ""
    module_prefix = f"{module}{index}_" if module else ""
    return f"{legacy}{module_prefix}{key}"


def resolve_entities(
    hass: HomeAssistant, entry: LambdaConfigEntry, indexes: dict[str, int] | None = None
) -> dict[str, str]:
    """The entity id behind each of the cockpit's slots, for one module of each kind."""
    indexes = indexes or {}
    registry = er.async_get(hass)
    resolved: dict[str, str] = {}
    for slot, domain, module, key in _SLOTS:
        index = indexes.get(module or "", 1)
        entity_id = registry.async_get_entity_id(
            domain, DOMAIN, _unique_id(entry, module, index, key)
        )
        if entity_id is not None:
            resolved[slot] = entity_id
    # The older firmware's flow setpoint stands in for the newer one.
    if "hc_soll" not in resolved and "hc_soll_old" in resolved:
        resolved["hc_soll"] = resolved["hc_soll_old"]
    resolved.pop("hc_soll_old", None)
    return resolved


def _external_entities(entry: LambdaConfigEntry) -> dict[str, str]:
    """The entities the cockpit shows that do not belong to the integration."""
    options = entry.options
    external: dict[str, str] = {}
    if options.get(CONF_ROOM_THERMOSTAT_CONTROL) and (
        room := options.get(CONF_ROOM_TEMPERATURE_ENTITY.format(1))
    ):
        external["room"] = room
    if options.get(CONF_PV_SURPLUS) and (pv := options.get(CONF_PV_POWER_SENSOR_ENTITY)):
        external["pv_source"] = pv
    return external


def _features(entry: LambdaConfigEntry) -> dict[str, bool]:
    """Which of the integration's functions are switched on, for the cards to show."""
    options = entry.options
    return {
        "room_thermostat": bool(options.get(CONF_ROOM_THERMOSTAT_CONTROL, False)),
        "pv_surplus": bool(options.get(CONF_PV_SURPLUS, False)),
    }


def build_dashboard(hass: HomeAssistant, entry: LambdaConfigEntry) -> dict[str, Any]:
    """The dashboard's config: the cockpit, and the entity overview behind it."""
    entities = {**resolve_entities(hass, entry), **_external_entities(entry)}
    german = str(hass.config.language or "en").startswith("de")
    return {
        "title": "Lambda",
        "views": [
            {
                "title": "Cockpit",
                "path": "cockpit",
                "icon": "mdi:heat-pump",
                "type": "panel",
                "cards": [
                    {
                        "type": "custom:lambda-cockpit-card",
                        "config_entry": entry.entry_id,
                        "details_path": f"/{DASHBOARD_URL_PATH}/{_ENTITIES_PATH}",
                        "features": _features(entry),
                        "entities": entities,
                    }
                ],
            },
            {
                "title": "Lambda Entitäten" if german else "Lambda entities",
                "path": _ENTITIES_PATH,
                "icon": "mdi:format-list-bulleted-type",
                "type": "panel",
                "subview": True,
                "cards": [
                    {
                        "type": "custom:lambda-entities-card",
                        "config_entry": entry.entry_id,
                        "back_path": f"/{DASHBOARD_URL_PATH}/cockpit",
                    }
                ],
            },
        ],
    }


def _enable_shown_entities(hass: HomeAssistant, entity_ids: list[str]) -> None:
    """Turn on what the cockpit shows that the integration shipped switched off.

    Per-day counters are off by default; the cockpit needs them. An entity the
    user switched off themselves stays off.
    """
    registry = er.async_get(hass)
    for entity_id in entity_ids:
        entry = registry.async_get(entity_id)
        if entry is not None and entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION:
            registry.async_update_entity(entity_id, disabled_by=None)


async def async_write_dashboard(hass: HomeAssistant, entry: LambdaConfigEntry) -> bool:
    """Write the dashboard. Returns whether a restart is needed for it to appear."""
    config = build_dashboard(hass, entry)
    _enable_shown_entities(hass, list(config["views"][0]["cards"][0]["entities"].values()))

    # A dashboard Lovelace already knows is saved through it, which updates it
    # live — only a new one has to wait for a restart.
    live = _live_dashboard(hass)
    if live is not None:
        await live.async_save(config)
        return False

    await Store(hass, 1, _DASHBOARD_CONFIG_KEY).async_save({"config": config})
    store: Store[dict[str, Any]] = Store(hass, 1, _DASHBOARDS_KEY)
    data = await store.async_load() or {"items": []}
    items: list[dict[str, Any]] = data.setdefault("items", [])
    if not any(item.get("url_path") == DASHBOARD_URL_PATH for item in items):
        items.append(
            {
                "id": _DASHBOARD_ID,
                "url_path": DASHBOARD_URL_PATH,
                "title": "Lambda Cockpit",
                "icon": "mdi:heat-pump",
                "show_in_sidebar": True,
                "require_admin": False,
                "mode": "storage",
            }
        )
        await store.async_save(data)
    return True


def _live_dashboard(hass: HomeAssistant):
    """Lovelace's own object for the cockpit dashboard, if it has one running.

    Lovelace offers no public API for this; anything unexpected means writing
    the storage files instead.
    """
    try:
        from homeassistant.components.lovelace.const import LOVELACE_DATA
        from homeassistant.components.lovelace.dashboard import LovelaceStorage
    except ImportError:
        return None
    data = hass.data.get(LOVELACE_DATA)
    dashboard = getattr(data, "dashboards", {}).get(DASHBOARD_URL_PATH) if data else None
    return dashboard if isinstance(dashboard, LovelaceStorage) else None


def _dashboards_collection(hass: HomeAssistant):
    """Lovelace's own collection of storage dashboards, if it can be reached.

    Lovelace does not keep it anywhere an integration can look it up; the one
    reference outside its setup is the websocket command the frontend deletes a
    dashboard with, which is a method of the collection's websocket wrapper.
    Deleting through the collection is what the frontend does: the panel goes
    at once, its config is deleted, and the list on disk stays in step with
    Lovelace's own copy. Anything unexpected returns None.
    """
    try:
        from homeassistant.components.websocket_api import DOMAIN as WEBSOCKET_DOMAIN

        handler = hass.data[WEBSOCKET_DOMAIN]["lovelace/dashboards/delete"][0]
        collection = inspect.unwrap(handler).__self__.storage_collection
    except (ImportError, KeyError, AttributeError, TypeError):
        return None
    if not hasattr(collection, "async_items") or not hasattr(
        collection, "async_delete_item"
    ):
        return None
    return collection


def _remove_cockpit_settings(hass: HomeAssistant, entry: LambdaConfigEntry) -> None:
    """Drop the settings entities only the cockpit used, rather than orphan them.

    With the option off they are no longer created, and an entity the
    integration no longer provides would linger in the registry as unavailable.
    """
    from .number import COCKPIT_SETTINGS  # the platform, not needed otherwise

    suffixes = tuple(f"_{description.key}_number" for description in COCKPIT_SETTINGS)
    registry = er.async_get(hass)
    for registry_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        if registry_entry.domain == "number" and registry_entry.unique_id.endswith(suffixes):
            registry.async_remove(registry_entry.entity_id)


async def async_remove_dashboard(hass: HomeAssistant) -> None:
    """Remove the cockpit dashboard, live where Lovelace allows it."""
    collection = _dashboards_collection(hass)
    if collection is not None:
        item = next(
            (
                item
                for item in collection.async_items()
                if item.get("url_path") == DASHBOARD_URL_PATH
            ),
            None,
        )
        if item is not None:
            await collection.async_delete_item(item["id"])
            return

    # Not in Lovelace's running list (written, but no restart yet), or the
    # collection could not be reached: take it out of the sidebar and the files.
    try:
        from homeassistant.components import frontend
        from homeassistant.components.lovelace.const import LOVELACE_DATA

        frontend.async_remove_panel(hass, DASHBOARD_URL_PATH, warn_if_unknown=False)
        data = hass.data.get(LOVELACE_DATA)
        if data is not None:
            data.dashboards.pop(DASHBOARD_URL_PATH, None)
    except (ImportError, AttributeError):
        pass
    await Store(hass, 1, _DASHBOARD_CONFIG_KEY).async_remove()
    store: Store[dict[str, Any]] = Store(hass, 1, _DASHBOARDS_KEY)
    data = await store.async_load()
    if data and any(i.get("url_path") == DASHBOARD_URL_PATH for i in data.get("items", [])):
        data["items"] = [
            i for i in data["items"] if i.get("url_path") != DASHBOARD_URL_PATH
        ]
        await store.async_save(data)


async def async_setup_dashboard(hass: HomeAssistant, entry: LambdaConfigEntry) -> None:
    """Write the dashboard if the option asks for it, remove it if it no longer does."""
    await async_register_frontend(hass)
    state_store: Store[dict[str, int]] = Store(hass, _STATE_VERSION, _STATE_KEY)
    state = await state_store.async_load() or {}

    if not entry.options.get(CONF_INSTALL_DASHBOARD, False):
        # Only a dashboard this entry put there is taken away, and only once no
        # other controller still wants it.
        if entry.entry_id not in state:
            return
        del state[entry.entry_id]
        await state_store.async_save(state)
        if state:
            return
        ir.async_delete_issue(hass, DOMAIN, ISSUE_DASHBOARD_RESTART)
        _remove_cockpit_settings(hass, entry)
        try:
            await async_remove_dashboard(hass)
        except Exception:  # noqa: BLE001 - a failed removal must not fail setup
            _LOGGER.exception("Could not remove the Lambda Cockpit dashboard")
        else:
            _LOGGER.info("Lambda Cockpit dashboard removed")
        return

    if state.get(entry.entry_id) == DASHBOARD_LAYOUT_VERSION:
        return

    async def _write() -> None:
        try:
            restart = await async_write_dashboard(hass, entry)
        except Exception:  # noqa: BLE001 - a failed write must not fail setup
            _LOGGER.exception("Could not write the Lambda Cockpit dashboard")
            return
        if restart:
            ir.async_create_issue(
                hass,
                DOMAIN,
                ISSUE_DASHBOARD_RESTART,
                is_fixable=True,
                severity=ir.IssueSeverity.WARNING,
                translation_key=ISSUE_DASHBOARD_RESTART,
            )
            _LOGGER.info("Lambda Cockpit dashboard written; restart to see it")
        state[entry.entry_id] = DASHBOARD_LAYOUT_VERSION
        await state_store.async_save(state)

    # After the platforms have added their entities: the dashboard looks them up.
    entry.async_create_background_task(hass, _write(), f"{DOMAIN} dashboard")


async def async_regenerate_dashboard(hass: HomeAssistant, entry: LambdaConfigEntry) -> None:
    """Write the dashboard again on request, e.g. after deleting it by hand."""
    if await async_write_dashboard(hass, entry):
        ir.async_create_issue(
            hass,
            DOMAIN,
            ISSUE_DASHBOARD_RESTART,
            is_fixable=True,
            severity=ir.IssueSeverity.WARNING,
            translation_key=ISSUE_DASHBOARD_RESTART,
        )
    state_store: Store[dict[str, int]] = Store(hass, _STATE_VERSION, _STATE_KEY)
    state = await state_store.async_load() or {}
    state[entry.entry_id] = DASHBOARD_LAYOUT_VERSION
    await state_store.async_save(state)
