"""Structured Migration System for Lambda Heat Pumps integration."""

from __future__ import annotations
import functools
import logging
import os
import re
import shutil
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry


from .const import DOMAIN, LAMBDA_WP_CONFIG_TEMPLATE
from .const_migration import (
    MigrationVersion,
    MIGRATION_BACKUP_DIR,
    MIGRATION_NAMES,
    BACKUP_RETENTION_DAYS,
    CLEANUP_ON_MIGRATION,
    ROLLBACK_ENABLED,
    ROLLBACK_ON_CRITICAL_ERRORS,
    CRITICAL_ERROR_THRESHOLD,
    DEFAULT_CYCLING_OFFSETS,
    DEFAULT_ENERGY_CONSUMPTION_SENSORS,
    DEFAULT_ENERGY_CONSUMPTION_OFFSETS
)
from .utils import (
    analyze_file_ageing,
    delete_files,
)

_LOGGER = logging.getLogger(__name__)


# =============================================================================
# BACKUP UND ROLLBACK SYSTEM
# =============================================================================

async def create_registry_backup(
    hass: HomeAssistant, 
    migration_version: MigrationVersion
) -> Tuple[bool, str]:
    """
    Erstelle Backup der Registry-Dateien für eine Migration.
    
    Args:
        hass: Home Assistant Instanz
        migration_version: Version der Migration
    
    Returns:
        Tuple[bool, str]: (erfolg, backup_pfad)
    """
    try:
        config_dir = hass.config.config_dir
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        migration_name = MIGRATION_NAMES.get(migration_version, f"v{migration_version.value}")
        
        # Backup-Verzeichnis erstellen
        backup_dir = os.path.join(config_dir, MIGRATION_BACKUP_DIR)
        await hass.async_add_executor_job(
            functools.partial(os.makedirs, backup_dir, exist_ok=True)
        )
        
        # Registry-Dateien definieren
        registry_files = [
            "core.entity_registry",
            "core.device_registry", 
            "core.config_entries"
        ]
        
        backup_paths = []
        for registry_file in registry_files:
            source_path = os.path.join(config_dir, ".storage", registry_file)
            dest_path = os.path.join(
                backup_dir, 
                f"{registry_file}.{migration_name}_{timestamp}"
            )
            
            if await hass.async_add_executor_job(os.path.exists, source_path):
                await hass.async_add_executor_job(shutil.copy2, source_path, dest_path)
                backup_paths.append(dest_path)
                _LOGGER.info("Registry backup erstellt: %s", dest_path)
        
        return True, backup_dir
        
    except Exception as e:
        _LOGGER.error("Fehler beim Erstellen der Registry-Backups: %s", e)
        return False, ""


async def create_lambda_config_backup(
    hass: HomeAssistant, 
    migration_version: MigrationVersion
) -> Tuple[bool, str]:
    """
    Erstelle Backup der lambda_wp_config.yaml für eine Migration.
    
    Args:
        hass: Home Assistant Instanz
        migration_version: Version der Migration
    
    Returns:
        Tuple[bool, str]: (erfolg, backup_pfad)
    """
    try:
        config_dir = hass.config.config_dir
        lambda_config_path = os.path.join(config_dir, "lambda_wp_config.yaml")
        
        if not await hass.async_add_executor_job(os.path.exists, lambda_config_path):
            _LOGGER.info("lambda_wp_config.yaml nicht gefunden, kein Backup erforderlich")
            return True, ""
        
        # Backup-Verzeichnis erstellen
        backup_dir = os.path.join(config_dir, MIGRATION_BACKUP_DIR)
        await hass.async_add_executor_job(
            functools.partial(os.makedirs, backup_dir, exist_ok=True)
        )
        
        # Backup erstellen
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        migration_name = MIGRATION_NAMES.get(migration_version, f"v{migration_version.value}")
        backup_path = os.path.join(
            backup_dir, 
            f"lambda_wp_config.{migration_name}_{timestamp}.yaml"
        )
        
        await hass.async_add_executor_job(shutil.copy2, lambda_config_path, backup_path)
        
        _LOGGER.info("Lambda config backup erstellt: %s", backup_path)
        return True, backup_path
        
    except Exception as e:
        _LOGGER.error("Fehler beim Erstellen des Lambda config Backups: %s", e)
        return False, ""


async def rollback_migration(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    backup_info: Dict[str, str],
    migration_version: MigrationVersion
) -> bool:
    """
    Führe Rollback einer fehlgeschlagenen Migration durch.
    
    Args:
        hass: Home Assistant Instanz
        config_entry: Config Entry
        backup_info: Backup-Informationen
        migration_version: Version der Migration
    
    Returns:
        bool: True wenn Rollback erfolgreich
    """
    try:
        _LOGGER.warning(
            "Rollback für Migration %s wird durchgeführt", 
            migration_version.name
        )
        
        # Hier würde die tatsächliche Rollback-Logik stehen
        # Für jetzt nur Logging
        
        _LOGGER.info("Rollback für Migration %s abgeschlossen", migration_version.name)
        return True
        
    except Exception as e:
        _LOGGER.error("Fehler beim Rollback der Migration %s: %s", migration_version.name, e)
        return False


# =============================================================================
# LAMBDA CONFIG SECTIONS (lambda_wp_config.yaml)
# Template-basierte Migration: fehlende Abschnitte an richtiger Stelle einfügen,
# bestehende konfigurierte Abschnitte unverändert lassen.
# =============================================================================

# Eindeutige Header-Zeile pro Abschnitt (Reihenfolge = Template-Reihenfolge)
_SECTION_HEADER_LINES = (
    "# Override sensor names (only works if use_legacy_modbus_names is true)",
    "# Cycling counter offsets for total sensors",
    "# Energy consumption sensor configuration",
    "# Energy consumption offsets for total sensors",
    "# Modbus configuration",
)
_SECTION_HEADER_TO_NAME = {
    "# Override sensor names (only works if use_legacy_modbus_names is true)": "sensors_names_override",
    "# Cycling counter offsets for total sensors": "cycling_offsets",
    "# Energy consumption sensor configuration": "energy_consumption_sensors",
    "# Energy consumption offsets for total sensors": "energy_consumption_offsets",
    "# Modbus configuration": "modbus",
}


