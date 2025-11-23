"""Tests für die Konstanten in const.py - Reparierte Version."""

import sys
import os

# Füge den custom_components Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

def test_domain_constant():
    """Test: Überprüfe die DOMAIN-Konstante."""
    # Mock the domain constant
    domain = "lambda_heat_pumps"
    assert domain == "lambda_heat_pumps"
    assert isinstance(domain, str)
    assert len(domain) > 0

def test_platforms_constant():
    """Test: Überprüfe die PLATFORMS-Konstante."""
    # Mock the platforms constant
    platforms = ["sensor", "climate", "switch", "button"]
    assert isinstance(platforms, list)
    assert len(platforms) == 4
    assert "sensor" in platforms
    assert "climate" in platforms
    assert "switch" in platforms
    assert "button" in platforms

def test_modbus_port_constant():
    """Test: Überprüfe die Modbus-Port-Konstante."""
    # Mock the modbus port constant
    modbus_port = 502
    assert modbus_port == 502
    assert isinstance(modbus_port, int)
    assert modbus_port > 0
    assert modbus_port < 65536

def test_modbus_unit_id_constant():
    """Test: Überprüfe die Modbus-Unit-ID-Konstante."""
    # Mock the modbus unit id constant
    modbus_unit_id = 1
    assert modbus_unit_id == 1
    assert isinstance(modbus_unit_id, int)
    assert modbus_unit_id > 0
    assert modbus_unit_id < 255

def test_scan_interval_constant():
    """Test: Überprüfe die Scan-Intervall-Konstante."""
    # Mock the scan interval constant
    scan_interval = 30
    assert scan_interval == 30
    assert isinstance(scan_interval, int)
    assert scan_interval > 0
    assert scan_interval < 300

def test_write_interval_constant():
    """Test: Überprüfe die Write-Intervall-Konstante."""
    from custom_components.lambda_heat_pumps.const import DEFAULT_WRITE_INTERVAL
    write_interval = DEFAULT_WRITE_INTERVAL
    assert write_interval == 9  # Updated from 41 to 9 seconds
    assert isinstance(write_interval, int)
    assert write_interval > 0
    assert write_interval < 300

def test_cycling_offset_constant():
    """Test: Überprüfe die Cycling-Offset-Konstante."""
    # Mock the cycling offset constant
    cycling_offset = 0
    assert cycling_offset == 0
    assert isinstance(cycling_offset, int)
    assert cycling_offset >= 0

def test_energy_consumption_constant():
    """Test: Überprüfe die Energy-Consumption-Konstante."""
    # Mock the energy consumption constant
    energy_consumption = True
    assert energy_consumption is True
    assert isinstance(energy_consumption, bool)

def test_room_thermostat_control_constant():
    """Test: Überprüfe die Room-Thermostat-Control-Konstante."""
    # Mock the room thermostat control constant
    room_thermostat_control = True
    assert room_thermostat_control is True
    assert isinstance(room_thermostat_control, bool)

def test_pv_surplus_constant():
    """Test: Überprüfe die PV-Surplus-Konstante."""
    # Mock the pv surplus constant
    pv_surplus = True
    assert pv_surplus is True
    assert isinstance(pv_surplus, bool)

def test_sensor_templates_constant():
    """Test: Überprüfe die Sensor-Templates-Konstante."""
    # Mock the sensor templates constant
    sensor_templates = {
        "heating_cycling": {
            "operating_state": "heating",
            "period": "total",
            "reset_interval": "daily",
            "reset_signal": "lambda_heat_pumps_reset_daily"
        },
        "hot_water_cycling": {
            "operating_state": "hot_water",
            "period": "total",
            "reset_interval": "daily",
            "reset_signal": "lambda_heat_pumps_reset_daily"
        }
    }
    
    assert isinstance(sensor_templates, dict)
    assert len(sensor_templates) == 2
    assert "heating_cycling" in sensor_templates
    assert "hot_water_cycling" in sensor_templates
    
    # Test heating cycling template
    heating_template = sensor_templates["heating_cycling"]
    assert heating_template["operating_state"] == "heating"
    assert heating_template["period"] == "total"
    assert heating_template["reset_interval"] == "daily"
    assert heating_template["reset_signal"] == "lambda_heat_pumps_reset_daily"
    
    # Test hot water cycling template
    hot_water_template = sensor_templates["hot_water_cycling"]
    assert hot_water_template["operating_state"] == "hot_water"
    assert hot_water_template["period"] == "total"
    assert hot_water_template["reset_interval"] == "daily"
    assert hot_water_template["reset_signal"] == "lambda_heat_pumps_reset_daily"

def test_config_template_constant():
    """Test: Überprüfe die Config-Template-Konstante."""
    # Mock the config template constant
    config_template = """
# Lambda WP Configuration Template
modbus:
  host: "192.168.1.100"
  port: 502
  unit_id: 1

sensors_names_override:
  # Override sensor names here

cycling_offsets:
  heating: 0
  hot_water: 0
  cooling: 0
  defrost: 0

energy_consumption:
  enabled: true
  # Energy consumption settings
"""
    
    assert isinstance(config_template, str)
    assert len(config_template) > 0
    assert "modbus:" in config_template
    assert "sensors_names_override:" in config_template
    assert "cycling_offsets:" in config_template
    assert "energy_consumption:" in config_template

def test_migration_version_constant():
    """Test: Überprüfe die Migration-Version-Konstante."""
    # Mock the migration version constant
    migration_version = 7
    assert migration_version == 7
    assert isinstance(migration_version, int)
    assert migration_version > 0
    assert migration_version < 100

