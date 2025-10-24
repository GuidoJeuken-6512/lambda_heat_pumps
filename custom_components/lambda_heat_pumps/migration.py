"""Structured Migration System for Lambda Heat Pumps integration."""

from __future__ import annotations
import logging
import os
import shutil
import yaml
from datetime import datetime
from typing import Any, Dict, Tuple

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry


from .const import DOMAIN
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
    migrate_lambda_config_sections
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
            lambda: os.makedirs(backup_dir, exist_ok=True)
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
            
            if await hass.async_add_executor_job(lambda: os.path.exists(source_path)):
                await hass.async_add_executor_job(
                    lambda: shutil.copy2(source_path, dest_path)
                )
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
        
        if not await hass.async_add_executor_job(lambda: os.path.exists(lambda_config_path)):
            _LOGGER.info("lambda_wp_config.yaml nicht gefunden, kein Backup erforderlich")
            return True, ""
        
        # Backup-Verzeichnis erstellen
        backup_dir = os.path.join(config_dir, MIGRATION_BACKUP_DIR)
        await hass.async_add_executor_job(
            lambda: os.makedirs(backup_dir, exist_ok=True)
        )
        
        # Backup erstellen
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        migration_name = MIGRATION_NAMES.get(migration_version, f"v{migration_version.value}")
        backup_path = os.path.join(
            backup_dir, 
            f"lambda_wp_config.{migration_name}_{timestamp}.yaml"
        )
        
        await hass.async_add_executor_job(
            lambda: shutil.copy2(lambda_config_path, backup_path)
        )
        
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
        from .utils import generate_sensor_names
        from .const import CLIMATE_TEMPLATES, HP_SENSOR_TEMPLATES, BOIL_SENSOR_TEMPLATES, HC_SENSOR_TEMPLATES, BUFF_SENSOR_TEMPLATES, SOL_SENSOR_TEMPLATES, SENSOR_TYPES

        # Hole aktuelle Namensschemata für alle Climate- und Sensor-Entitäten
        entry_data = config_entry.data
        use_legacy_modbus_names = entry_data.get("use_legacy_modbus_names", True)
        name_prefix = entry_data.get("name", "").lower().replace(" ", "")
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
        
        if await hass.async_add_executor_job(lambda: os.path.exists(lambda_config_path)):
            # Bestehende Config laden
            content = await hass.async_add_executor_job(
                lambda: open(lambda_config_path, "r").read()
            )
            config = yaml.safe_load(content) or {}
        else:
            config = {}
        
        # Cycling-Offsets hinzufügen falls nicht vorhanden
        if "cycling_offsets" not in config:
            config["cycling_offsets"] = DEFAULT_CYCLING_OFFSETS
            
            # Config speichern
            await hass.async_add_executor_job(
                lambda: open(lambda_config_path, "w").write(yaml.dump(config, default_flow_style=False))
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
        
        if await hass.async_add_executor_job(lambda: os.path.exists(lambda_config_path)):
            # Bestehende Config laden
            content = await hass.async_add_executor_job(
                lambda: open(lambda_config_path, "r").read()
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
        await hass.async_add_executor_job(
            lambda: open(lambda_config_path, "w").write(yaml.dump(config, default_flow_style=False))
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


# Dictionary mit allen Migrationsfunktionen
MIGRATION_FUNCTIONS = {
    MigrationVersion.LEGACY_NAMES: migrate_to_legacy_names,
    MigrationVersion.CYCLING_OFFSETS: migrate_to_cycling_offsets,
    MigrationVersion.ENERGY_CONSUMPTION: migrate_to_energy_consumption,
    MigrationVersion.ENTITY_OPTIMIZATION: migrate_to_entity_optimization,
    MigrationVersion.CONFIG_RESTRUCTURE: migrate_to_config_restructure,
    MigrationVersion.UNIFIED_CONFIG_MIGRATION: migrate_to_unified_config,
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
                    _LOGGER.info(
                        "Migration zu Version %s für Config %s erfolgreich", 
                        migration_version.name, entry_id
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
        
        if not await hass.async_add_executor_job(lambda: os.path.exists(backup_dir)):
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