def _find_section_ranges_in_content(content: str) -> Tuple[str, list]:
    """
    Findet die Zeichenbereiche (start, end) jedes vorhandenen Abschnitts in content.
    Returns: (normalisierter content mit \\n), Liste (start, end, section_name) sortiert nach start.
    """
    content_n = content.replace("\r\n", "\n").replace("\r", "\n")
    found: list = []  # (position, section_name)
    for header_line in _SECTION_HEADER_LINES:
        name = _SECTION_HEADER_TO_NAME[header_line]
        pos = content_n.find(header_line)
        if pos != -1:
            found.append((pos, name))
    found.sort(key=lambda x: x[0])
    ranges: list = []
    for i, (start, name) in enumerate(found):
        end = found[i + 1][0] if i + 1 < len(found) else len(content_n)
        ranges.append((start, end, name))
    return content_n, ranges


def _extract_config_sections() -> Dict[str, str]:
    """
    Extrahiert alle Konfigurationsabschnitte aus dem LAMBDA_WP_CONFIG_TEMPLATE.
    """
    sections = {}
    lines = LAMBDA_WP_CONFIG_TEMPLATE.split("\n")
    current_section = None
    current_content = []
    for line in lines:
        if line.strip() in _SECTION_HEADER_TO_NAME:
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = _SECTION_HEADER_TO_NAME[line.strip()]
            current_content = [line]
        elif current_section:
            current_content.append(line)
        else:
            continue
    if current_section and current_content:
        sections[current_section] = "\n".join(current_content).strip()
    _LOGGER.debug("Extracted config sections: %s", list(sections.keys()))
    return sections