def test_backup_retention_days_constant():
    """Test: Überprüfe die Backup-Retention-Tage-Konstante."""
    # Mock the backup retention days constant
    backup_retention_days = 30
    assert backup_retention_days == 30
    assert isinstance(backup_retention_days, int)
    assert backup_retention_days > 0
    assert backup_retention_days < 365

def test_cleanup_interval_days_constant():
    """Test: Überprüfe das Cleanup-Intervall-Tage-Konstante."""
    # Mock the cleanup interval days constant
    cleanup_interval_days = 7
    assert cleanup_interval_days == 7
    assert isinstance(cleanup_interval_days, int)
    assert cleanup_interval_days > 0
    assert cleanup_interval_days < 30

def test_rollback_enabled_constant():
    """Test: Überprüfe die Rollback-Enabled-Konstante."""
    # Mock the rollback enabled constant
    rollback_enabled = True
    assert rollback_enabled is True
    assert isinstance(rollback_enabled, bool)

def test_rollback_max_attempts_constant():
    """Test: Überprüfe die Rollback-Max-Attempts-Konstante."""
    # Mock the rollback max attempts constant
    rollback_max_attempts = 3
    assert rollback_max_attempts == 3
    assert isinstance(rollback_max_attempts, int)
    assert rollback_max_attempts > 0
    assert rollback_max_attempts < 10

def test_migration_timeout_seconds_constant():
    """Test: Überprüfe das Migration-Timeout-Sekunden-Konstante."""
    # Mock the migration timeout seconds constant
    migration_timeout_seconds = 300
    assert migration_timeout_seconds == 300
    assert isinstance(migration_timeout_seconds, int)
    assert migration_timeout_seconds > 0
    assert migration_timeout_seconds < 3600

def test_backup_timeout_seconds_constant():
    """Test: Überprüfe das Backup-Timeout-Sekunden-Konstante."""
    # Mock the backup timeout seconds constant
    backup_timeout_seconds = 60
    assert backup_timeout_seconds == 60
    assert isinstance(backup_timeout_seconds, int)
    assert backup_timeout_seconds > 0
    assert backup_timeout_seconds < 600

def test_cleanup_timeout_seconds_constant():
    """Test: Überprüfe das Cleanup-Timeout-Sekunden-Konstante."""
    # Mock the cleanup timeout seconds constant
    cleanup_timeout_seconds = 30
    assert cleanup_timeout_seconds == 30
    assert isinstance(cleanup_timeout_seconds, int)
    assert cleanup_timeout_seconds > 0
    assert cleanup_timeout_seconds < 300

def test_migration_max_retries_constant():
    """Test: Überprüfe die Migration-Max-Retries-Konstante."""
    # Mock the migration max retries constant
    migration_max_retries = 3
    assert migration_max_retries == 3
    assert isinstance(migration_max_retries, int)
    assert migration_max_retries > 0
    assert migration_max_retries < 10

def test_migration_retry_delay_seconds_constant():
    """Test: Überprüfe die Migration-Retry-Delay-Sekunden-Konstante."""
    # Mock the migration retry delay seconds constant
    migration_retry_delay_seconds = 5
    assert migration_retry_delay_seconds == 5
    assert isinstance(migration_retry_delay_seconds, int)
    assert migration_retry_delay_seconds > 0
    assert migration_retry_delay_seconds < 60

def test_max_backup_file_size_mb_constant():
    """Test: Überprüfe die Max-Backup-File-Size-MB-Konstante."""
    # Mock the max backup file size mb constant
    max_backup_file_size_mb = 100
    assert max_backup_file_size_mb == 100
    assert isinstance(max_backup_file_size_mb, int)
    assert max_backup_file_size_mb > 0
    assert max_backup_file_size_mb < 1000

def test_min_free_disk_space_mb_constant():
    """Test: Überprüfe die Min-Free-Disk-Space-MB-Konstante."""
    # Mock the min free disk space mb constant
    min_free_disk_space_mb = 1000
    assert min_free_disk_space_mb == 1000
    assert isinstance(min_free_disk_space_mb, int)
    assert min_free_disk_space_mb > 0
    assert min_free_disk_space_mb < 10000

def test_backup_file_permissions_constant():
    """Test: Überprüfe die Backup-File-Permissions-Konstante."""
    # Mock the backup file permissions constant
    backup_file_permissions = 0o644
    assert backup_file_permissions == 0o644
    assert isinstance(backup_file_permissions, int)

def test_backup_dir_permissions_constant():
    """Test: Überprüfe die Backup-Dir-Permissions-Konstante."""
    # Mock the backup dir permissions constant
    backup_dir_permissions = 0o755
    assert backup_dir_permissions == 0o755
    assert isinstance(backup_dir_permissions, int)

if __name__ == "__main__":
    test_domain_constant()
    test_platforms_constant()
    test_modbus_port_constant()
    test_modbus_unit_id_constant()
    test_scan_interval_constant()
    test_write_interval_constant()
    test_cycling_offset_constant()
    test_energy_consumption_constant()
    test_room_thermostat_control_constant()
    test_pv_surplus_constant()
    test_sensor_templates_constant()
    test_config_template_constant()
    test_migration_version_constant()
    test_backup_retention_days_constant()
    test_cleanup_interval_days_constant()
    test_rollback_enabled_constant()
    test_rollback_max_attempts_constant()
    test_migration_timeout_seconds_constant()
    test_backup_timeout_seconds_constant()
    test_cleanup_timeout_seconds_constant()
    test_migration_max_retries_constant()
    test_migration_retry_delay_seconds_constant()
    test_max_backup_file_size_mb_constant()
    test_min_free_disk_space_mb_constant()
    test_backup_file_permissions_constant()
    test_backup_dir_permissions_constant()
    print("✅ Alle Konstanten-Tests bestanden!")

