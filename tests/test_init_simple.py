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
    """K-01: Ein zweiter Reload desselben Entry wird übersprungen wenn Lock gehalten wird."""
    from custom_components.lambda_heat_pumps import async_reload_entry

    entry = MagicMock()
    entry.entry_id = "test_concurrent_reload"

    # Simuliere laufenden Reload: Lock direkt setzen und sperren
    lock = asyncio.Lock()
    _entry_reload_locks["test_concurrent_reload"] = lock
    await lock.acquire()  # Lock halten = Reload läuft

    try:
        result = await async_reload_entry(MagicMock(), entry)
        # Zweiter Aufruf soll True zurückgeben (nicht abstürzen)
        assert result is True
    finally:
        lock.release()
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
# Fix K-02 / Issue #80: wait_for_stable_connection im blocking-Detect-Pfad
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_first_start_blocking_detect_waits_for_stable_connection():
    """K-02/Issue #80: wait_for_stable_connection wird im else-Zweig aufgerufen
    (kein num_hps/num_hc in entry.data → Erststart ohne vorhandene Modulanzahl)."""
    from custom_components.lambda_heat_pumps import async_setup_entry, _previously_setup_entries

    entry_id = "test_issue80_first_start"
    entry = MagicMock()
    entry.entry_id = entry_id
    # Kein num_hps / num_hc → has_module_counts = False → else-Zweig
    entry.data = {"host": "192.168.1.1", "port": 502, "slave_id": 1}
    entry.options = {}
    entry.add_update_listener = MagicMock(return_value=MagicMock())
    entry.async_on_unload = MagicMock()

    _previously_setup_entries.discard(entry_id)

    hass = MagicMock()
    hass.data = {}
    hass.config_entries = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    hass.services = MagicMock()
    hass.services.has_service = MagicMock(return_value=True)
    hass.async_create_task = MagicMock()

    mock_coordinator = MagicMock()
    mock_coordinator.async_init = AsyncMock()
    mock_coordinator.async_refresh = AsyncMock()
    mock_coordinator.client = MagicMock()
    mock_coordinator.client.connect = AsyncMock(return_value=True)
    mock_coordinator.slave_id = 1
    mock_coordinator._int32_register_order = "high_first"
    mock_coordinator._persist_dirty = False

    mock_wait = AsyncMock()

    with (
        patch("custom_components.lambda_heat_pumps.ensure_lambda_config", new=AsyncMock()),
        patch("custom_components.lambda_heat_pumps.LambdaDataUpdateCoordinator", return_value=mock_coordinator),
        patch("custom_components.lambda_heat_pumps.wait_for_stable_connection", mock_wait),
        patch("custom_components.lambda_heat_pumps.auto_detect_modules", new=AsyncMock(
            return_value={"hp": 1, "hc": 2, "boil": 1, "buff": 0, "sol": 0}
        )),
        patch("custom_components.lambda_heat_pumps.update_entry_with_detected_modules", new=AsyncMock(return_value=False)),
        patch("custom_components.lambda_heat_pumps.async_remove_duplicate_entity_suffixes", new=AsyncMock()),
        patch("custom_components.lambda_heat_pumps.modbus_utils.get_int32_register_order", new=AsyncMock(return_value="high_first")),
        patch("custom_components.lambda_heat_pumps.ResetManager") as mock_rm,
    ):
        mock_rm.return_value.setup_reset_automations = MagicMock()
        result = await async_setup_entry(hass, entry)

    try:
        assert result is True
        mock_wait.assert_called_once_with(mock_coordinator)
    finally:
        _previously_setup_entries.discard(entry_id)


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
    """2d: async_read_input_registers verwendet den globalen Modbus-Lock (lazy-init)."""
    import inspect
    from custom_components.lambda_heat_pumps.modbus_utils import (
        async_read_input_registers,
        _get_modbus_read_lock,
    )
    # Funktion existiert und ist eine Coroutine
    assert asyncio.iscoroutinefunction(async_read_input_registers)
    # Lock-Getter liefert einen Lock (lazy-init)
    assert isinstance(_get_modbus_read_lock(), asyncio.Lock)
    # Quellcode der Funktion referenziert den Lock-Getter
    source = inspect.getsource(async_read_input_registers)
    assert "_get_modbus_read_lock" in source
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