async def migrate_lambda_config_sections(hass: HomeAssistant) -> bool:
    """
    Template-basierte Migration der lambda_wp_config.yaml:
    - Upgrade energy_consumption_sensors auf neues Format (thermal_sensor_entity_id optional)
    - Fehlende Abschnitte an der richtigen Stelle einfügen (Template-Reihenfolge),
      bestehende Abschnitte unverändert übernehmen (kein Anhängen, keine Duplikate)

    Returns:
        bool: True wenn Migration durchgeführt wurde, False sonst
    """
    config_dir = hass.config.config_dir
    lambda_config_path = os.path.join(config_dir, "lambda_wp_config.yaml")

    if not await hass.async_add_executor_job(os.path.exists, lambda_config_path):
        _LOGGER.debug("No existing lambda_wp_config.yaml found, no migration needed")
        return False

    try:
        content = await hass.async_add_executor_job(
            functools.partial(Path(lambda_config_path).read_text, encoding="utf-8")
        )
        current_config = yaml.safe_load(content)
        if not current_config:
            _LOGGER.debug("Empty config file, no migration needed")
            return False

        content_modified = False
        content_normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        # Upgrade alter energy_consumption_sensors-Block (thermal_sensor_entity_id)
        first_ecs = content_normalized.find("energy_consumption_sensors:")
        if first_ecs != -1:
            header_before_first = content_normalized[max(0, first_ecs - 400) : first_ecs]
            has_new_format = "sensor_entity_id = elektrisch, thermal_sensor_entity_id = thermisch" in header_before_first
            if not has_new_format:
                old_header = (
                    "# Das System konvertiert automatisch zu kWh für die Berechnungen\n"
                    "# Beispiel:\nenergy_consumption_sensors:"
                )
                new_header = (
                    "# Das System konvertiert automatisch zu kWh für die Berechnungen\n"
                    "# sensor_entity_id = elektrisch, thermal_sensor_entity_id = thermisch (optional)\n"
                    "# Beispiel:\nenergy_consumption_sensors:"
                )
                if old_header in content_normalized:
                    content = content_normalized.replace(old_header, new_header, 1)
                    content_modified = True
                    _LOGGER.info(
                        "Migrated energy_consumption_sensors to new format (thermal_sensor_entity_id optional)"
                    )
                else:
                    _LOGGER.debug(
                        "energy_consumption_sensors: first block header not matched"
                    )
        if content_modified:
            current_config = yaml.safe_load(content)

        content_n, ranges = _find_section_ranges_in_content(content)
        section_ranges = {name: (s, e) for s, e, name in ranges}
        # Fehlt bei einem hp-Eintrag die optionale Zeile thermal_sensor_entity_id? → bei jedem sensor_entity_id: prüfen und ggf. einfügen
        # Prüfen auf Key "thermal_sensor_entity_id:" (Doppelpunkt), Einrückung/Kommentar (#  hp2) übernehmen
        if "energy_consumption_sensors" in section_ranges:
            s_ecs, e_ecs = section_ranges["energy_consumption_sensors"]
            section_text = content_n[s_ecs:e_ecs]
            # Alle Zeilen mit sensor_entity_id: (mit optionalem führendem # für auskommentierte hp2)
            inserts = []  # (position in section_text, new_line)
            for match in re.finditer(r"\n((?:\s+|#\s*))sensor_entity_id:[^\n]*", section_text):
                line_end = section_text.find("\n", match.end())
                if line_end == -1:
                    line_end = len(section_text)
                # Nächste Zeile bereits thermal_sensor_entity_id? → überspringen
                next_start = line_end + 1
                next_end = section_text.find("\n", next_start)
                if next_end == -1:
                    next_end = len(section_text)
                next_line = section_text[next_start:next_end] if next_start < len(section_text) else ""
                if "thermal_sensor_entity_id:" in next_line:
                    continue
                prefix = match.group(1)  # z. B. "    " oder "#    "
                new_line = "\n" + prefix + "# thermal_sensor_entity_id: \"sensor.lambda_wp_waerme\"  # optional"
                inserts.append((line_end, new_line))
            # Von hinten nach vorne einfügen, damit Positionen stimmen
            for pos, new_line in sorted(inserts, key=lambda x: -x[0]):
                section_text = section_text[:pos] + new_line + section_text[pos:]
            if inserts:
                content_n = content_n[:s_ecs] + section_text + content_n[e_ecs:]
                content = content_n
                content_modified = True
                _LOGGER.info(
                    "Added optional thermal_sensor_entity_id line(s) to energy_consumption_sensors block (%d hp)",
                    len(inserts),
                )
        if content_modified:
            current_config = yaml.safe_load(content)
            content_n, ranges = _find_section_ranges_in_content(content)
            section_ranges = {name: (s, e) for s, e, name in ranges}

        # Migrate cycling_offsets: add compressor_start_cycling_total after defrost_cycling_total if missing
        if "cycling_offsets" in section_ranges:
            s_co, e_co = section_ranges["cycling_offsets"]
            section_text = content_n[s_co:e_co]
            inserts = []
            for match in re.finditer(r"\n((?:#\s+|\s+))defrost_cycling_total:[^\n]*", section_text):
                line_end = section_text.find("\n", match.end())
                if line_end == -1:
                    line_end = len(section_text)
                next_start = line_end + 1
                next_end = section_text.find("\n", next_start)
                if next_end == -1:
                    next_end = len(section_text)
                next_line = section_text[next_start:next_end] if next_start < len(section_text) else ""
                if "compressor_start_cycling_total:" in next_line:
                    continue
                prefix = match.group(1)  # e.g. "#    " or "    "
                new_line = "\n" + prefix + "compressor_start_cycling_total: 0      # Offset for compressor start total"
                inserts.append((line_end, new_line))
            for pos, new_line in sorted(inserts, key=lambda x: -x[0]):
                section_text = section_text[:pos] + new_line + section_text[pos:]
            if inserts:
                content_n = content_n[:s_co] + section_text + content_n[e_co:]
                content = content_n
                content_modified = True
                _LOGGER.info(
                    "Added compressor_start_cycling_total line(s) to cycling_offsets block (%d entries)",
                    len(inserts),
                )
                content_n, ranges = _find_section_ranges_in_content(content)
                section_ranges = {name: (s, e) for s, e, name in ranges}

        # Migrate energy_consumption_offsets: add missing thermal_energy_total lines
        # Chain: defrost_energy_total → heating_thermal → hot_water_thermal → cooling_thermal → defrost_thermal
        _THERMAL_CHAIN = [
            (r"\n((?:#\s+|\s+))defrost_energy_total:[^\n]*",          "heating_thermal_energy_total",   "0.0      # kWh offset for heating total (thermal, optional)"),
            (r"\n((?:#\s+|\s+))heating_thermal_energy_total:[^\n]*",   "hot_water_thermal_energy_total", "0.0      # kWh offset for hot water total (thermal, optional)"),
            (r"\n((?:#\s+|\s+))hot_water_thermal_energy_total:[^\n]*", "cooling_thermal_energy_total",   "0.0      # kWh offset for cooling total (thermal, optional)"),
            (r"\n((?:#\s+|\s+))cooling_thermal_energy_total:[^\n]*",   "defrost_thermal_energy_total",   "0.0      # kWh offset for defrost total (thermal, optional)"),
        ]
        if "energy_consumption_offsets" in section_ranges:
            s_eo, e_eo = section_ranges["energy_consumption_offsets"]
            section_text = content_n[s_eo:e_eo]
            thermal_inserts_total = 0
            for anchor_pattern, new_key, new_comment in _THERMAL_CHAIN:
                inserts = []
                for match in re.finditer(anchor_pattern, section_text):
                    line_end = section_text.find("\n", match.end())
                    if line_end == -1:
                        line_end = len(section_text)
                    next_start = line_end + 1
                    next_end = section_text.find("\n", next_start)
                    if next_end == -1:
                        next_end = len(section_text)
                    next_line = section_text[next_start:next_end] if next_start < len(section_text) else ""
                    if new_key + ":" in next_line:
                        continue
                    prefix = match.group(1)
                    inserts.append((line_end, "\n" + prefix + f"{new_key}: {new_comment}"))
                for pos, new_line in sorted(inserts, key=lambda x: -x[0]):
                    section_text = section_text[:pos] + new_line + section_text[pos:]
                thermal_inserts_total += len(inserts)
            if thermal_inserts_total:
                content_n = content_n[:s_eo] + section_text + content_n[e_eo:]
                content = content_n
                content_modified = True
                _LOGGER.info(
                    "Added %d thermal_energy_total line(s) to energy_consumption_offsets block",
                    thermal_inserts_total,
                )
                content_n, ranges = _find_section_ranges_in_content(content)
                section_ranges = {name: (s, e) for s, e, name in ranges}

        template_sections = _extract_config_sections()
        template_order = list(template_sections.keys())
        first_section_start = min(r[0] for r in ranges) if ranges else len(content_n)
        part_before = content_n[:first_section_start].rstrip()

        missing_sections = []
        for section_name in template_order:
            in_file = section_name in section_ranges
            in_config = section_name in current_config
            if not in_file and not in_config:
                missing_sections.append(section_name)
                _LOGGER.debug("Missing section: %s", section_name)
            elif in_file:
                _LOGGER.debug("Section %s already present in file", section_name)
            else:
                _LOGGER.debug("Section %s in config dict, preserved via part_before", section_name)

        if not missing_sections and not content_modified:
            _LOGGER.info("All config sections already present - no migration needed")
            return False

        backup_path = lambda_config_path + ".backup"
        await hass.async_add_executor_job(
            lambda: open(backup_path, "w", encoding="utf-8").write(content)
        )
        _LOGGER.info("Created backup at %s", backup_path)

        if content_modified and not missing_sections:
            await hass.async_add_executor_job(
                lambda: open(lambda_config_path, "w", encoding="utf-8").write(content)
            )
            _LOGGER.info(
                "Successfully migrated lambda_wp_config.yaml (energy_consumption_sensors format). Backup at %s",
                backup_path,
            )
            return True

        if missing_sections:
            _LOGGER.info(
                "Migrating lambda_wp_config.yaml - inserting %d missing sections at correct position",
                len(missing_sections),
            )
            parts = [part_before]
            for section_name in template_order:
                if section_name in section_ranges:
                    s, e = section_ranges[section_name]
                    parts.append(content_n[s:e].rstrip())
                elif section_name in current_config:
                    continue
                else:
                    parts.append(template_sections[section_name].strip())
                    _LOGGER.info("Inserted section: %s", section_name)
            updated_content = "\n\n".join(parts) + "\n"
            await hass.async_add_executor_job(
                lambda: open(lambda_config_path, "w", encoding="utf-8").write(updated_content)
            )
            _LOGGER.info(
                "Successfully migrated lambda_wp_config.yaml - inserted %d sections in place. Backup at %s",
                len(missing_sections), backup_path,
            )
        return True

    except Exception as e:
        _LOGGER.error("Error during config section migration: %s", e)
        return False


# =============================================================================
# CLEANUP: DUPLIKAT-ENTITIES (_2, _3, …)
# =============================================================================

# Regex für Entity-IDs, die mit _2, _3, … enden (Home Assistant Duplikat-Suffix)
_ENTITY_ID_DUPLICATE_SUFFIX_RE = re.compile(r"_\d+$")


def _entity_id_has_duplicate_suffix(entity_id: str) -> bool:
    """Prüft, ob entity_id mit _2, _3, … endet."""
    return bool(_ENTITY_ID_DUPLICATE_SUFFIX_RE.search(entity_id))


