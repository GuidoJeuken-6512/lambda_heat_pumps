"""Tests für die Migration-Konstanten in const_migration.py."""

import pytest
from custom_components.lambda_heat_pumps.const_migration import (
    MigrationVersion,
    MIGRATION_BACKUP_DIR,
    MIGRATION_BACKUP_RETENTION_DAYS,
    BACKUP_RETENTION_DAYS,
    CLEANUP_INTERVAL_DAYS,
    CLEANUP_ENABLED,
    CLEANUP_ON_MIGRATION,
    CLEANUP_ON_SETUP,
    MIGRATION_NAMES,
    DEFAULT_CYCLING_OFFSETS,
    REQUIRED_CONFIG_SECTIONS,
    ROLLBACK_ENABLED,
    ROLLBACK_ON_CRITICAL_ERRORS,
    CRITICAL_ERROR_THRESHOLD,
    ROLLBACK_MAX_ATTEMPTS,
    MIGRATION_TIMEOUT_SECONDS,
    BACKUP_TIMEOUT_SECONDS,
    CLEANUP_TIMEOUT_SECONDS,
    MIGRATION_MAX_RETRIES,
    MIGRATION_RETRY_DELAY_SECONDS,
    MAX_BACKUP_FILE_SIZE_MB,
    MIN_FREE_DISK_SPACE_MB,
    BACKUP_FILE_PERMISSIONS,
    BACKUP_DIR_PERMISSIONS
)


class TestMigrationVersion:
    """Test-Klasse für die MigrationVersion Enum."""
    
    def test_migration_version_values(self):
        """Test: Überprüfe die Werte der MigrationVersion Enum."""
        assert MigrationVersion.INITIAL == 1
        assert MigrationVersion.LEGACY_NAMES == 2
        assert MigrationVersion.CYCLING_OFFSETS == 3
        assert MigrationVersion.ENERGY_CONSUMPTION == 4
        assert MigrationVersion.ENTITY_OPTIMIZATION == 5
        assert MigrationVersion.CONFIG_RESTRUCTURE == 6
    
    def test_migration_version_names(self):
        """Test: Überprüfe die Namen der MigrationVersion Enum."""
        assert MigrationVersion.INITIAL.name == "INITIAL"
        assert MigrationVersion.LEGACY_NAMES.name == "LEGACY_NAMES"
        assert MigrationVersion.CYCLING_OFFSETS.name == "CYCLING_OFFSETS"
        assert MigrationVersion.ENTITY_OPTIMIZATION.name == "ENTITY_OPTIMIZATION"
        assert MigrationVersion.CONFIG_RESTRUCTURE.name == "CONFIG_RESTRUCTURE"
    
    def test_get_latest(self):
        """Test: Überprüfe die get_latest Methode."""
        latest = MigrationVersion.get_latest()
        assert latest == MigrationVersion.CONFIG_RESTRUCTURE
        assert latest.value == 6
    
    def test_get_pending_migrations(self):
        """Test: Überprüfe die get_pending_migrations Methode."""
        # Von Version 1
        pending = MigrationVersion.get_pending_migrations(1)
        expected = [
            MigrationVersion.LEGACY_NAMES,
            MigrationVersion.CYCLING_OFFSETS,
            MigrationVersion.ENERGY_CONSUMPTION,
            MigrationVersion.ENTITY_OPTIMIZATION,
            MigrationVersion.CONFIG_RESTRUCTURE
        ]
        assert pending == expected
        
        # Von Version 2
        pending = MigrationVersion.get_pending_migrations(2)
        expected = [
            MigrationVersion.CYCLING_OFFSETS,
            MigrationVersion.ENERGY_CONSUMPTION,
            MigrationVersion.ENTITY_OPTIMIZATION,
            MigrationVersion.CONFIG_RESTRUCTURE
        ]
        assert pending == expected
        
        # Von Version 6 (aktuellste)
        pending = MigrationVersion.get_pending_migrations(6)
        assert pending == []
        
        # Von Version 0 (vor der ersten Version)
        pending = MigrationVersion.get_pending_migrations(0)
        expected = [
            MigrationVersion.INITIAL,
            MigrationVersion.LEGACY_NAMES,
            MigrationVersion.CYCLING_OFFSETS,
            MigrationVersion.ENERGY_CONSUMPTION,
            MigrationVersion.ENTITY_OPTIMIZATION,
            MigrationVersion.CONFIG_RESTRUCTURE
        ]
        assert pending == expected
    
    def test_migration_version_comparison(self):
        """Test: Überprüfe Vergleiche zwischen MigrationVersion."""
        assert MigrationVersion.INITIAL < MigrationVersion.LEGACY_NAMES
        assert MigrationVersion.LEGACY_NAMES < MigrationVersion.CYCLING_OFFSETS
        assert MigrationVersion.CYCLING_OFFSETS < MigrationVersion.ENTITY_OPTIMIZATION
        assert MigrationVersion.ENTITY_OPTIMIZATION < MigrationVersion.CONFIG_RESTRUCTURE
        
        assert MigrationVersion.CONFIG_RESTRUCTURE > MigrationVersion.ENTITY_OPTIMIZATION
        assert MigrationVersion.ENTITY_OPTIMIZATION > MigrationVersion.CYCLING_OFFSETS
        assert MigrationVersion.CYCLING_OFFSETS > MigrationVersion.LEGACY_NAMES
        assert MigrationVersion.LEGACY_NAMES > MigrationVersion.INITIAL