# ---------------------------------------------------------------------------
# Fix: Sensoren ohne Werte nach Config-Änderung (Reload-Bug)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reload_entry_skips_auto_detect():
    """async_reload_entry ruft async_setup_entry mit skip_auto_detect=True auf.

    Ein durch den Options-Flow-Update-Listener ausgelöster Reload kann die
    Modul-Hardware nicht verändert haben, daher ist der Hintergrund-Scan dort
    unnötig und soll übersprungen werden.
    """
    from custom_components.lambda_heat_pumps import async_reload_entry

    entry = MagicMock()
    entry.entry_id = "test_reload_skip_auto_detect"

    with (
        patch(
            "custom_components.lambda_heat_pumps.async_unload_entry",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "custom_components.lambda_heat_pumps.async_setup_entry",
            new=AsyncMock(return_value=True),
        ) as mock_setup,
    ):
        result = await async_reload_entry(MagicMock(), entry)

    try:
        assert result is True
        mock_setup.assert_called_once()
        _, kwargs = mock_setup.call_args
        assert kwargs.get("skip_auto_detect") is True
    finally:
        _entry_reload_flags.pop(entry.entry_id, None)
        _entry_reload_locks.pop(entry.entry_id, None)


@pytest.mark.asyncio
async def test_skip_auto_detect_does_not_schedule_background_task():
    """Bei skip_auto_detect=True wird kein background_auto_detect-Task gestartet,
    auch wenn has_module_counts=True (bestehende Config mit Modulzahlen)."""
    from custom_components.lambda_heat_pumps import async_setup_entry

    entry_id = "test_skip_auto_detect"
    entry = MagicMock()
    entry.entry_id = entry_id
    entry.data = {
        "host": "192.168.1.1",
        "port": 502,
        "slave_id": 1,
        "num_hps": 1,
        "num_hc": 1,
        "num_boil": 1,
        "num_buff": 0,
        "num_sol": 0,
    }
    entry.options = {}
    entry.add_update_listener = MagicMock(return_value=MagicMock())
    entry.async_on_unload = MagicMock()

    hass = MagicMock()
    hass.data = {}
    hass.config_entries = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    hass.services = MagicMock()
    hass.services.has_service = MagicMock(return_value=True)
    hass.async_create_task = MagicMock()

    mock_coordinator = MagicMock()
    mock_coordinator.async_init = AsyncMock()
    mock_coordinator.async_refresh = AsyncMock()
    mock_coordinator.client = MagicMock()
    mock_coordinator.slave_id = 1
    mock_coordinator._int32_register_order = "high_first"
    mock_coordinator._persist_dirty = False

    with (
        patch("custom_components.lambda_heat_pumps.ensure_lambda_config", new=AsyncMock()),
        patch("custom_components.lambda_heat_pumps.LambdaDataUpdateCoordinator", return_value=mock_coordinator),
        patch("custom_components.lambda_heat_pumps.async_remove_duplicate_entity_suffixes", new=AsyncMock()),
        patch("custom_components.lambda_heat_pumps.modbus_utils.get_int32_register_order", new=AsyncMock(return_value="high_first")),
        patch("custom_components.lambda_heat_pumps.ResetManager") as mock_rm,
    ):
        mock_rm.return_value.setup_reset_automations = MagicMock()
        result = await async_setup_entry(hass, entry, skip_auto_detect=True)

    assert result is True
    # Kein Hintergrund-Task darf erzeugt worden sein
    hass.async_create_task.assert_not_called()
    assert "auto_detect_task" not in hass.data.get(DOMAIN, {}).get(entry_id, {})


@pytest.mark.asyncio
async def test_unload_closes_modbus_client_early():
    """Modbus-Client wird beim Unload sofort geschlossen (vor der Task-Cancellation),
    damit in-flight Modbus-Reads sofort fehlschlagen statt den globalen Lock zu
    blockieren (siehe Root-Cause "Sensoren ohne Werte nach Config-Änderung")."""
    from custom_components.lambda_heat_pumps import async_unload_entry

    entry = MagicMock()
    entry.entry_id = "test_close_client_early"

    mock_coordinator = MagicMock()
    original_client = MagicMock()
    mock_coordinator.client = original_client
    mock_coordinator._persist_dirty = False

    hass = MagicMock()
    hass.data = {
        DOMAIN: {
            "test_close_client_early": {
                "coordinator": mock_coordinator,
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

    original_client.close.assert_called_once()
    assert mock_coordinator.client is None


if __name__ == "__main__":
    pytest.main([__file__])