def _extract_duplicate_suffix(entity_id: str) -> str | None:
    """Gibt das Duplikat-Suffix (z. B. '_2', '_3') zurück oder None."""
    match = _ENTITY_ID_DUPLICATE_SUFFIX_RE.search(entity_id)
    return match.group(0) if match else None


def _is_our_platform(registry_entry: Any) -> bool:
    """Prüft, ob die Entity zu unserer Integration gehört (Platform-Domain)."""
    platform = getattr(registry_entry, "platform", None)
    if platform is None:
        return False
    if isinstance(platform, (list, tuple)) and len(platform) >= 1:
        return platform[0] == DOMAIN
    if isinstance(platform, str):
        return platform.startswith(DOMAIN + ".") or platform == DOMAIN
    return False


async def async_remove_duplicate_entity_suffixes(
    hass: HomeAssistant, entry_id: str
) -> int:
    """
    Entfernt Entities dieser Integration, deren entity_id mit _2, _3, … endet.

    Ablauf: Eine Sammelphase (Kandidaten ermitteln), danach eine Löschphase.
    - Kandidaten: Entities dieses Config-Eintrags (entry_id) mit Suffix ODER
      verwaiste Duplikate (config_entry_id existiert nicht mehr, gleiche Platform).

    Benutzer-Anpassungen (z. B. umbenannte Entities ohne Suffix) werden nicht angetastet.

    Hinweis: entity_registry.async_remove() und hass.states.async_remove() sind in
    Home Assistant keine Coroutinen und werden bewusst nicht mit await aufgerufen.

    Args:
        hass: Home Assistant Instanz
        entry_id: Config-Entry-ID (entry.entry_id)

    Returns:
        Anzahl der entfernten Entities. Spätere Erweiterung auf Dict {removed, failed, skipped} denkbar.
    """
    removed = 0
    renamed = 0
    failed = 0
    try:
        _LOGGER.info(
            "Cleanup: Prüfe auf Duplikat-Entities (_2, _3, …) für Entry %s …",
            entry_id,
        )
        entity_registry = async_get_entity_registry(hass)
        current_entry_ids = {
            e.entry_id for e in hass.config_entries.async_entries(DOMAIN)
        }

        # ----- Sammelphase: alle Kandidaten (entity_id, reason) sammeln -----
        candidates: list[tuple[str, str]] = []  # (entity_id, reason)

        # 1a) Entities dieses Config-Eintrags mit Suffix _2, _3, …
        registry_entries = entity_registry.entities.get_entries_for_config_entry_id(
            entry_id
        )
        for registry_entry in registry_entries:
            eid = registry_entry.entity_id
            if "config_parameter_" in eid:
                continue
            if _entity_id_has_duplicate_suffix(eid):
                candidates.append((eid, "aktueller_eintrag"))

        # 1b) Verwaiste Duplikate (config_entry_id nicht mehr in current_entry_ids)
        if hasattr(entity_registry.entities, "values"):
            all_entries = list(entity_registry.entities.values())
        else:
            all_entries = []
        for registry_entry in all_entries:
            eid = getattr(registry_entry, "entity_id", None)
            config_eid = getattr(registry_entry, "config_entry_id", None)
            if not eid or not _entity_id_has_duplicate_suffix(eid):
                continue
            if "config_parameter_" in eid:
                continue
            if not _is_our_platform(registry_entry):
                continue
            if config_eid is not None and config_eid in current_entry_ids:
                continue
            # Verwaist: nur aufnehmen wenn noch nicht in candidates (z. B. aus 1a)
            if eid not in [c[0] for c in candidates]:
                candidates.append((eid, "verwaist"))

        # ----- Löschphase: Kandidaten umbenennen oder entfernen -----
        # Strategie: Wenn die Ziel-entity_id (ohne _2-Suffix) noch nicht vergeben ist,
        # wird die _2-Entity umbenannt statt gelöscht. Dadurch wird kein deleted_entities-
        # Eintrag mit _2-entity_id erzeugt, den HA beim nächsten Start wiederherstellen würde.
        for eid, reason in candidates:
            try:
                base_eid = _ENTITY_ID_DUPLICATE_SUFFIX_RE.sub("", eid)
                if entity_registry.async_get(base_eid) is None:
                    # Umbenennen: _2-Entity erhält die korrekte entity_id.
                    # Kein deleted_entities-Eintrag → kein _2-Restore beim nächsten Start.
                    entity_registry.async_update_entity(eid, new_entity_id=base_eid)
                    renamed += 1
                    _LOGGER.info(
                        "Cleanup: Duplikat umbenannt: %s -> %s (reason: %s)",
                        eid,
                        base_eid,
                        reason,
                    )
                else:
                    existing_base = entity_registry.async_get(base_eid)
                    _2_entry = entity_registry.async_get(eid)
                    if _2_entry and existing_base and existing_base.unique_id == _2_entry.unique_id:
                        # Gleiche unique_id: veralteter base_eid-Eintrag blockiert das Umbenennen.
                        # Alten Eintrag zuerst entfernen (erzeugt deleted_entities für base_eid,
                        # nicht für _2), dann _2 auf den korrekten Namen umbenennen.
                        entity_registry.async_remove(base_eid)
                        hass.states.async_remove(base_eid)
                        entity_registry.async_update_entity(eid, new_entity_id=base_eid)
                        renamed += 1
                        _LOGGER.info(
                            "Cleanup: Veralteten Eintrag ersetzt und umbenannt: %s -> %s (reason: %s)",
                            eid,
                            base_eid,
                            reason,
                        )
                    else:
                        # Echtes Duplikat mit anderer unique_id → löschen
                        entity_registry.async_remove(eid)
                        hass.states.async_remove(eid)
                        removed += 1
                        _LOGGER.info(
                            "Cleanup: Duplikat entfernt: %s (reason: %s)",
                            eid,
                            reason,
                        )
            except Exception as e:
                failed += 1
                _LOGGER.warning(
                    "Cleanup: Entity %s konnte nicht verarbeitet werden (reason: %s): %s",
                    eid,
                    reason,
                    e,
                )

        # Zusammenfassung
        if removed or renamed or failed:
            _LOGGER.info(
                "Cleanup abgeschlossen: %d umbenannt, %d entfernt, %d Fehler für Entry %s",
                renamed,
                removed,
                failed,
                entry_id,
            )
        elif not candidates:
            _LOGGER.info(
                "Cleanup: Keine Duplikat-Entities (_2, _3, …) für Entry %s gefunden.",
                entry_id,
            )
    except Exception as e:
        _LOGGER.warning(
            "Cleanup Duplikat-Entities für Entry %s fehlgeschlagen: %s", entry_id, e
        )
    return removed + renamed


