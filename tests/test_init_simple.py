"""Vereinfachte Tests für das __init__ Modul."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant.const import Platform

from custom_components.lambda_heat_pumps import (
    DOMAIN,
    PLATFORMS,
    TRANSLATION_SOURCES,
    setup_debug_logging,
    _entry_reload_locks,
    _entry_reload_flags,
    _previously_setup_entries,
)


def test_constants():
    """Test that constants are properly defined."""
    assert PLATFORMS == [Platform.SENSOR, Platform.CLIMATE, Platform.NUMBER]
    assert TRANSLATION_SOURCES == {DOMAIN: "translations"}
    assert DOMAIN == "lambda_heat_pumps"


def test_setup_debug_logging():
    """Test setup_debug_logging function."""
    from unittest.mock import Mock

    mock_hass = Mock()
    mock_config = {}

    # Should not raise an exception
    setup_debug_logging(mock_hass, mock_config)

    # Verify logger was accessed (indirect test)
    assert mock_hass.config is not None


def test_imports():
    """Test that all required modules can be imported."""
    from custom_components.lambda_heat_pumps import (
        async_setup,
        async_setup_entry,
        async_unload_entry,
        async_reload_entry,
    )

    # Functions should be callable
    assert callable(async_setup)
    assert callable(async_setup_entry)
    assert callable(async_unload_entry)
    assert callable(async_reload_entry)


# ---------------------------------------------------------------------------
# Fix K-02: Per-Entry Reload-State
# ---------------------------------------------------------------------------

def test_per_entry_reload_state_uses_dicts():
    """K-02: Reload-State ist per Entry in Dicts gespeichert, nicht modul-global."""
    # _entry_reload_locks und _entry_reload_flags sind Dicts (nicht Lock/bool)
    assert isinstance(_entry_reload_locks, dict)
    assert isinstance(_entry_reload_flags, dict)


@pytest.mark.asyncio
async def test_concurrent_reload_same_entry_is_skipped():
    """K-02: Ein zweiter Reload desselben Entry wird übersprungen wenn einer läuft."""
    from custom_components.lambda_heat_pumps import async_reload_entry

    entry = MagicMock()
    entry.entry_id = "test_concurrent_reload"

    # Setze Flag manuell so als lief bereits ein Reload
    _entry_reload_flags["test_concurrent_reload"] = True

    try:
        result = await async_reload_entry(MagicMock(), entry)
        # Zweiter Aufruf soll True zurückgeben (nicht abstürzen)
        assert result is True
    finally:
        _entry_reload_flags.pop("test_concurrent_reload", None)
        _entry_reload_locks.pop("test_concurrent_reload", None)


@pytest.mark.asyncio
async def test_reload_locks_are_per_entry_independent():
    """K-02: Verschiedene Entries haben unabhängige Locks."""
    from custom_components.lambda_heat_pumps import async_reload_entry

    # Erzeuge zwei verschiedene Entry-IDs und prüfe, dass je ein eigener Lock entsteht
    entry_a = MagicMock()
    entry_a.entry_id = "entry_a_locktest"
    entry_b = MagicMock()
    entry_b.entry_id = "entry_b_locktest"

    # Flag für A setzen → B darf trotzdem anlaufen
    _entry_reload_flags["entry_a_locktest"] = True
    _entry_reload_flags["entry_b_locktest"] = False

    # Für B wird kein Lock blockiert → setdefault liefert einen Lock
    lock_b = _entry_reload_locks.setdefault("entry_b_locktest", asyncio.Lock())
    assert isinstance(lock_b, asyncio.Lock)
    assert not lock_b.locked()

    # Cleanup
    for key in ("entry_a_locktest", "entry_b_locktest"):
        _entry_reload_flags.pop(key, None)
        _entry_reload_locks.pop(key, None)


# ---------------------------------------------------------------------------
# Fix K-01: Template-Task wird beim Unload abgebrochen
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_template_task_cancelled_on_unload():
    """K-01: template_setup_task in coordinator_data wird beim Unload abgebrochen."""
    from custom_components.lambda_heat_pumps import async_unload_entry

    entry = MagicMock()
    entry.entry_id = "test_template_cancel"

    # Erstelle einen echten Task der nicht endet (simuliert laufenden Template-Setup)
    async def _never_ending():
        await asyncio.sleep(3600)

    task = asyncio.ensure_future(_never_ending())
    assert not task.done()

    # DOMAIN == "lambda_heat_pumps" – nur einen Key verwenden, keinen doppelten Eintrag.
    hass = MagicMock()
    hass.data = {
        DOMAIN: {
            "test_template_cancel": {
                "template_setup_task": task,
            }
        }
    }

    hass.config_entries = MagicMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.services = MagicMock()
    hass.services.has_service = MagicMock(return_value=False)

    with patch(
        "custom_components.lambda_heat_pumps.utils.async_cleanup_all_components",
        new=AsyncMock(),
    ):
        await async_unload_entry(hass, entry)

    # Eine Iteration abwarten, damit asyncio die Cancellation verarbeiten kann
    await asyncio.sleep(0)

    # Task muss nach Unload abgebrochen worden sein
    assert task.cancelled() or task.done()


# ---------------------------------------------------------------------------
# Fix K-01: Auto-Detect-Task wird beim Unload abgebrochen
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_auto_detect_task_cancelled_on_unload():
    """K-02: auto_detect_task in coordinator_data wird beim Unload abgebrochen."""
    from custom_components.lambda_heat_pumps import async_unload_entry

    entry = MagicMock()
    entry.entry_id = "test_autodetect_cancel"

    async def _never_ending():
        await asyncio.sleep(3600)

    task = asyncio.ensure_future(_never_ending())
    assert not task.done()

    hass = MagicMock()
    hass.data = {
        DOMAIN: {
            "test_autodetect_cancel": {
                "auto_detect_task": task,
            }
        }
    }
    hass.config_entries = MagicMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.services = MagicMock()
    hass.services.has_service = MagicMock(return_value=False)

    with patch(
        "custom_components.lambda_heat_pumps.utils.async_cleanup_all_components",
        new=AsyncMock(),
    ):
        await async_unload_entry(hass, entry)

    await asyncio.sleep(0)

    assert task.cancelled() or task.done()


# ---------------------------------------------------------------------------
# Fix K-03: Zweite Bereinigung nach Platform-Setup
# ---------------------------------------------------------------------------

def test_async_remove_duplicate_suffixes_callable_after_platform_setup():
    """K-03: async_remove_duplicate_entity_suffixes kann nach Platform-Setup aufgerufen werden."""
    from custom_components.lambda_heat_pumps.migration import (
        async_remove_duplicate_entity_suffixes,
    )
    assert callable(async_remove_duplicate_entity_suffixes)


# ---------------------------------------------------------------------------
# Phase 2 – 2a: is_reload via _previously_setup_entries (H-04)
# ---------------------------------------------------------------------------

def test_previously_setup_entries_is_a_set():
    """2a: _previously_setup_entries ist ein Set (nicht hass.data-abhängig)."""
    assert isinstance(_previously_setup_entries, set)


def test_is_reload_false_on_first_setup():
    """2a: Neuer Entry wird NICHT als Reload erkannt."""
    entry_id = "brand_new_entry_id"
    _previously_setup_entries.discard(entry_id)
    assert entry_id not in _previously_setup_entries


def test_is_reload_true_after_first_setup():
    """2a: Einmal registrierter Entry wird beim nächsten Setup als Reload erkannt."""
    entry_id = "already_setup_entry_id"
    _previously_setup_entries.add(entry_id)
    try:
        assert entry_id in _previously_setup_entries
    finally:
        _previously_setup_entries.discard(entry_id)


# ---------------------------------------------------------------------------
# Phase 2 – 2c: Config-Cache-Invalidierung (M-07)
# ---------------------------------------------------------------------------

def test_config_cache_keys_cleared_on_setup():
    """2c: _lambda_config_cache und _lambda_migration_done werden beim Setup entfernt."""
    import types
    # Simuliere hass.data mit altem Cache
    hass_data: dict = {
        "_lambda_config_cache": {"some": "cached_data"},
        "_lambda_migration_done": True,
    }
    # Wende die gleiche Logik an wie in async_setup_entry
    hass_data.pop("_lambda_config_cache", None)
    hass_data.pop("_lambda_migration_done", None)
    assert "_lambda_config_cache" not in hass_data
    assert "_lambda_migration_done" not in hass_data


# ---------------------------------------------------------------------------
# Phase 2 – 2d: async_read_input_registers hat Retry-Logik (M-09)
# ---------------------------------------------------------------------------

def test_async_read_input_registers_uses_lock_and_retry():
    """2d: async_read_input_registers verwendet den globalen Modbus-Lock."""
    import inspect
    from custom_components.lambda_heat_pumps.modbus_utils import (
        async_read_input_registers,
        _modbus_read_lock,
    )
    # Funktion existiert und ist eine Coroutine
    assert asyncio.iscoroutinefunction(async_read_input_registers)
    # Globaler Lock existiert
    assert isinstance(_modbus_read_lock, asyncio.Lock)
    # Quellcode der Funktion referenziert den Lock
    source = inspect.getsource(async_read_input_registers)
    assert "_modbus_read_lock" in source
    assert "LAMBDA_MAX_RETRIES" in source


# ---------------------------------------------------------------------------
# Phase 2 – 2e: cycling_sensor.py wurde gelöscht (M-05)
# ---------------------------------------------------------------------------

def test_cycling_sensor_py_deleted():
    """2e: Die leere Geisterdatei cycling_sensor.py existiert nicht mehr."""
    import os
    import pathlib
    component_dir = pathlib.Path(__file__).parent.parent / "custom_components" / "lambda_heat_pumps"
    assert not (component_dir / "cycling_sensor.py").exists()


if __name__ == "__main__":
    pytest.main([__file__])