class TestBackupConstants:
    """Test-Klasse für Backup-bezogene Konstanten."""
    
    def test_backup_directory(self):
        """Test: Überprüfe Backup-Verzeichnis-Pfad."""
        assert MIGRATION_BACKUP_DIR == "lambda_heat_pumps/backup"
        assert isinstance(MIGRATION_BACKUP_DIR, str)
    
    def test_backup_retention_days(self):
        """Test: Überprüfe Backup-Retention-Tage."""
        assert MIGRATION_BACKUP_RETENTION_DAYS == 30
        assert isinstance(MIGRATION_BACKUP_RETENTION_DAYS, int)
        assert MIGRATION_BACKUP_RETENTION_DAYS > 0
    
    def test_backup_retention_days_dict(self):
        """Test: Überprüfe Backup-Retention-Tage für verschiedene Dateitypen."""
        assert isinstance(BACKUP_RETENTION_DAYS, dict)
        assert "entity_registry" in BACKUP_RETENTION_DAYS
        assert "device_registry" in BACKUP_RETENTION_DAYS
        assert "config_entries" in BACKUP_RETENTION_DAYS
        assert "lambda_config" in BACKUP_RETENTION_DAYS
        assert "old_backups" in BACKUP_RETENTION_DAYS
        
        # Überprüfe, dass alle Werte positive Ganzzahlen sind
        for key, value in BACKUP_RETENTION_DAYS.items():
            assert isinstance(value, int)
            assert value > 0
            retention_msg = f"Backup-Retention für {key} ist {value} Tage"
            assert retention_msg


class TestCleanupConstants:
    """Test-Klasse für Cleanup-bezogene Konstanten."""
    
    def test_cleanup_interval(self):
        """Test: Überprüfe Cleanup-Intervall."""
        assert CLEANUP_INTERVAL_DAYS == 7
        assert isinstance(CLEANUP_INTERVAL_DAYS, int)
        assert CLEANUP_INTERVAL_DAYS > 0
    
    def test_cleanup_enabled(self):
        """Test: Überprüfe Cleanup-Status."""
        assert CLEANUP_ENABLED is True
        assert isinstance(CLEANUP_ENABLED, bool)
    
    def test_cleanup_on_migration(self):
        """Test: Überprüfe Cleanup bei Migration."""
        assert CLEANUP_ON_MIGRATION is True
        assert isinstance(CLEANUP_ON_MIGRATION, bool)
    
    def test_cleanup_on_setup(self):
        """Test: Überprüfe Cleanup beim Setup."""
        assert CLEANUP_ON_SETUP is False
        assert isinstance(CLEANUP_ON_SETUP, bool)