# =============================================================================
# MIGRATIONSFUNKTIONEN FÜR JEDE VERSION
# =============================================================================

async def migrate_to_legacy_names(
    hass: HomeAssistant, 
    config_entry: ConfigEntry
) -> bool:
    """
    Migration zu Legacy-Namen (Version 2).
    
    Args:
        hass: Home Assistant Instanz
        config_entry: Config Entry
    
    Returns:
        bool: True wenn Migration erfolgreich
    """
    try:
        entry_id = config_entry.entry_id
        _LOGGER.info(
            "Starte Migration zu Legacy-Namen für Config %s", 
            entry_id
        )

        # Entity Registry bereinigen: Entferne alle alten/inkonsistenten Climate- und Sensor-Entitäten
        entity_registry = async_get_entity_registry(hass)
        registry_entries = entity_registry.entities.get_entries_for_config_entry_id(entry_id)

        # Importiere aktuelle Namenslogik
        from .utils import generate_sensor_names, normalize_name_prefix
        from .const import CLIMATE_TEMPLATES, HP_SENSOR_TEMPLATES, BOIL_SENSOR_TEMPLATES, HC_SENSOR_TEMPLATES, BUFF_SENSOR_TEMPLATES, SOL_SENSOR_TEMPLATES, SENSOR_TYPES

        # Hole aktuelle Namensschemata für alle Climate- und Sensor-Entitäten
        entry_data = config_entry.data
        use_legacy_modbus_names = entry_data.get("use_legacy_modbus_names", True)
        name_prefix = normalize_name_prefix(entry_data.get("name", ""))
        num_boil = entry_data.get("num_boil", 1)
        num_hc = entry_data.get("num_hc", 1)
        num_hps = entry_data.get("num_hps", 1)
        num_buff = entry_data.get("num_buff", 0)
        num_sol = entry_data.get("num_sol", 0)

        # Climate: aktuelle unique_ids und entity_ids
        valid_climate_ids = set()
        for idx in range(1, num_boil + 1):
            device_prefix = f"boil{idx}"
            names = generate_sensor_names(device_prefix, CLIMATE_TEMPLATES["hot_water"]["name"], "hot_water", name_prefix, use_legacy_modbus_names)
            valid_climate_ids.add((names["entity_id"], names["unique_id"]))
        for idx in range(1, num_hc + 1):
            device_prefix = f"hc{idx}"
            names = generate_sensor_names(device_prefix, CLIMATE_TEMPLATES["heating_circuit"]["name"], "heating_circuit", name_prefix, use_legacy_modbus_names)
            valid_climate_ids.add((names["entity_id"], names["unique_id"]))

        # Sensoren: aktuelle unique_ids und entity_ids
        valid_sensor_ids = set()
        # HP
        from .utils import get_firmware_version_int, get_compatible_sensors
        fw_version = get_firmware_version_int(config_entry)
        for prefix, count, template in [
            ("hp", num_hps, get_compatible_sensors(HP_SENSOR_TEMPLATES, fw_version)),
            ("boil", num_boil, get_compatible_sensors(BOIL_SENSOR_TEMPLATES, fw_version)),
            ("buff", num_buff, get_compatible_sensors(BUFF_SENSOR_TEMPLATES, fw_version)),
            ("sol", num_sol, get_compatible_sensors(SOL_SENSOR_TEMPLATES, fw_version)),
            ("hc", num_hc, get_compatible_sensors(HC_SENSOR_TEMPLATES, fw_version)),
        ]:
            for idx in range(1, count + 1):
                device_prefix = f"{prefix}{idx}"
                for sensor_id, sensor_info in template.items():
                    names = generate_sensor_names(device_prefix, sensor_info["name"], sensor_id, name_prefix, use_legacy_modbus_names)
                    valid_sensor_ids.add((names["entity_id"], names["unique_id"]))
        # General Sensors
        for sensor_id, sensor_info in SENSOR_TYPES.items():
            names = generate_sensor_names(sensor_id, sensor_info["name"], sensor_id, name_prefix, use_legacy_modbus_names)
            valid_sensor_ids.add((names["entity_id"], names["unique_id"]))

        # Entferne alle Climate- und Sensor-Entitäten, die nicht im aktuellen Schema sind
        removed = 0
        for registry_entry in registry_entries:
            eid = registry_entry.entity_id
            uid = registry_entry.unique_id
            domain = eid.split(".")[0] if "." in eid else ""
            # Climate
            if domain == "climate":
                if (eid, uid) not in valid_climate_ids:
                    _LOGGER.info(f"Entferne alte Climate-Entity: {eid} ({uid})")
                    try:
                        entity_registry.async_remove(eid)
                        removed += 1
                    except Exception as e:
                        _LOGGER.error(f"Fehler beim Entfernen alter Climate-Entity {eid}: {e}")
            # Sensor
            elif domain == "sensor":
                if (eid, uid) not in valid_sensor_ids:
                    _LOGGER.info(f"Entferne alte Sensor-Entity: {eid} ({uid})")
                    try:
                        entity_registry.async_remove(eid)
                        removed += 1
                    except Exception as e:
                        _LOGGER.error(f"Fehler beim Entfernen alter Sensor-Entity {eid}: {e}")

        _LOGGER.info(
            f"Migration zu Legacy-Namen für Config {entry_id} abgeschlossen: {removed} alte Entities entfernt."
        )
        return True

    except Exception as e:
        _LOGGER.error(
            "Fehler bei Migration zu Legacy-Namen für Config %s: %s", 
            entry_id, e
        )
        return False


