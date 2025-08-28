"""Constants for Lambda Heat Pumps migration system."""

from __future__ import annotations
from enum import IntEnum
from typing import List


# Migration Version Management
class MigrationVersion(IntEnum):
    """Enum für alle verfügbaren Migrationsversionen."""
    
    # Bestehende Versionen
    INITIAL = 1                    # Ursprüngliche Version
    LEGACY_NAMES = 2              # Entity-Namen Migration
    
    # Neue Versionen mit Config-Datei-Updates
    CYCLING_OFFSETS = 3           # lambda_wp_config.yaml: cycling_offsets
    ENTITY_OPTIMIZATION = 4       # Entity-Struktur optimieren
    CONFIG_RESTRUCTURE = 5        # Konfigurationsschema ändern
    
    # Hilfsmethoden
    @classmethod
    def get_latest(cls) -> 'MigrationVersion':
        """Ermittle die neueste verfügbare Version."""
        return max(cls)
    
    @classmethod
    def get_pending_migrations(cls, current_version: int) -> List['MigrationVersion']:
        """Ermittle alle ausstehenden Migrationen."""
        return [
            version for version in cls 
            if current_version < version <= cls.get_latest()
        ]


# =============================================================================
# BACKUP UND CLEANUP KONSTANTEN
# =============================================================================

# Backup-Verzeichnisse
MIGRATION_BACKUP_DIR = "lambda_heat_pumps/backup"
MIGRATION_BACKUP_RETENTION_DAYS = 30

# Backup-Datei-Präfixe
BACKUP_PREFIX_REGISTRY = "core"
BACKUP_PREFIX_CONFIG = "lambda_wp_config"

# Alte Backup-Pfade (aus utils.py)
OLD_BACKUP_EXTENSIONS = [
    ".backup",                    # lambda_wp_config.yaml.backup
    ".backup.old",               # lambda_wp_config.yaml.backup.old
    ".backup.bak",               # lambda_wp_config.yaml.backup.bak
]

# Neue Backup-Pfade (zentralisiert)
NEW_BACKUP_EXTENSIONS = {
    "entity_registry": ".entity_registry",
    "device_registry": ".device_registry", 
    "config_entries": ".config_entries",
    "lambda_config": ".yaml",
}

# =============================================================================
# CLEANUP KONSTANTEN
# =============================================================================

# Cleanup-Intervall (wie oft wird aufgeräumt)
CLEANUP_INTERVAL_DAYS = 7        # Alle 7 Tage wird aufgeräumt
CLEANUP_ENABLED = True           # Aufräumfunktion aktiviert/deaktiviert
CLEANUP_ON_MIGRATION = True      # Aufräum bei jeder Migration durchführen
CLEANUP_ON_SETUP = False         # Aufräum beim Setup der Integration (nicht gewünscht)

# Backup-Retention für verschiedene Dateitypen (in Tagen)
BACKUP_RETENTION_DAYS = {
    "entity_registry": 30,        # Registry-Backups: 30 Tage
    "device_registry": 30,        # Device-Registry-Backups: 30 Tage
    "config_entries": 30,         # Config-Entry-Backups: 30 Tage
    "lambda_config": 60,          # Config-Datei-Backups: 60 Tage (länger behalten)
    "old_backups": 7,             # Alte .backup Dateien: nur 7 Tage
}

# Cleanup-Schwellenwerte
CLEANUP_MIN_FREE_SPACE_MB = 100  # Mindestfreier Speicherplatz in MB
CLEANUP_MAX_BACKUP_COUNT = 100   # Maximale Anzahl von Backup-Dateien
CLEANUP_MAX_TOTAL_SIZE_MB = 500  # Maximale Gesamtgröße aller Backups in MB

# =============================================================================
# MIGRATION KONSTANTEN
# =============================================================================

# Migration-Namen für Backup-Dateien
MIGRATION_NAMES = {
    MigrationVersion.LEGACY_NAMES: "legacy_names_migration",
    MigrationVersion.CYCLING_OFFSETS: "cycling_offsets_migration",
    MigrationVersion.ENTITY_OPTIMIZATION: "entity_optimization_migration",
    MigrationVersion.CONFIG_RESTRUCTURE: "config_restructure_migration",
}

# Standardwerte für neue Config-Sektionen
DEFAULT_CYCLING_OFFSETS = {
    "hp1": {
        "heating_cycling_total": 0,
        "hot_water_cycling_total": 0,
        "cooling_cycling_total": 0,
        "defrost_cycling_total": 0,
    }
}

# Validierung der lambda_wp_config.yaml
REQUIRED_CONFIG_SECTIONS = [
    "disabled_registers",
]

# =============================================================================
# ROLLBACK KONSTANTEN
# =============================================================================

# Rollback-Einstellungen
ROLLBACK_ENABLED = True
ROLLBACK_ON_CRITICAL_ERRORS = True
CRITICAL_ERROR_THRESHOLD = 0.5   # 50% der Migrationen müssen fehlschlagen
ROLLBACK_MAX_ATTEMPTS = 3        # Maximale Anzahl von Rollback-Versuchen

# =============================================================================
# LOGGING UND DEBUGGING KONSTANTEN
# =============================================================================

# Migration-Logging
MIGRATION_LOG_PREFIX = "Migration"
MIGRATION_SUCCESS_LOG = "Migration {version} erfolgreich abgeschlossen"
MIGRATION_FAILED_LOG = "Migration {version} fehlgeschlagen: {error}"
MIGRATION_SKIP_LOG = "Migration {version} übersprungen - bereits auf Version {current}"

# Cleanup-Logging
CLEANUP_LOG_PREFIX = "Cleanup"
CLEANUP_START_LOG = "Starte Backup-Bereinigung"
CLEANUP_COMPLETE_LOG = "Backup-Bereinigung abgeschlossen: {removed} Dateien entfernt"
CLEANUP_ERROR_LOG = "Fehler bei Backup-Bereinigung: {error}"

# =============================================================================
# PERFORMANCE UND TIMEOUT KONSTANTEN
# =============================================================================

# Timeouts für Migrationen
MIGRATION_TIMEOUT_SECONDS = 300  # 5 Minuten Timeout pro Migration
BACKUP_TIMEOUT_SECONDS = 60      # 1 Minute Timeout für Backups
CLEANUP_TIMEOUT_SECONDS = 120    # 2 Minuten Timeout für Cleanup

# Retry-Einstellungen
MIGRATION_MAX_RETRIES = 3        # Maximale Anzahl von Wiederholungsversuchen
MIGRATION_RETRY_DELAY_SECONDS = 5  # Verzögerung zwischen Wiederholungsversuchen

# =============================================================================
# VALIDIERUNG UND SICHERHEIT
# =============================================================================

# Datei-Größen-Limits
MAX_BACKUP_FILE_SIZE_MB = 50     # Maximale Größe einer einzelnen Backup-Datei
MIN_FREE_DISK_SPACE_MB = 100     # Mindestfreier Speicherplatz vor Migration

# Datei-Berechtigungen
BACKUP_FILE_PERMISSIONS = 0o644  # Unix-Berechtigungen für Backup-Dateien
BACKUP_DIR_PERMISSIONS = 0o755   # Unix-Berechtigungen für Backup-Verzeichnisse