class TestMigrationNames:
    """Test-Klasse für Migration-Namen."""
    
    def test_migration_names_dict(self):
        """Test: Überprüfe Migration-Namen Dictionary."""
        assert isinstance(MIGRATION_NAMES, dict)
        assert len(MIGRATION_NAMES) == 5  # 5 Migrationen definiert
        
        # Überprüfe alle Migration-Namen
        expected_names = [
            "legacy_names_migration",
            "cycling_offsets_migration",
            "entity_optimization_migration",
            "config_restructure_migration"
        ]
        
        for name in expected_names:
            name_found = any(name == value for value in MIGRATION_NAMES.values())
            assert name_found
    
    def test_migration_names_values(self):
        """Test: Überprüfe spezifische Migration-Namen."""
        assert (MIGRATION_NAMES[MigrationVersion.LEGACY_NAMES] == 
                "legacy_names_migration")
        assert (MIGRATION_NAMES[MigrationVersion.CYCLING_OFFSETS] == 
                "cycling_offsets_migration")
        assert (MIGRATION_NAMES[MigrationVersion.ENTITY_OPTIMIZATION] == 
                "entity_optimization_migration")
        assert (MIGRATION_NAMES[MigrationVersion.CONFIG_RESTRUCTURE] == 
                "config_restructure_migration")


class TestDefaultValues:
    """Test-Klasse für Standardwerte."""
    
    def test_default_cycling_offsets(self):
        """Test: Überprüfe Standard-Cycling-Offsets."""
        assert isinstance(DEFAULT_CYCLING_OFFSETS, dict)
        assert "hp1" in DEFAULT_CYCLING_OFFSETS
        
        hp1_config = DEFAULT_CYCLING_OFFSETS["hp1"]
        expected_keys = [
            "heating_cycling_total",
            "hot_water_cycling_total",
            "cooling_cycling_total",
            "defrost_cycling_total"
        ]
        
        for key in expected_keys:
            assert key in hp1_config
            assert hp1_config[key] == 0
    
    def test_required_config_sections(self):
        """Test: Überprüfe erforderliche Config-Sektionen."""
        assert isinstance(REQUIRED_CONFIG_SECTIONS, list)
        assert "disabled_registers" in REQUIRED_CONFIG_SECTIONS
        assert len(REQUIRED_CONFIG_SECTIONS) == 1


class TestRollbackConstants:
    """Test-Klasse für Rollback-Konstanten."""
    
    def test_rollback_enabled(self):
        """Test: Überprüfe Rollback-Status."""
        assert ROLLBACK_ENABLED is True
        assert isinstance(ROLLBACK_ENABLED, bool)
    
    def test_rollback_on_critical_errors(self):
        """Test: Überprüfe Rollback bei kritischen Fehlern."""
        assert ROLLBACK_ON_CRITICAL_ERRORS is True
        assert isinstance(ROLLBACK_ON_CRITICAL_ERRORS, bool)
    
    def test_critical_error_threshold(self):
        """Test: Überprüfe kritischen Fehler-Schwellenwert."""
        assert CRITICAL_ERROR_THRESHOLD == 0.5
        assert isinstance(CRITICAL_ERROR_THRESHOLD, float)
        assert 0.0 <= CRITICAL_ERROR_THRESHOLD <= 1.0
    
    def test_rollback_max_attempts(self):
        """Test: Überprüfe maximale Rollback-Versuche."""
        assert ROLLBACK_MAX_ATTEMPTS == 3
        assert isinstance(ROLLBACK_MAX_ATTEMPTS, int)
        assert ROLLBACK_MAX_ATTEMPTS > 0