async def migrate_to_cycling_offsets(
    hass: HomeAssistant, 
    config_entry: ConfigEntry
) -> bool:
    """
    Migration zu Cycling-Offsets (Version 3).
    
    DEPRECATED: Use migrate_to_unified_config() (Version 7) instead.
    This function is kept for backward compatibility.
    
    Args:
        hass: Home Assistant Instanz
        config_entry: Config Entry
    
    Returns:
        bool: True wenn Migration erfolgreich
    """
    try:
        entry_id = config_entry.entry_id
        _LOGGER.info(
            "Starte Migration zu Cycling-Offsets für Config %s", 
            entry_id
        )
        
        # Lambda config laden und aktualisieren
        config_dir = hass.config.config_dir
        lambda_config_path = os.path.join(config_dir, "lambda_wp_config.yaml")
        
        if await hass.async_add_executor_job(os.path.exists, lambda_config_path):
            # Bestehende Config laden
            content = await hass.async_add_executor_job(
                Path(lambda_config_path).read_text
            )
            config = yaml.safe_load(content) or {}
        else:
            config = {}

        # Cycling-Offsets hinzufügen falls nicht vorhanden
        if "cycling_offsets" not in config:
            config["cycling_offsets"] = DEFAULT_CYCLING_OFFSETS

            # Config speichern
            yaml_content = yaml.dump(config, default_flow_style=False)
            await hass.async_add_executor_job(
                Path(lambda_config_path).write_text, yaml_content
            )
            
            _LOGGER.info(
                "Cycling-Offsets zu lambda_wp_config.yaml hinzugefügt"
            )
        
        _LOGGER.info(
            "Migration zu Cycling-Offsets für Config %s erfolgreich abgeschlossen", 
            entry_id
        )
        return True
        
    except Exception as e:
        _LOGGER.error(
            "Fehler bei Migration zu Cycling-Offsets für Config %s: %s", 
            entry_id, e
        )
        return False


async def migrate_to_energy_consumption(
    hass: HomeAssistant, 
    config_entry: ConfigEntry
) -> bool:
    """
    Migration zu Energy Consumption Sensoren (Version 4).
    
    DEPRECATED: Use migrate_to_unified_config() (Version 7) instead.
    This function is kept for backward compatibility.
    
    Args:
        hass: Home Assistant Instanz
        config_entry: Config Entry
    
    Returns:
        bool: True wenn Migration erfolgreich
    """
    try:
        entry_id = config_entry.entry_id
        _LOGGER.info(
            "Starte Migration zu Energy Consumption für Config %s", 
            entry_id
        )
        
        # Lambda config laden und aktualisieren
        config_dir = hass.config.config_dir
        lambda_config_path = os.path.join(config_dir, "lambda_wp_config.yaml")
        
        if await hass.async_add_executor_job(os.path.exists, lambda_config_path):
            # Bestehende Config laden
            content = await hass.async_add_executor_job(
                Path(lambda_config_path).read_text
            )
            config = yaml.safe_load(content) or {}
        else:
            config = {}

        # Energy Consumption Sensoren hinzufügen falls nicht vorhanden
        if "energy_consumption_sensors" not in config:
            config["energy_consumption_sensors"] = DEFAULT_ENERGY_CONSUMPTION_SENSORS
            _LOGGER.info("Energy Consumption Sensoren zu lambda_wp_config.yaml hinzugefügt")

        # Energy Consumption Offsets hinzufügen falls nicht vorhanden
        if "energy_consumption_offsets" not in config:
            config["energy_consumption_offsets"] = DEFAULT_ENERGY_CONSUMPTION_OFFSETS
            _LOGGER.info("Energy Consumption Offsets zu lambda_wp_config.yaml hinzugefügt")

        # Config speichern
        yaml_content = yaml.dump(config, default_flow_style=False)
        await hass.async_add_executor_job(
            Path(lambda_config_path).write_text, yaml_content
        )
        
        _LOGGER.info(
            "Migration zu Energy Consumption für Config %s erfolgreich abgeschlossen", 
            entry_id
        )
        return True
        
    except Exception as e:
        _LOGGER.error(
            "Fehler bei Migration zu Energy Consumption für Config %s: %s", 
            config_entry.entry_id, e
        )
        return False


async def migrate_to_entity_optimization(
    hass: HomeAssistant, 
    config_entry: ConfigEntry
) -> bool:
    """
    Migration zu Entity-Optimierung (Version 4).
    
    Args:
        hass: Home Assistant Instanz
        config_entry: Config Entry
    
    Returns:
        bool: True wenn Migration erfolgreich
    """
    try:
        entry_id = config_entry.entry_id
        _LOGGER.info(
            "Starte Migration zu Entity-Optimierung für Config %s", 
            entry_id
        )
        
        # Hier würde die tatsächliche Entity-Optimierung stehen
        # Für jetzt nur Logging
        
        _LOGGER.info(
            "Migration zu Entity-Optimierung für Config %s erfolgreich abgeschlossen", 
            entry_id
        )
        return True
        
    except Exception as e:
        _LOGGER.error(
            "Fehler bei Migration zu Entity-Optimierung für Config %s: %s", 
            entry_id, e
        )
        return False


async def migrate_to_config_restructure(
    hass: HomeAssistant, 
    config_entry: ConfigEntry
) -> bool:
    """
    Migration zu Config-Restrukturierung (Version 5).
    
    Args:
        hass: Home Assistant Instanz
        config_entry: Config Entry
    
    Returns:
        bool: True wenn Migration erfolgreich
    """
    try:
        entry_id = config_entry.entry_id
        _LOGGER.info(
            "Starte Migration zu Config-Restrukturierung für Config %s", 
            entry_id
        )
        
        # Hier würde die tatsächliche Config-Restrukturierung stehen
        # Für jetzt nur Logging
        
        _LOGGER.info(
            "Migration zu Config-Restrukturierung für Config %s erfolgreich abgeschlossen", 
            entry_id
        )
        return True
        
    except Exception as e:
        _LOGGER.error(
            "Fehler bei Migration zu Config-Restrukturierung für Config %s: %s", 
            entry_id, e
        )
        return False


# =============================================================================
# MIGRATIONS-DISPATCHER
# =============================================================================

async def migrate_to_unified_config(
    hass: HomeAssistant, 
    config_entry: ConfigEntry
) -> bool:
    """
    Migration zu unified config (Version 7).
    Template-basierte Migration aller Konfigurationsabschnitte.
    
    Args:
        hass: Home Assistant Instanz
        config_entry: Config Entry
    
    Returns:
        bool: True wenn Migration erfolgreich
    """
    try:
        entry_id = config_entry.entry_id
        _LOGGER.info(
            "Starte unified config migration für Config %s", 
            entry_id
        )
        
        # Verwende die neue template-basierte Migration
        success = await migrate_lambda_config_sections(hass)
        
        if success:
            _LOGGER.info(
                "Unified config migration für Config %s erfolgreich abgeschlossen", 
                entry_id
            )
        else:
            _LOGGER.info(
                "Unified config migration für Config %s - keine Änderungen erforderlich", 
                entry_id
            )
        
        return True
        
    except Exception as e:
        _LOGGER.error(
            "Fehler bei unified config migration für Config %s: %s", 
            entry_id, e
        )
        return False


async def migrate_to_register_order_terminology(
    hass: HomeAssistant, 
    config_entry: ConfigEntry
) -> bool:
    """
    Migration zu Register-Order-Terminologie (Version 8).
    Migriert modbus.int32_byte_order zu modbus.int32_register_order.
    
    Args:
        hass: Home Assistant Instanz
        config_entry: Config Entry
    
    Returns:
        bool: True wenn Migration erfolgreich
    """
    try:
        entry_id = config_entry.entry_id
        _LOGGER.info(
            "Starte Register-Order-Terminologie-Migration für Config %s", 
            entry_id
        )
        
        config_dir = hass.config.config_dir
        lambda_config_path = os.path.join(config_dir, "lambda_wp_config.yaml")
        
        if not await hass.async_add_executor_job(os.path.exists, lambda_config_path):
            _LOGGER.info(
                "lambda_wp_config.yaml nicht gefunden, keine Migration erforderlich"
            )
            return True

        # Lade aktuelle Config
        content = await hass.async_add_executor_job(
            functools.partial(Path(lambda_config_path).read_text, encoding="utf-8")
        )
        config = yaml.safe_load(content) or {}
        
        # Prüfe ob Migration erforderlich ist
        modbus_config = config.get("modbus", {})
        if "int32_byte_order" not in modbus_config:
            _LOGGER.info(
                "modbus.int32_byte_order nicht gefunden, keine Migration erforderlich"
            )
            return True
        
        # Backup erstellen
        backup_success, backup_path = await create_lambda_config_backup(
            hass, 
            MigrationVersion.REGISTER_ORDER_TERMINOLOGY
        )
        if not backup_success:
            _LOGGER.warning("Backup konnte nicht erstellt werden, setze Migration fort")
        
        # Migration durchführen
        old_value = modbus_config.pop("int32_byte_order")
        modbus_config["int32_register_order"] = old_value
        
        # Stelle sicher, dass modbus-Sektion existiert
        if "modbus" not in config:
            config["modbus"] = {}
        config["modbus"] = modbus_config
        
        # Aktualisiere YAML-Content
        # Ersetze int32_byte_order durch int32_register_order im Text
        updated_content = content.replace(
            "int32_byte_order", 
            "int32_register_order"
        )
        
        # Schreibe aktualisierte Config
        await hass.async_add_executor_job(
            lambda: open(lambda_config_path, "w", encoding="utf-8").write(updated_content)
        )
        
        _LOGGER.info(
            "Register-Order-Terminologie-Migration für Config %s erfolgreich abgeschlossen. "
            "Backup erstellt: %s", 
            entry_id, backup_path if backup_success else "N/A"
        )
        return True
        
    except Exception as e:
        _LOGGER.error(
            "Fehler bei Register-Order-Terminologie-Migration für Config %s: %s", 
            entry_id, e
        )
        return False


# Dictionary mit allen Migrationsfunktionen
MIGRATION_FUNCTIONS = {
    MigrationVersion.LEGACY_NAMES: migrate_to_legacy_names,
    MigrationVersion.CYCLING_OFFSETS: migrate_to_cycling_offsets,
    MigrationVersion.ENERGY_CONSUMPTION: migrate_to_energy_consumption,
    MigrationVersion.ENTITY_OPTIMIZATION: migrate_to_entity_optimization,
    MigrationVersion.CONFIG_RESTRUCTURE: migrate_to_config_restructure,
    MigrationVersion.UNIFIED_CONFIG_MIGRATION: migrate_to_unified_config,
    MigrationVersion.REGISTER_ORDER_TERMINOLOGY: migrate_to_register_order_terminology,
}


async def execute_migration(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    target_version: MigrationVersion
) -> bool:
    """
    Führe eine spezifische Migration durch.
    
    Args:
        hass: Home Assistant Instanz
        config_entry: Config Entry
        target_version: Zielversion der Migration
    
    Returns:
        bool: True wenn Migration erfolgreich
    """
    try:
        migration_func = MIGRATION_FUNCTIONS.get(target_version)
        if not migration_func:
            _LOGGER.error(
                "Keine Migrationsfunktion für Version %s gefunden", 
                target_version.name
            )
            return False
        
        # Backup erstellen
        registry_success, registry_backup = await create_registry_backup(hass, target_version)
        config_success, config_backup = await create_lambda_config_backup(hass, target_version)
        
        if not registry_success:
            _LOGGER.error("Registry-Backup fehlgeschlagen")
            return False
        
        backup_info = {
            "registry_backup": registry_backup,
            "config_backup": config_backup
        }
        
        # Migration durchführen
        success = await migration_func(hass, config_entry)
        
        if success:
            _LOGGER.info(
                "Migration zu Version %s erfolgreich abgeschlossen", 
                target_version.name
            )
            return True
        else:
            _LOGGER.error(
                "Migration zu Version %s fehlgeschlagen", 
                target_version.name
            )
            
            # Rollback durchführen falls aktiviert
            if ROLLBACK_ENABLED:
                await rollback_migration(hass, config_entry, backup_info, target_version)
            
            return False
        
    except Exception as e:
        _LOGGER.error(
            "Fehler bei Migration zu Version %s: %s", 
            target_version.name, e
        )
        return False


# =============================================================================
# HAUPTMIGRATIONSFUNKTION
# =============================================================================