class TestTimeoutConstants:
    """Test-Klasse für Timeout-Konstanten."""
    
    def test_migration_timeout(self):
        """Test: Überprüfe Migration-Timeout."""
        assert MIGRATION_TIMEOUT_SECONDS == 300
        assert isinstance(MIGRATION_TIMEOUT_SECONDS, int)
        assert MIGRATION_TIMEOUT_SECONDS > 0
    
    def test_backup_timeout(self):
        """Test: Überprüfe Backup-Timeout."""
        assert BACKUP_TIMEOUT_SECONDS == 60
        assert isinstance(BACKUP_TIMEOUT_SECONDS, int)
        assert BACKUP_TIMEOUT_SECONDS > 0
    
    def test_cleanup_timeout(self):
        """Test: Überprüfe Cleanup-Timeout."""
        assert CLEANUP_TIMEOUT_SECONDS == 120
        assert isinstance(CLEANUP_TIMEOUT_SECONDS, int)
        assert CLEANUP_TIMEOUT_SECONDS > 0
    
    def test_timeout_hierarchy(self):
        """Test: Überprüfe Timeout-Hierarchie."""
        # Migration sollte den längsten Timeout haben
        assert MIGRATION_TIMEOUT_SECONDS > CLEANUP_TIMEOUT_SECONDS
        assert CLEANUP_TIMEOUT_SECONDS > BACKUP_TIMEOUT_SECONDS


class TestRetryConstants:
    """Test-Klasse für Retry-Konstanten."""
    
    def test_migration_max_retries(self):
        """Test: Überprüfe maximale Migration-Wiederholungen."""
        assert MIGRATION_MAX_RETRIES == 3
        assert isinstance(MIGRATION_MAX_RETRIES, int)
        assert MIGRATION_MAX_RETRIES > 0
    
    def test_migration_retry_delay(self):
        """Test: Überprüfe Migration-Wiederholungsverzögerung."""
        assert MIGRATION_RETRY_DELAY_SECONDS == 5
        assert isinstance(MIGRATION_RETRY_DELAY_SECONDS, int)
        assert MIGRATION_RETRY_DELAY_SECONDS > 0


class TestFileSizeConstants:
    """Test-Klasse für Dateigrößen-Konstanten."""
    
    def test_max_backup_file_size(self):
        """Test: Überprüfe maximale Backup-Dateigröße."""
        assert MAX_BACKUP_FILE_SIZE_MB == 50
        assert isinstance(MAX_BACKUP_FILE_SIZE_MB, int)
        assert MAX_BACKUP_FILE_SIZE_MB > 0
    
    def test_min_free_disk_space(self):
        """Test: Überprüfe minimalen freien Speicherplatz."""
        assert MIN_FREE_DISK_SPACE_MB == 100
        assert isinstance(MIN_FREE_DISK_SPACE_MB, int)
        assert MIN_FREE_DISK_SPACE_MB > 0


class TestPermissionConstants:
    """Test-Klasse für Berechtigungs-Konstanten."""
    
    def test_backup_file_permissions(self):
        """Test: Überprüfe Backup-Datei-Berechtigungen."""
        assert BACKUP_FILE_PERMISSIONS == 0o644
        assert isinstance(BACKUP_FILE_PERMISSIONS, int)
        # Überprüfe, dass es eine gültige Oktal-Zahl ist
        assert 0 <= BACKUP_FILE_PERMISSIONS <= 0o777
    
    def test_backup_dir_permissions(self):
        """Test: Überprüfe Backup-Verzeichnis-Berechtigungen."""
        assert BACKUP_DIR_PERMISSIONS == 0o755
        assert isinstance(BACKUP_DIR_PERMISSIONS, int)
        # Überprüfe, dass es eine gültige Oktal-Zahl ist
        assert 0 <= BACKUP_DIR_PERMISSIONS <= 0o777


if __name__ == "__main__":
    pytest.main([__file__])