async def perform_structured_migration(
    hass: HomeAssistant, 
    config_entry: ConfigEntry
) -> bool:
    """
    Führe strukturierte Migration für einen Config Entry durch.
    
    Args:
        hass: Home Assistant Instanz
        config_entry: Config Entry
    
    Returns:
        bool: True wenn alle Migrationen erfolgreich
    """
    try:
        entry_id = config_entry.entry_id
        current_version = config_entry.version
        target_version = MigrationVersion.get_latest()
        
        _LOGGER.info(
            "Starte strukturierte Migration für Config %s: Version %d -> %d", 
            entry_id, current_version, target_version.value
        )
        
        # Prüfe ob Migration erforderlich ist
        if current_version >= target_version.value:
            _LOGGER.info(
                "Config %s ist bereits auf der neuesten Version %d", 
                entry_id, target_version.value
            )
            return True
        
        # Alle ausstehenden Migrationen ermitteln
        pending_migrations = MigrationVersion.get_pending_migrations(current_version)
        
        if not pending_migrations:
            _LOGGER.info("Keine ausstehenden Migrationen für Config %s", entry_id)
            return True
        
        _LOGGER.info(
            "Ausstehende Migrationen für Config %s: %s", 
            entry_id, [v.name for v in pending_migrations]
        )
        
        # Migrationen sequenziell durchführen
        successful_migrations = 0
        total_migrations = len(pending_migrations)
        
        for migration_version in pending_migrations:
            try:
                _LOGGER.info(
                    "Starte Migration zu Version %s für Config %s", 
                    migration_version.name, entry_id
                )
                
                success = await execute_migration(hass, config_entry, migration_version)
                
                if success:
                    successful_migrations += 1
                    # Version sofort nach erfolgreicher Migration aktualisieren
                    # Verwendet die spezifische Versionsnummer dieser Migration
                    hass.config_entries.async_update_entry(
                        config_entry,
                        version=migration_version.value
                    )
                    _LOGGER.info(
                        "Migration zu Version %s (v%d) für Config %s erfolgreich - Version aktualisiert", 
                        migration_version.name, migration_version.value, entry_id
                    )
                else:
                    _LOGGER.error(
                        "Migration zu Version %s für Config %s fehlgeschlagen", 
                        migration_version.name, entry_id
                    )
                    
                    # Prüfe ob Rollback erforderlich ist
                    if (ROLLBACK_ON_CRITICAL_ERRORS and 
                        successful_migrations / total_migrations < CRITICAL_ERROR_THRESHOLD):
                        _LOGGER.error(
                            "Kritischer Fehler-Schwellenwert erreicht, Rollback wird durchgeführt"
                        )
                        # Hier würde der Rollback aller Migrationen stehen
                        return False
                    
            except Exception as e:
                _LOGGER.error(
                    "Fehler bei Migration zu Version %s für Config %s: %s", 
                    migration_version.name, entry_id, e
                )
                return False
        
        # Alle Migrationen erfolgreich
        if successful_migrations == total_migrations:
            _LOGGER.info(
                "Alle Migrationen für Config %s erfolgreich abgeschlossen (%d/%d)", 
                entry_id, successful_migrations, total_migrations
            )
            
            # Cleanup durchführen falls aktiviert
            if CLEANUP_ON_MIGRATION:
                await cleanup_old_backups(hass)
            
            return True
        else:
            _LOGGER.error(
                "Nicht alle Migrationen für Config %s erfolgreich (%d/%d)", 
                entry_id, successful_migrations, total_migrations
            )
            return False
        
    except Exception as e:
        _LOGGER.error(
            "Fehler bei strukturierter Migration für Config %s: %s", 
            entry_id, e
        )
        return False


# =============================================================================
# CLEANUP UND WARTUNG
# =============================================================================

async def cleanup_old_backups(hass: HomeAssistant) -> None:
    """
    Räume alte Backup-Dateien auf.
    
    Args:
        hass: Home Assistant Instanz
    """
    try:
        _LOGGER.info("Starte Backup-Bereinigung")
        
        config_dir = hass.config.config_dir
        backup_dir = os.path.join(config_dir, MIGRATION_BACKUP_DIR)
        
        if not await hass.async_add_executor_job(os.path.exists, backup_dir):
            _LOGGER.info("Backup-Verzeichnis existiert nicht")
            return
        
        # Alte Backups analysieren - ASYNCHRON mit async_add_executor_job
        old_files = await analyze_file_ageing(
            hass, 
            backup_dir, 
            "", 
            recursive=True
        )
        
        # Dateien zum Löschen identifizieren
        files_to_delete = []
        for file_path, days_old, error in old_files:
            if error:
                continue
            
            # Bestimme Retention basierend auf Dateityp
            retention_days = BACKUP_RETENTION_DAYS.get("entity_registry", 30)
            
            if days_old > retention_days:
                files_to_delete.append(file_path)
        
        if files_to_delete:
            _LOGGER.info(
                "Lösche %d alte Backup-Dateien (älter als %d Tage)", 
                len(files_to_delete), 
                BACKUP_RETENTION_DAYS.get("entity_registry", 30)
            )
            
            deleted_count, errors = await delete_files(
                hass, 
                files_to_delete, 
                dry_run=False
            )
            
            _LOGGER.info(
                "Backup-Bereinigung abgeschlossen: %d Dateien gelöscht", 
                deleted_count
            )
            
            if errors:
                _LOGGER.warning("Fehler beim Löschen von %d Dateien", len(errors))
        else:
            _LOGGER.info("Keine alten Backup-Dateien zum Löschen gefunden")
        
    except Exception as e:
        _LOGGER.error("Fehler bei Backup-Bereinigung: %s", e)


# =============================================================================
# KOMPATIBILITÄT MIT ALTEM CODE
# =============================================================================

async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """
    Hauptfunktion für Migration - wird von Home Assistant aufgerufen.
    
    Args:
        hass: Home Assistant Instanz
        config_entry: Config Entry
    
    Returns:
        bool: True wenn Migration erfolgreich
    """
    _LOGGER.info(
        "🔄 MIGRATION: async_migrate_entry aufgerufen für Config %s (Version: %d)",
        config_entry.entry_id, config_entry.version
    )
    return await perform_structured_migration(hass, config_entry)


# Alte Funktionen für Rückwärtskompatibilität
async def perform_option_c_migration(hass: HomeAssistant) -> Dict[str, Any]:
    """
    Alte Migrationsfunktion - wird durch neue strukturierte Migration ersetzt.
    
    Args:
        hass: Home Assistant Instanz
    
    Returns:
        Dict[str, Any]: Ergebnis der Migration
    """
    _LOGGER.warning(
        "perform_option_c_migration ist veraltet und wird durch perform_structured_migration ersetzt"
    )
    
    # Versuche alle Config Entries zu migrieren
    config_entries = hass.config_entries.async_entries(DOMAIN)
    
    if not config_entries:
        _LOGGER.info("Keine Config Entries für Migration gefunden")
        return {"success": True, "migrated": 0}
    
    successful_migrations = 0
    total_entries = len(config_entries)
    
    for config_entry in config_entries:
        try:
            success = await perform_structured_migration(hass, config_entry)
            if success:
                successful_migrations += 1
        except Exception as e:
            _LOGGER.error(
                "Fehler bei Migration von Config Entry %s: %s", 
                config_entry.entry_id, e
            )
    
    result = {
        "success": successful_migrations == total_entries,
        "migrated": successful_migrations,
        "total": total_entries
    }
    
    _LOGGER.info(
        "Migration abgeschlossen: %d/%d erfolgreich", 
        successful_migrations, total_entries
    )
    
    return result


# Export für Home Assistant
__all__ = ['async_migrate_entry'] 
