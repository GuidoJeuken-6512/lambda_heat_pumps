# Changelog

**Deutsche Version siehe unten / [German version see below](#deutsche-version)**

<!-- lang:en -->
## English Version

> **📚 Documentation**: A German documentation is currently being built at [https://guidojeuken-6512.github.io/lambda_heat_pumps](https://guidojeuken-6512.github.io/lambda_heat_pumps)

### [3.6.0] - 2026-10-29

**Misread energy counters are caught.** Some controllers lay out their 32-bit counters the other way round than their firmware is documented to (e.g. a `V0.0.10-3K` that needs `high_first`, [#104](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/104)). When the accumulated energy counters read as values a heat pump cannot have (below zero or above 1 GWh) but make sense with the other order, a repair **"Check the 32-bit register order"** names the setting to choose. Until then the two counters keep their last plausible value, the calculated COP is unknown and no energy is booked from them, so the long-term statistics stay clean. The FAQ now explains step by step how to clean up statistics recorded with a wrong order.

**New controller:** firmware `V1.0.2-3K`, `V1.0.7-3K` and `V1.0.8-3K` can be selected ([#100](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/100), [#144](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/144)). On V1.0.x the 20 undocumented sensors on registers 1024–1033 and 1051–1060 (hot gas, suction gas, expansion valve, capacity limits, config parameters 24/33/60, …) are no longer created: the new controller answers them with 32768 only, even while the display shows values. Existing ones show as "no longer provided" and can be deleted. `V1.1.0-3K` keeps them.

**Fewer meaningless values:** `-32768 W` in the E-Manager and inverter powers (and in the heat sink flow and request type) now reads as unknown ([#91](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/91)). Request and write registers that only hold a value while something requests one (heat pump 1015–1018, buffer 3005–3009, heating circuit room/flow request and operating mode) are disabled by default on new installations ([#132](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/132), [#143](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/143)); existing entities keep their state.

**Upgrade from 2.x:** a firmware changed later in the 2.x options dialog is now taken over instead of the one originally set up ([#82](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/82)); an unknown firmware name raises a repair instead of silently falling back to the oldest. The 2.x PV-surplus mode `entry` is offered as `pos` in the options dialog.

**Testers on 3.5.x:** if your entry was migrated with 3.5.6 or older, check *Configure → 32-bit register order* once (the new repair also points it out).

Details:
- Plausibility: a counter is implausible below 0 Wh or above 1 GWh. A heat pump's counter read with swapped words lands there unless it is still under about 15 kWh. All values reported in #104, #133 and #90 are covered by a test: swapped, each gives the value from the display. When one counter of a heat pump gives the order away, both are held, because a small counter misread can still look possible (400 kWh reads as 445 MWh). Without this, a wrong order booked 65.5 kWh for every Wh, below the 100 kWh jump guard.
- Firmware ordinals: V1.0.2-3K 9, V1.0.4-3K 10, V1.0.7-3K 11, V1.0.8-3K 12, V1.1.0-3K 13. Entries store the name, and no sensor gates on an ordinal above 8, so nothing changes for existing entries.
- #122/#85 (climate entities with a `sensor.*` id): no migration needed. Home Assistant always registers an entity under its platform's domain and only takes the object id from a proposed id; the warning came from 2.x proposing the wrong domain, which 3.5 no longer does. A test covers it.
- Test environment raised to Home Assistant 2026.10 (`pytest-homeassistant-custom-component` 0.13.373; 0.13.355 brought HA 2026.8.1, below the minimum 2026.9.0). hassfest/HACS validation and the documentation check also run on pushes to the 3.x branches.

### [3.5.7] - 2026-10-17

Fixed the 2.x→3.5 config-entry migration overriding the firmware's 32-bit register order, found via a live 2.8.6→3.5.6 upgrade on real hardware (EU10L, firmware `V1.1.0-3K`) ([Issue #133](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/133)).

#### Added
- **Firmware `V1.0.4-3K`** (new controller, SW V1.3.x) added to `FIRMWARE_CONFIG` with `reg_order: low_first`, as confirmed by a raw register dump (registers 1020/1021 = 2892/0 for 2892 Wh) in [Issue #100](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/100). Ordered by release between `V0.0.10-3K` (8) and `V1.1.0-3K`, which moves from ordinal 9 to 10. No sensor gates on 8, 9 or 10 (only `1-2`, `1-7` and `3`), and entries store the firmware name, not the ordinal, so existing entries are unaffected.

#### Fixed
- **Migration pinned `int32_register_order: high_first`**: `async_migrate_entry()` (`__init__.py`) called `options.setdefault(CONF_INT32_REGISTER_ORDER, await _async_read_register_order(hass))`, and `_async_read_register_order()` returned `DEFAULT_INT32_REGISTER_ORDER` (`high_first`) whenever `lambda_wp_config.yaml` was missing, empty, unreadable or had the key commented out. That value was stored on the entry, so the coordinator's fallback to `default_register_order(firmware)` never applied again. On `low_first` firmware (`V0.0.10-3K`, `V1.1.0-3K`) the accumulated counters read as e.g. 1,140,719,617 Wh instead of 82,942 Wh, and the 5-minute long-term statistics for that window kept the wrong values. `_async_read_register_order()` now returns `None` unless the old file sets the order explicitly, and the migration only stores an explicit value — otherwise the firmware's order applies, matching 2.8.x behaviour.
- **Options flow pre-selected `high_first`**: the register-order field defaulted to `options.get(CONF_INT32_REGISTER_ORDER, DEFAULT_INT32_REGISTER_ORDER)`, so saving the options dialog for any reason (e.g. only to enable PV surplus) pinned `high_first` on `low_first` firmware. The default is now the stored value, else `default_register_order(firmware)`, else `high_first` (`config_flow.py`).
- **External energy meter compared with the controller's register**: when a meter configured in `energy_consumption_sensors` reported `unknown`/`unavailable`, `_track_energy` fell back to the controller's register but kept the meter's last reading as the reference, so the difference between the two counters was booked as consumption (up to `MAX_ENERGY_DELTA_KWH` = 100 kWh) — and again the other way when the meter came back. The coordinator now remembers which source each reference came from (`_energy_source`); a change of source — meter out, back, or replaced — drops the reference exactly as at startup, so the first reading of the new source only sets it and the second delta is the first one counted. An outage is treated the same: a failed poll (`_forget_what_answered`) or a heat pump that did not answer (`hp<n>` in `failed`, or no operating state) resets the source, so the energy used during the gap is not booked against whatever mode the heat pump is in when it returns. Falling back to the register while the meter is out is kept.
- **Misleading help text for the firmware field**: the setup dialog said the firmware "is shown as the device's firmware and does not change what is read". It decides which sensors are created and the 32-bit register order. The text now says which version is meant (`V…-3K` from the heat pump page's status bar, not the controller's software version) and what it decides; the *Reconfigure* step shows it too (`strings.json`, `translations/*.json`).
- **Existing 3.5 installs are not corrected automatically**: an entry migrated before this fix already holds `high_first`, which cannot be told apart from a deliberate choice. Set the order once in the options dialog.
- **A register order chosen for one firmware outlived a firmware change**: `int32_register_order` is a per-entry option, and the options dialog stores it on every save, so after any save the firmware default no longer applied. Changing the firmware under *Reconfigure* (`async_step_reconfigure`) then kept the old order, e.g. `high_first` from `V0.0.9-3K` on a controller now running `V1.1.0-3K`. *Reconfigure* now drops `int32_register_order` from the options when the firmware changes (via `async_update_reload_and_abort(..., options=...)`); all other options are kept, and a change of host/port/unit id alone leaves it untouched.

#### Tests
- `tests/test_config_flow.py`: `test_an_older_entry_without_the_config_file` and `test_an_unreadable_old_config_file_falls_back_to_the_firmware_order` (renamed) now expect no stored option instead of `high_first`. Added `test_an_old_config_file_without_a_register_order` (commented-out key, `V1.1.0-3K`, asserts the counter reads 100000 Wh) and `test_an_old_config_file_set_to_high_first_is_kept`.
- `tests/test_options_flow.py`: added `test_the_register_order_offered_is_the_firmwares_own` (parametrized over `V1.1.0-3K`, `V0.0.10-3K`, `V0.0.8-3K`) and `test_a_set_register_order_is_offered_as_set`.
- `tests/test_config_flow.py`: added `test_a_firmware_change_drops_the_register_order` (V0.0.9-3K with `high_first` → V1.1.0-3K: option removed, other options kept, counter reads 100000 Wh) and `test_the_same_firmware_keeps_the_register_order`.
- `tests/test_firmware.py`: added `test_v1_0_4_sits_between_v0_0_10_and_v1_1_0`; `test_options_flow.py` parametrization extended by `V1.0.4-3K`.
- `tests/test_config_file.py`: added `test_a_meter_dropping_out_and_back_never_compares_two_counters` and `test_a_heat_pump_that_stops_answering_starts_its_counting_over`; both fail on the previous code.
- The new tests fail without the fix. Full suite: 158/158 passing.

### [3.5.6] - 2026-09-15

Fixed a data-loss bug affecting every installation upgrading from a pre-3.5 version, found and verified via a live v2.8.x→3.5.x upgrade on real hardware.

#### Fixed
- **Lifetime total counters reset to zero (or just the configured offset) across the v2.8.x→3.5.x upgrade**: `LambdaCounterSensor._restored_value()` (`sensor.py`) only ever tried Home Assistant's native restore (`RestoreSensor` extra data, then the entity's plain last state). An old integration version's entities go `unavailable` while its config entry unloads for the upgrade — exactly the moment a new version's entities try to restore from them — and `float("unavailable")` failed with no further fallback, silently starting every `_total` counter (`heating_energy_total`, `heating_thermal_energy_total`, `hot_water_energy_total`, `stby_energy_total`, and the cycling-count equivalents) over from `0.0`. `_restored_value()` now falls back to `homeassistant.components.recorder.statistics.get_last_statistics()`: since these are `state_class: TOTAL`/`TOTAL_INCREASING` sensors, Home Assistant already keeps long-term statistics for them, compiled from real values only — the last one still holds what the counter actually was, even across an `unavailable` gap in the plain state history.
- **A value recovered this way could get its configured offset added a second time**: `_applied_offset` (the amount of the configured `energy_consumption_offsets`/`cycling_offsets` already baked into a restored value) used to be read unconditionally from the last state's `applied_offset` attribute — which, like the state itself, is gone when that state was `"unavailable"`. `async_added_to_hass()` now treats a value recovered via the new statistics fallback as already including today's configured offset, so `_apply_offset()`'s delta calculation comes out to zero instead of re-applying the full offset on top.
- **A second, unrelated crash in the same change**: `YesterdayCycleSensor` (the `*_cycling_yesterday` sensors) calls the same `_restored_value()` helper, but its caller was not updated for the new return type (`_Restored`, carrying both the value and whether the source can be trusted for the offset attribute) — it kept assigning the whole object to `self._value`, and `round()`-ing a non-numeric object raised `TypeError: type _Restored doesn't define __round__ method` on every restore and again on every subsequent coordinator update, crashing entity setup and leaving these five sensors `unavailable`. Fixed to unwrap `.value` like the other caller.
- `manifest.json`: added `after_dependencies: ["recorder"]` (soft dependency — the platform starts after `recorder` when it is present, without requiring it).

#### Tests
- Added `tests/test_migration_restore.py::test_a_restart_from_unavailable_restores_from_statistics`: uses `pytest_homeassistant_custom_component`'s `recorder_mock` fixture plus `async_import_statistics()` to reproduce the exact failure — a mocked `"unavailable"` last state with no `RestoreSensor` extra data, and a long-term statistic holding the real prior value and a configured offset — and asserts the counter restores that value with the offset applied exactly once. Kept in its own file: `recorder_mock` has to resolve before `hass` does in this test harness, which conflicts with the module-wide `enable_custom_integrations` mark the other test files use.
- Added `tests/test_counters.py::test_yesterday_survives_a_restart`, covering the second bug directly (a plain restored state, no recorder involved) — reproduces the `TypeError` before the fix and passes after it.
- Full suite: 146/146 passing.
- **Verified live against real hardware** (installation `.115`, firmware `V0.0.9-3K`, upgrading from v2.8.x): captured a full before/after snapshot of all 177 `lambda_heat_pumps` entities via the ha-mcp API. Every lifetime and cycling total (`heating_energy_total`, `heating_thermal_energy_total`, `hot_water_energy_total`, `stby_energy_total`, and all five cycling totals, five of them with real configured offsets between 3.1 and 1500) survived the actual upgrade with its exact prior value and its offset applied exactly once. The `_cycling_yesterday` crash was reproduced live first (confirming the log signature above), then resolved by redeploying the fix and restarting again — no code regression this time, and the five previously-crashing sensors came back healthy.

### [3.5.5] - 2026-09-12

Fixed a register conflict reported for firmware 3+ controllers ([Issue #112](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/112)).

#### Fixed
- **Heating-circuit register 7 was modelled by two sensors with overlapping firmware ranges**: from firmware 3 on, the controller repurposes this address from the writable setpoint request (`flow_line_temperature_setpoint`) to the read-only value the controller actually acts on (`target_temp_flow_line`, added with `firmware_version=3`). `flow_line_temperature_setpoint` had no upper firmware bound, so on firmware 3+ both sensors were created against the same register — the reporter observed `flow_line_temperature_setpoint` showing no values there. `flow_line_temperature_setpoint` is now restricted to `firmware_versions=("1-2",)`, matching the reporter's own suggested fix and the range on which the register still means what its name says.

#### Tests
- Added `test_a_register_that_changed_meaning_is_not_double_modelled` in `tests/test_init.py`, covering both sides of the boundary: on `V0.0.8-3K` (firmware 6, past the repurposing) only `target_temp_flow_line` is created for HC1; on `V0.0.4-3K` (firmware 2, before it) only `flow_line_temperature_setpoint` is created — modelled after the existing `test_a_register_its_firmware_withdrew_is_not_modelled`.

### [3.5.4] - 2026-09-09

Fixed a second Home Assistant deprecation warning, surfaced by auditing the real system log of two live installations after a Home Assistant 2026.9.1 upgrade.

#### Fixed
- **`device_registry.async_get_device()` is deprecated, scheduled for removal in Home Assistant 2027.8.0**: `LambdaCoordinator.device_info()` used the identifiers-set lookup (`async_get_device(identifiers={controller})`) to find the controller device and set a sub-device's `via_device_id`. Home Assistant 2026.9 warns that device identifiers are no longer guaranteed unique across config entries and directs callers to `async_get_device_by_identifier()`, `async_get_device_by_connection()`, or `async_get_devices()` instead. Switched to `async_get_device_by_identifier(controller, entry.entry_id)`, which scopes the lookup to this config entry and so cannot be ambiguous — the same fix as the `via_device` deprecation resolved in 3.5.2 for the same underlying reason.

#### Tests
- Verified against real hardware on both live installations: the full suite (143 tests) passes unchanged; a live remove-and-recreate of the config entry (delete the entry, its devices and entities from storage, restart, recreate the entry, restart again) reproduces the identical 156 entities across 4 devices, with `via_device_id` correctly resolved on all three sub-devices; and a full end-to-end run of the actual config flow (`async_step_user` → `async_can_connect` → `async_create_entry` → `async_setup_entry`, including the real module auto-detection) against the real controller registers the same 156 entities and leaves the entry `LOADED`.

### [3.5.3] - 2026-09-06

Fixed a functional regression from 3.5.0 found via live testing against real hardware: every Modbus write used the wrong function code.

#### Fixed
- **Every Modbus write used FC06 (Write Single Register) for a single-register write; Lambda's own Modbus documentation mandates FC16 (Write Multiple Registers) for every write and does not implement FC06 at all** — it answers FC06 with Illegal Function (exception 0x01). This made every write-capable feature fail, logged or silent depending on the path: room-thermostat control (register 5004, logged every ~9s), PV-surplus export, the hot-water/heating-circuit/cooling-circuit setpoints, the flow-line offset, and the generic `write_modbus_register` service. The pre-3.5 `pymodbus`-based code never hit this, because it always wrote through `write_registers()` (FC16), even for a single register. Every `writable=True` field in `lambda_modbus/` now sets `force_fc16=True` (a flag `modbus-connection` provides for exactly this case), and the two call sites that wrote directly (`services.py`'s PV-surplus writer and the generic register-write service) now call `write_registers()` instead of `write_register()`.
- Verified live against real hardware (firmware `V0.0.8-3K`): the room-temperature write (register 5004) and a hot-water setpoint change via `climate.set_temperature` both landed correctly after the fix; before it, both failed with `Modbus Exception 0x01 for function code 0x06`.

#### Note
- No `PackedBitsField`/bit-field register exists in the current model, so the one FC06-only path inside `modbus-connection`'s `write_register_field()` (used for read-modify-write of packed bit registers, which ignores `force_fc16`) never applies here.

### [3.5.2] - 2026-09-06

Follow-up to 3.5.0: three gaps found while auditing every 2.7.x/2.8.x bugfix made on the pre-rewrite `main` branch against the rewritten codebase, to see which still applied.

#### Fixed
- **`via_device` deprecation warning on sub-devices**: `LambdaCoordinator.device_info()` still passed the legacy `via_device` (identifiers-tuple) kwarg, logging a Home Assistant removal warning (targeted for 2027.8.0) on every setup. Since 3.x requires Home Assistant ≥ 2026.9 unconditionally, it now always resolves and passes `via_device_id` (the parent device's registry id) instead — unlike the 2.8.5 fix on `main`, no HA-version gate is needed here.
- **0xFFFF ("no request"/"no external sensor") read as a real value**: the outside-air temperature (no external ambient sensor connected) and a buffer's request registers (no active request) report `0xFFFF` (-1) instead of a measurement — scaled, that looked like a plausible reading (-0.1 °C) instead of `unknown`. This sentinel is now filtered on the affected fields (`Ambient.temperature`, `Buffer.request_type`/`request_flow_line_temp_setpoint`/`request_return_line_temp_setpoint`/`request_heat_sink_temp_diff_setpoint`/`modbus_request_heating_capacity`, `HeatingCircuit.operating_mode`) — global sentinel filtering was left untouched, since -1 is a genuine value on other registers (e.g. temperature offsets).
- **Modbus reads and writes were not actually serialized**: `modbus-connection`'s own request-pacing lock only activates when a nonzero `message_spacing`/`unit_spacing` is configured on the connection — with neither set (the default), it is a no-op. The poll loop and the write timer for PV-surplus/room-temperature control run on independent schedules against the same connection, so without this the same class of transaction desync GitHub Issue #105 reported (a write logged as successful, but never actually reaching the device) could reproduce. A `message_spacing` of 50 ms is now set when the connection is built.

#### Tests
- Added a regression test asserting a second heat pump's COP, energy and cycling counters come from its own registers, independent of the first (Issue #107/#93's original symptom).
- Added a regression test combining a counter restart-restore with a changed configured offset in the same run, asserting the offset moves the total by the delta exactly once.
- Added a regression test for an implausibly large single-poll energy jump (above the existing delta ceiling) not being booked, mirroring the existing tests for a negative delta.
- Added a regression test asserting the connection is always built with a nonzero `message_spacing`.
- Strengthened the existing device-info test to assert the coordinator never hands out the deprecated `via_device` kwarg, not just the resulting `via_device_id` value.

### [3.5.0] - 2026-09-06

Adoption of a ground-up rewrite of the integration (PR #115, "fork-takeover"), replacing the `main`-branch 2.8.x codebase's Modbus layer and much of its entity code.

#### Changed
- **Modbus layer**: `pymodbus` and the hand-rolled `modbus_utils.py` wrapper are replaced by [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection) with the `tmodbus` backend. The register model is now declared declaratively per sub-system (`lambda_modbus/`), rather than as data-driven dictionaries.
- **Multi-heat-pump addressing**: heat pumps (and every other module) are addressed by an integer index and modelled as in-process objects throughout, rather than by reconstructing an `entity_id` string from the device name — the class of bug behind GitHub Issues #93/#107 (a second heat pump's sensors silently wired to the wrong source, or never found) cannot occur in this shape any more.
- **Energy/cycling counter persistence**: counters are plain Home Assistant `RestoreSensor`s with a self-tracked offset baseline; the previous coordinator-owned `cycle_energy_persist.json` file (and the restart/offset-persistence bug class fixed in 2.8.4/2.8.6 on `main`) no longer exists in this shape.
- **Minimum Home Assistant version**: now 2026.9.0 (required by `modbus-connection[tmodbus]`), enforced in `hacs.json`. Earlier Home Assistant versions are not supported by this line.

#### Upgrade note (statistics repairs)
- **Unit label change**: `hp1_volume_flow_heat_sink` and `hp1_volume_flow_energy_source` are now declared with Home Assistant's `UnitOfVolumeFlowRate` (`L/h`, `L/min`) instead of the 2.x strings `l/h` / `l/min`. The recorder cannot convert the old labels, so HA raises "unit changed" and "mean type changed" repairs (2.x stored these as `state_class: total`, 3.5 as `measurement`). The mean-type mismatch blocks new long-term statistics until the old ones are deleted; HA offers no other fix for it. Fix: in the unit repair choose "Delete all old statistic data for this entity" (or delete them under Developer Tools → Statistics), which clears both repairs. "Update the unit of the historic statistic values from 'l/h' to 'L/h', without converting." only relabels the unit and leaves the mean-type repair, so no statistics are recorded; the 2.x statistics of these two sensors cannot be kept.
- **State class removed**: code-like sensors (`*_error_number`, `request_type`, `config_parameter_24/33/50/60`) have no state class in 3.5 (`_count()` in `sensor.py`), they were `total`/`measurement` in 2.x. HA raises "state class removed" repairs; safe to ignore or delete the statistics.
- Renamed/removed 2.x entities surface as Spook "unknown entity reference" repairs in dashboards/templates.
- **`hcX_flow_line_temperature_setpoint` removed on firmware level 3+**: since 3.5.5 ([#112](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/112)) the sensor is gated to `firmware_versions=("1-2",)` (`sensor.py`), because register 5X07 is the read-only `target_temp_flow_line` from firmware level 3 on. 2.x created both entities on that firmware, so upgraders keep an orphaned `…_flow_line_temperature_setpoint` and anything referencing it breaks. No registry migration renames it automatically (different `unique_id`, different meaning). To keep the statistics chain: delete the orphaned entity, then give `…_target_temp_flow_line` the old entity_id.

#### Note
- See [3.5.2](#352---2026-09-06) above for the gaps this audit found and fixed. The [Entwickler documentation](https://guidojeuken-6512.github.io/lambda_heat_pumps/Entwickler/modbus-serialisierung/) covers the new Modbus-serialization design in detail.

### [2.6.0] - 2026-06-24

#### New Features
- **Cooling Circuit Climate Entity**: New `climate.<prefix>_hc<n>_cooling_circuit` entity per detected heating circuit, analogous to the existing `heating_circuit` climate entity. Shares the same current-temperature source (room device temperature) as `heating_circuit`, but writes its setpoint to the dedicated cooling setpoint register (offset 52, e.g. register 5052 for HC1, 5152 for HC2, …). Disabled by default — enable via the new `cooling_mode_enabled` option in the integration's Options Flow.

---

### [2.5.0] - 2026-04-16

Pure code quality and stability release — no breaking changes, no impact on `unique_id`, `entity_id`, or `sensor_id`.

#### Fixed
- **Race condition in reload flag** (K-01): Fast-path now uses `lock.locked()` (atomic) to close a TOCTOU gap in `async_reload_entry()`
- **Background auto-detection exception logging** (K-02, fixes #80): Level raised to `WARNING` with full traceback (`exc_info=True`)
- **Modbus locks bound to wrong event loop** (K-03): Lazy initialization — locks are created on first call, not at module import
- **Entity registry listener without debounce** (H-01): 250 ms debounce prevents redundant parallel mapping updates
- **Non-atomic sensor ID update** (H-02): Local copies + atomic swap eliminates inconsistent intermediate state
- **Persist data lost on shutdown** (H-03): `_persist_counters(force=True)` called on unload to flush within the debounce window
- **Climate state inconsistency on write error** (H-04): Explicit `None` check before local state update; refresh on failure
- **Fragile JSON repair logic** (M-01): Regex-based repair removed; backup-and-reset strategy for corrupted persist files
- **Modbus batch size too close to protocol limit** (M-02): Limit lowered from 120 to 100 registers (safe margin below the 125-register maximum)
- **Missing temperature range validation** (M-03): `min_temp >= max_temp` now falls back to defaults with a warning
- **Persist file missing version field** (M-04): `"version": 1` written to all new persist files

#### Code Quality
- Log levels corrected (`INFO` → `WARNING`/`DEBUG`) for connection errors and health-check results (Q-01)
- ~110 lines of hardcoded INT32 debug code for registers 1020/1022 removed (Q-02)
- Dead-code method `_generate_entity_id()` removed (Q-03)
- Log-prefix constants defined in `__init__.py` (Q-04); inline imports moved to file top (Q-05)

#### Dependencies
- `pymodbus` 3.9.2 → 3.13.0 · `packaging` ≥23.1 → ≥26.0 · `homeassistant` ≥2025.10 → ≥2026.2.3 (test)

---

### [2.4.0] - 2026-03-29
 
#### Fixed
- **Critical: Cycling offset re-applied on every cycle event**: `increment_cycling_counter()` was re-adding the full `cycling_offsets` YAML value on every detected mode change instead of once at startup. Offset logic removed from this function; sole responsibility now lies with `_apply_cycling_offset()` in `sensor.py`, which correctly uses differential tracking.
- **Mode detection for cycling counters**: Fixed shared-state bug that caused cycle events to be missed.
- **NameError in `increment_cycling_counter()`**: Operating mode transitions were detected but never counted due to a `cycling_entity` NameError.
- **Energy offsets silently ignored**: `_apply_energy_offset()` was never called from `async_added_to_hass()`, causing configured energy offsets to have no effect at HA startup.

#### Improvements
- Configuration template (`lambda_wp_config.yaml`) extended with examples for negative offsets and thermal energy offset keys.
- Migration system updated; 23 new tests added covering offset scenarios.
- Documentation updated: negative offset usage documented, stale warning banners removed.

---

### [2.3.4] - 2026-03-21
Change to the logic for detecting compressor starts (cycling): The 'compressor_unit_rating' sensor is used and is queried more frequently.

### [2.3] - 2026-03-01

> ⚠️ **Before upgrading**: Create a backup of your Home Assistant configuration. This release contains a breaking change that may alter entity IDs under certain conditions.

#### Breaking Changes
- **Name Prefix Normalization**: The configured `name_prefix` is now automatically converted to lowercase with spaces removed. 

#### New Features
- **COP Sensors** (Heating / Cooling / Hot Water): New sensors for the Coefficient of Performance — hourly, daily, monthly, and total periods. Calculated from thermal energy output and electrical consumption.
- **Thermal Energy Consumption Sensors**: Tracks heat output per heat pump — daily, monthly, total, and yesterday. Can optionally use an external heat meter as source sensor via `lambda_wp_config.yaml` (`thermal_sensor_entity_id`).
- **Flow Line Temperature Setpoint Sensor**: New sensor `hp_flow_line_temperature_setpoint` for the calculated flow temperature target value.
- **Compressor Start Cycling Yesterday**: New sensor `compressor_start_cycling_yesterday` for yesterday's compressor start count.

#### Fixed
- **Compressor Start Cycle Counter**: Counter now triggers on HP-State `2` (RESTART-BLOCK) instead of `5` (START COMPRESSOR). RESTART-BLOCK is the lockout state entered after a completed compressor run — counting here means counting completed cycles, not started ones.
- **Entity Duplicate Cleanup**: Sensors with `config_parameter_` in their name were falsely detected as HA duplicates by the `_\d+$` regex (e.g. `config_parameter_24` ends in `_24`). These sensors are now skipped in both cleanup passes.
- **Energy Consistency**: Daily, monthly, and yearly energy values are now validated on restore and reset — a previous-period value can never exceed the current total, preventing negative consumption differences.
- **Reset Sequence**: Yesterday sensors are now updated before the daily counter reset, ensuring `_yesterday` always reflects the actual prior-day value.
- **Energy Calculation**: Daily/monthly/yearly deltas now read baseline values directly from registered HA entities instead of internal variables, avoiding inconsistencies after reloads.
- **Modbus int16 Conversion**: Fixed signed-to-unsigned conversion for 16-bit registers (Two's Complement). New helper `clamp_to_int16` prevents overflow.
- **Room Thermostat Offset**: Corrected configurable offset range and Modbus conversion for signed values.
- **Maximum Boiler Temperature**: Removed from sensor templates — it reads the same Modbus register as `target_high_temperature`.

#### Improvements
- **Internal Refactoring**: `const.py` split into three focused modules (`const_base.py`, `const_sensor.py`, `const_calculated_sensors.py`); per-entry reload locks replacing a single global lock; f-string logging replaced with HA-compliant `%s` format; redundant `_unique_id` attributes removed from sensor classes.

---

### [2.1] - 2025-12-20

#### New Features
- **Flow Line Offset Number Entity**: Added bidirectional Modbus-synchronized Number entity for flow line offset temperature adjustment
  - Automatically created for each heating circuit (HC1, HC2, etc.)
  - Range: -10.0°C to +10.0°C with 0.1°C step size
  - Reads current value from Modbus register and writes changes directly back
  - Appears in device configuration alongside heating curve support points
  - Modbus Register: Register 50 (relative to heating circuit base address)

#### Fixed
- **Heating Curve Validation**: Fixed validation logic to check both conditions independently
  - Changed `elif` to `if` to ensure both validation checks are performed
  - Now reports all validation problems when multiple heating curve values are misconfigured
  - Previously only the first issue was reported when all three temperature points were in wrong order
  - Fixed issue when all three heating curve points have identical values (Issue #48)

- **Hot Water Temperature Limits**: Adjusted minimum/maximum values for hot water to Lambda standard (25/65°C) (Issue #50)
- **Eco Mode in Heating Curve**: Added eco temperature reduction feature for heating circuits (Issue #51)
  - New Number entity `eco_temp_reduction` per heating circuit with range -10.0 to 0.0°C (default: -1.0°C)
  - Automatically reduces calculated flow temperature when heating circuit is in ECO mode (operating_state = 1)
  - Integrated into heating curve calculation alongside flow line offset and room thermostat adjustments 


### [2.0.0] - 2025-01-XX

#### New Features
- **Device Hierarchy**: Implemented separation into main devices and sub-devices for better organization and clearer entity structure
- **Multilingual Support**: Added comprehensive translations in German and English for all entity names, ensuring proper localization support
- **Heating Curve Calculation**: Implemented intelligent heating curve calculation with three support points (cold, mid, warm) and automatic flow temperature calculation based on outside temperature
  - **Cold Point**: Defines the heating curve at low outside temperatures
  - **Mid Point**: Defines the heating curve at medium outside temperatures
  - **Warm Point**: Defines the heating curve at high outside temperatures
  - **New Sensor**: `heating_curve_flow_line_temperature_calc` automatically calculates the optimal flow temperature based on current outside temperature and the configured support points
- **Compressor Start Cycling Sensor**: Added new cycling sensor for tracking compressor start events
  - **Total Sensor**: `compressor_start_cycling_total` - Tracks total compressor starts since installation
  - **Daily Sensor**: `compressor_start_cycling_daily` - Tracks daily compressor starts (resets at midnight)
  - **2H Sensor**: `compressor_start_cycling_2h` - Tracks 2-hour compressor starts (resets every 2 hours)
  - **4H Sensor**: `compressor_start_cycling_4h` - Tracks 4-hour compressor starts (resets every 4 hours)
  - **Monthly Sensor**: `compressor_start_cycling_monthly` - Tracks monthly compressor starts (resets on 1st of month)
  - **Flank Detection**: Uses HP_STATE register (1002) instead of HP_OPERATING_STATE, detecting "START COMPRESSOR" state (value 5)

#### Improvements
- Enhanced entity naming with proper device and sub-device prefixes
- Improved translation loading and application for all entity types
- Better integration with Home Assistant's translation system
- **Write Interval Optimization**: Reduced write interval from 41 seconds to 9 seconds for faster response times
- **External Energy Sensor Validation**: Enhanced validation of external energy consumption sensors with Entity Registry fallback check, allowing sensors to be accepted even when not yet available in state during startup. Runtime retry mechanism handles temporary unavailability gracefully.

### [1.4.3] - 2025-11-04
#### Fixed
- **ISSUE 39** Modbus batch reads incorrectly detect errors: Faster switching to individual reads so that correct sensors become available again
- **ISSUE 22** Additional logging added to identify errors
- **Unit of sensor volume_flow_heat_sink corrected** to l/h

### [1.4.2] - 2025-10-24

#### Fixed
- Fixed failing tests by replacing Mock objects with proper test implementations
- Improved test reliability and reduced false failures
- Fixed integration reload errors
- Fixed `default_config` in `load_lambda_config()` to include all required keys (`energy_consumption_sensors`, `energy_consumption_offsets`, `modbus`)

#### Changed
- **Register Order Values**: Changed configuration values from `"big"`/`"little"` to `"high_first"`/`"low_first"` for better clarity
  - Old values (`big`/`little`) are still supported with automatic conversion
  - New default is `"high_first"` (replaces `"big"`)
  - Improved documentation and comments to clarify register order vs. byte endianness

#### Improvements
- Test optimization: 57 tests successfully repaired and optimized
- Gitignore correction: Fixed .gitignore for proper inclusion of all docs subdirectories
- Service documentation: Created comprehensive documentation for future service optimizations
- **Service Scheduler Optimization**: Implemented intelligent service scheduler that only activates when PV-Surplus or Room Thermostat control options are enabled, significantly reducing resource usage when services are not needed

---

### [1.4.1] - 2025-10-21

#### New Features
- **Massive Performance Improvements**: Dramatically improved integration startup and update performance
  - **Startup Time**: Reduced by ~72% (from ~7.3s to ~2.05s) through intelligent background auto-detection
  - **Update Cycles**: Reduced by ~50% (from >30s to <15s) through global register deduplication
  - **Modbus Traffic**: Reduced by ~80% through elimination of duplicate register reads
- **Intelligent Auto-Detection**: Implemented background auto-detection for existing configurations, eliminating startup delays while maintaining hardware change detection
- **Global Register Cache**: Added comprehensive register deduplication system that eliminates duplicate Modbus reads across all modules (HP, Boiler, Buffer, Solar, HC)
- **Optimized Batch Reading**: Improved Modbus batch reading with larger consecutive register ranges and reduced individual read thresholds
- **Parallel Template Setup**: Template sensors now load in background tasks, preventing startup blocking
- **Persist I/O Optimization**: Added debouncing and dirty-flag mechanisms to reduce unnecessary file writes
- **Connection Health Optimization**: Reduced connection timeout from 5s to 2s for faster failure detection

#### Improvements
- **Enhanced Energy Tracking**: Improved energy consumption tracking with automatic unit conversion (Wh/kWh/MWh)
- **Robust Sensor Handling**: Added retry mechanism for sensor availability during startup
- **Comprehensive Logging**: Added detailed logging for sensor change detection and energy calculations
- **Monthly & Yearly Power Consumption Sensors**: Added monthly and yearly energy consumption sensors for long-term tracking
- **Service Setup Optimization**: Services are now set up only once, regardless of the number of entries
- **Configuration Flow Improvements**: Enhanced validation for existing connections and IP addresses, removed obsolete modules
- **Generalized Reset Functions**: Implemented generalized reset functions for all sensor types with extended tests
- **Code Cleanup**: Cleaned up const.py, YAML templates, and general code structure
- **Documentation Updates**: Updated documentation and created program flow diagrams

#### Technical Changes
- Automatic `lambda_wp_config.yaml` creation from `LAMBDA_WP_CONFIG_TEMPLATE`
- Integration of config file creation into existing migration pipeline
- Enhanced error handling in `LambdaDataUpdateCoordinator`
- Improved sensor attribute loading with better error recovery

---

### [1.4.0] - 2025-10-05

#### New Features
- **Energy Consumption Sensors by Operating Mode**: Added configurable energy consumption sensors that track energy usage by operating mode (heating, hot water, cooling, defrost) with customizable source sensors (Issue #21)
- **Register Order Configuration**: Added register order configuration in `lambda_wp_config.yaml` for proper 32-bit value interpretation from multiple 16-bit registers (Issue #22)
- **Sensor Change Detection**: Implemented automatic detection of energy sensor changes with intelligent handling of sensor value transitions to prevent incorrect energy consumption calculations

#### Bug Fixes
- **Register Order Fix**: Fixed register order issues for 32-bit values with initial quick fix approach (Issue #22)
- **Daily Sensor Reset Automation**: Fixed errors in automation for resetting daily sensors (Issue #29)
- **Auto-Detection**: Fixed auto-detection not recognizing existing configurations (IP/Port/SlaveId)
- **DCHP Discovery**: Fixed DCHP discovery error messages
- **HASS Validation**: Fixed Home Assistant validation errors
- **Daily Reset Function**: Repaired daily reset function for sensors

#### Improvements
- **Enhanced Energy Tracking**: Improved energy consumption tracking with automatic unit conversion (Wh/kWh/MWh)
- **Robust Sensor Handling**: Added retry mechanism for sensor availability during startup
- **Comprehensive Logging**: Added detailed logging for sensor change detection and energy calculations
- **Monthly & Yearly Power Consumption Sensors**: Added monthly and yearly energy consumption sensors for long-term tracking
- **Service Setup Optimization**: Services are now set up only once, regardless of the number of entries
- **Configuration Flow Improvements**: Enhanced validation for existing connections and IP addresses, removed obsolete modules
- **Generalized Reset Functions**: Implemented generalized reset functions for all sensor types with extended tests
- **Code Cleanup**: Cleaned up const.py, YAML templates, and general code structure
- **Documentation Updates**: Updated documentation and created program flow diagrams

#### Technical Changes
- Automatic `lambda_wp_config.yaml` creation from `LAMBDA_WP_CONFIG_TEMPLATE`
- Integration of config file creation into existing migration pipeline
- Enhanced error handling in `LambdaDataUpdateCoordinator`
- Improved sensor attribute loading with better error recovery

---

### [1.3.0] - 2025-01-03

#### New Features
- **New 2H/4H Cycling Sensors**: Added 2-hour and 4-hour cycling sensors for detailed heat pump operation monitoring
- **Enhanced Cycling Offsets**: Improved cycling counter offset functionality for total sensor adjustments when replacing heat pumps or resetting counters
- **Robust Flank Detection**: Implemented robust flank detection for heat pump operating states with improved reliability
- **Dynamic Error Handling**: Enhanced batch read error handling with automatic fallback to individual reads after threshold failures
- **Cycling Warnings Management**: Added cycling warnings suppression logic to manage entity registration issues

#### Bug Fixes
- **Configuration File Creation**: Fixed issue where `lambda_wp_config.yaml` was not automatically created from template, ensuring proper configuration setup
- **Daily Cycling Sensors**: Fixed daily cycling sensors now properly displaying values and functioning correctly

#### Improvements
- **Coordinator Initialization**: Enhanced coordinator initialization process with improved error handling
- **Debug Logging**: Added comprehensive debug logs for tracking offset changes and system behavior
- **Documentation**: Updated documentation to reflect new functions and configuration options
- **Modbus Configuration**: Extended Lambda Heat Pumps integration with specific Modbus configurations

#### Technical Changes
- Automatic `lambda_wp_config.yaml` creation from `LAMBDA_WP_CONFIG_TEMPLATE`
- Integration of config file creation into existing migration pipeline
- Enhanced error handling in `LambdaDataUpdateCoordinator`
- Improved sensor attribute loading with better error recovery

---

### [1.2.2] - 2025-08-18

#### ⚠️ BREAKING CHANGES IN THIS RELEASE - BACKUP REQUIRED

This release contains significant changes to the Entity Registry and sensor naming conventions. **Please create a complete backup of your Home Assistant configuration before updating.**

**What will change:**
- Automatic migration of existing sensor entities to prevent duplicates
- Updated unique_id format for better consistency
- Sensor filtering based on firmware compatibility

**After migration, please verify:**
- Sensor names and long-term data are preserved correctly
- No duplicate entities exist in your system
- All sensors are functioning as expected
- **Automations may need to be updated** if they reference sensor entities that were migrated

**A Copy of the core.config_entries, core.device_registry and core.entity_registry is created before the sensors are migrated and can be copied back from the /lambda_heat_pumps folder to the hidden .storage folder to undo the changes. However, version 1.0.9 of the integration must then be reinstalled for the system to work properly.**

---

### [1.1.0] - 2025-08-03

#### Major Changes
- **Switch to asynchronous Modbus clients** - Complete migration from synchronous to asynchronous Modbus communication for better compatibility with other integrations
- **Runtime API compatibility** - Automatic detection and adaptation to different pymodbus versions (1.x, 2.x, 3.x)
- **Performance improvements** - Non-blocking Modbus operations for better system performance
- **Entity Registry Migration** - Automatic migration of general and climate sensors to prevent duplicate entities with consistent unique_id format

#### Added
- Asynchronous Modbus wrapper functions in `modbus_utils.py`
- Runtime API compatibility detection for pymodbus versions
- Comprehensive error handling for async Modbus operations
- Extended cycling counters with daily, yesterday and total values for all operating modes

#### Changed
- All Modbus operations migrated to `AsyncModbusTcpClient`
- Coordinator, config_flow, services, and climate modules updated for async operations
- Removed `async_add_executor_job` wrappers in favor of direct async calls

#### Fixed
- RuntimeWarning: "coroutine was never awaited" in automation setup
- Callback function implementation corrected
- Code quality improvements and linting issues resolved
- Duplicate sensor entities with "_2" suffix after updates
- Inconsistent unique_id format for general and climate sensors
- Sensor filtering based upon firmware settings

#### Removed
- **`use_legacy_modbus_names` configuration option** - This option has been removed as it became obsolete after the automatic migration of all sensors to the legacy naming scheme (`use_legacy=true`). All existing installations will automatically use the legacy naming format.

---

### [1.0.9] - 2024-12-19

#### Added
- Compatibility with pymodbus >= 3.6.0
- Counters for heat pump cycling by operating mode
- Extended statistics for different operating modes

#### Changed
- Updated to new pymodbus API (3.x)
- Removed redundant parameters in `read_holding_registers` calls
- Synchronous `connect()` calls instead of asynchronous
- Code style improvements (flake8-compatible)

#### Fixed
- Import errors in all modules fixed
- Whitespace issues resolved
- HACS validation errors corrected
- Manifest keys properly sorted

---

### [1.0.0] - Initial Release

#### Added
- First version of Lambda Heat Pumps Integration
- Modbus communication for heat pumps
- Cycle counter detection
- Climate entity for heat pump control

---
<!-- /lang:en -->
## Deutsche Version {#deutsche-version}


<!-- lang:de -->

> **📚 Dokumentation**: Eine deutsche Dokumentation wird derzeit unter [https://guidojeuken-6512.github.io/lambda_heat_pumps](https://guidojeuken-6512.github.io/lambda_heat_pumps) aufgebaut

### [3.6.0] - 2026-10-29

**Falsch gelesene Energiezähler werden erkannt.** Manche Steuerungen legen ihre 32-Bit-Zähler andersherum ab, als es für ihre Firmware dokumentiert ist (z. B. eine `V0.0.10-3K`, die `high_first` braucht, [#104](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/104)). Liefern die akkumulierten Energiezähler Werte, die eine Wärmepumpe nicht haben kann (unter null oder über 1 GWh), und sind sie mit der anderen Reihenfolge plausibel, erscheint die Reparatur **„32-Bit-Registerreihenfolge prüfen“** mit der passenden Einstellung. Bis dahin behalten die beiden Zähler ihren letzten plausiblen Wert, der berechnete COP ist unbekannt, und es wird keine Energie aus ihnen gezählt. Die Langzeitstatistik bleibt dadurch sauber. Die FAQ beschreibt jetzt Schritt für Schritt, wie man eine mit falscher Reihenfolge aufgezeichnete Statistik bereinigt.

**Neue Steuerung:** Die Firmware `V1.0.2-3K`, `V1.0.7-3K` und `V1.0.8-3K` ist auswählbar ([#100](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/100), [#144](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/144)). Auf V1.0.x werden die 20 undokumentierten Sensoren auf den Registern 1024–1033 und 1051–1060 (Heißgas, Sauggas, Expansionsventil, Leistungsgrenzen, Config-Parameter 24/33/60 …) nicht mehr angelegt: Die neue Steuerung liefert dort nur 32768, auch wenn das Display Werte zeigt. Vorhandene erscheinen als „nicht mehr bereitgestellt“ und können gelöscht werden. `V1.1.0-3K` behält sie.

**Weniger sinnlose Werte:** `-32768 W` bei den Leistungen von E-Manager und Inverter (sowie beim Volumenstrom und beim Anforderungstyp) wird jetzt als „unbekannt“ angezeigt ([#91](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/91)). Anforderungs- und Schreibregister, die nur bei einer aktiven Anforderung einen Wert haben (Wärmepumpe 1015–1018, Puffer 3005–3009, Raum-/Vorlauf-Anforderung und Betriebsart des Heizkreises), sind bei neuen Installationen standardmäßig deaktiviert ([#132](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/132), [#143](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/143)); vorhandene Entitäten behalten ihren Zustand.

**Update von 2.x:** Eine später im 2.x-Optionsdialog geänderte Firmware wird jetzt übernommen statt der ursprünglich eingerichteten ([#82](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/82)); ein unbekannter Firmware-Name erzeugt eine Reparatur, statt still auf die älteste zurückzufallen. Der 2.x-PV-Modus `entry` wird im Optionsdialog als `pos` angeboten.

**Tester mit 3.5.x:** Wurde Ihr Eintrag mit 3.5.6 oder älter migriert, prüfen Sie einmal *Konfigurieren → 32-Bit-Registerreihenfolge* (die neue Reparatur weist ebenfalls darauf hin).

Details:
- Plausibilität: Ein Zähler ist unplausibel unter 0 Wh oder über 1 GWh. Ein mit vertauschten Wörtern gelesener Zähler landet dort, solange er nicht unter etwa 15 kWh liegt. Alle in #104, #133 und #90 gemeldeten Werte sind per Test abgedeckt: Getauscht ergibt jeder den Wert vom Display. Verrät ein Zähler einer Wärmepumpe die Reihenfolge, werden beide angehalten, weil ein kleiner Zähler falsch gelesen noch möglich aussehen kann (400 kWh werden zu 445 MWh). Ohne das buchte eine falsche Reihenfolge pro Wh 65,5 kWh, unter dem 100-kWh-Sprungfilter.
- Firmware-Ordinals: V1.0.2-3K 9, V1.0.4-3K 10, V1.0.7-3K 11, V1.0.8-3K 12, V1.1.0-3K 13. Einträge speichern den Namen, und kein Sensor prüft auf ein Ordinal über 8; für bestehende Einträge ändert sich nichts.
- #122/#85 (Klima-Entitäten mit `sensor.*`-ID): keine Migration nötig. Home Assistant registriert eine Entität immer unter der Domain ihrer Plattform und übernimmt aus einer vorgeschlagenen ID nur den Objektteil; die Warnung kam vom falschen Vorschlag in 2.x, den 3.5 nicht mehr macht. Ein Test sichert das ab.
- Testumgebung auf Home Assistant 2026.10 angehoben (`pytest-homeassistant-custom-component` 0.13.373; 0.13.355 brachte HA 2026.8.1, unter dem Minimum 2026.9.0). hassfest/HACS-Prüfung und Doku-Check laufen auch bei Pushes auf die 3.x-Branches.

### [3.5.7] - 2026-10-17

Die Config-Entry-Migration 2.x→3.5 hat die 32-Bit-Registerreihenfolge der Firmware überschrieben, gefunden bei einem echten Upgrade 2.8.6→3.5.6 auf realer Hardware (EU10L, Firmware `V1.1.0-3K`) ([Issue #133](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/133)).

#### Hinzugefügt
- **Firmware `V1.0.4-3K`** (neue Steuerung, SW V1.3.x) in `FIRMWARE_CONFIG` aufgenommen, mit `reg_order: low_first`, bestätigt durch einen Rohregister-Dump (Register 1020/1021 = 2892/0 für 2892 Wh) in [Issue #100](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/100). Nach Erscheinungsdatum zwischen `V0.0.10-3K` (8) und `V1.1.0-3K` eingeordnet, das von Ordnungszahl 9 auf 10 rückt. Kein Sensor prüft auf 8, 9 oder 10 (nur `1-2`, `1-7` und `3`), und Einträge speichern den Firmware-Namen, nicht die Zahl – bestehende Einträge sind nicht betroffen.

#### Behoben
- **Migration schrieb `int32_register_order: high_first` fest**: `async_migrate_entry()` (`__init__.py`) rief `options.setdefault(CONF_INT32_REGISTER_ORDER, await _async_read_register_order(hass))` auf, und `_async_read_register_order()` lieferte `DEFAULT_INT32_REGISTER_ORDER` (`high_first`), sobald `lambda_wp_config.yaml` fehlte, leer oder unlesbar war oder der Schlüssel auskommentiert war. Dieser Wert landete im Entry, und der Fallback des Coordinators auf `default_register_order(firmware)` griff nie mehr. Bei `low_first`-Firmware (`V0.0.10-3K`, `V1.1.0-3K`) lasen sich die akkumulierten Zähler z. B. als 1.140.719.617 Wh statt 82.942 Wh, und die 5-Minuten-Langzeitstatistik dieses Zeitfensters behielt die falschen Werte. `_async_read_register_order()` gibt jetzt `None` zurück, solange die alte Datei die Reihenfolge nicht ausdrücklich setzt, und die Migration speichert nur einen ausdrücklichen Wert — sonst gilt die Reihenfolge der Firmware, wie in 2.8.x.
- **Options-Flow schlug `high_first` vor**: Das Feld für die Registerreihenfolge hatte den Default `options.get(CONF_INT32_REGISTER_ORDER, DEFAULT_INT32_REGISTER_ORDER)`. Wer den Options-Dialog aus irgendeinem Grund speicherte (z. B. nur um PV-Überschuss zu aktivieren), schrieb auf `low_first`-Firmware `high_first` fest. Der Default ist jetzt der gespeicherte Wert, sonst `default_register_order(firmware)`, sonst `high_first` (`config_flow.py`).
- **Externer Energiezähler mit dem Lambda-Register verrechnet**: Meldete ein in `energy_consumption_sensors` eingetragener Zähler `unknown`/`unavailable`, fiel `_track_energy` auf das Lambda-Register zurück, behielt aber den letzten Stand des externen Zählers als Ausgangswert. Der Unterschied zwischen beiden Zählern wurde so als Verbrauch gebucht (bis `MAX_ENERGY_DELTA_KWH` = 100 kWh), und beim Wiedererscheinen des Zählers noch einmal in die andere Richtung. Der Coordinator merkt sich jetzt, aus welcher Quelle jeder Ausgangswert stammt (`_energy_source`); ein Quellenwechsel — Zähler fällt aus, kommt zurück oder wird getauscht — verwirft den Ausgangswert wie beim Start: Die erste Ablesung der neuen Quelle setzt ihn nur, erst die zweite Differenz wird gezählt. Ein Ausfall wird genauso behandelt: Eine fehlgeschlagene Abfrage (`_forget_what_answered`) oder eine Wärmepumpe, die nicht antwortet (`hp<n>` in `failed` oder kein Betriebszustand), setzt die Quelle zurück, sodass der Verbrauch während der Lücke nicht der Betriebsart beim Wiedererscheinen zugeschlagen wird. Der Rückfall auf das Register während eines Zählerausfalls bleibt erhalten.
- **Irreführender Hilfetext zum Feld Firmware**: Der Einrichtungsdialog sagte, die Firmware „wird als Firmware des Geräts angezeigt und ändert nichts am Auslesen“. Sie bestimmt aber die angelegten Sensoren und die 32-Bit-Registerreihenfolge. Der Text nennt jetzt, welche Version gemeint ist (`V…-3K` aus der Statuszeile der Wärmepumpen-Seite, nicht die Software-Version der Steuerung) und was sie bestimmt; der Schritt *Neu konfigurieren* zeigt ihn ebenfalls (`strings.json`, `translations/*.json`).
- **Bestehende 3.5-Installationen werden nicht automatisch korrigiert**: Ein vor diesem Fix migrierter Eintrag hat bereits `high_first` gespeichert, was sich nicht von einer bewussten Wahl unterscheiden lässt. Die Reihenfolge einmal im Options-Dialog setzen.
- **Eine für eine Firmware gewählte Registerreihenfolge überlebte den Firmwarewechsel**: `int32_register_order` ist eine Option pro Eintrag, und der Options-Dialog speichert sie bei jedem Speichern; danach griff der Firmware-Standard nicht mehr. Ein Firmwarewechsel unter *Neu konfigurieren* (`async_step_reconfigure`) behielt dann die alte Reihenfolge, z. B. `high_first` von `V0.0.9-3K` auf einer Steuerung, die jetzt `V1.1.0-3K` läuft. *Neu konfigurieren* entfernt `int32_register_order` jetzt bei einem Firmwarewechsel aus den Options (über `async_update_reload_and_abort(..., options=...)`); alle anderen Options bleiben erhalten, und eine reine Änderung von Host/Port/Slave-ID lässt sie unangetastet.

#### Tests
- `tests/test_config_flow.py`: `test_an_older_entry_without_the_config_file` und `test_an_unreadable_old_config_file_falls_back_to_the_firmware_order` (umbenannt) erwarten jetzt keine gespeicherte Option statt `high_first`. Neu: `test_an_old_config_file_without_a_register_order` (auskommentierter Schlüssel, `V1.1.0-3K`, prüft den Zählerwert 100000 Wh) und `test_an_old_config_file_set_to_high_first_is_kept`.
- `tests/test_options_flow.py`: neu `test_the_register_order_offered_is_the_firmwares_own` (parametrisiert über `V1.1.0-3K`, `V0.0.10-3K`, `V0.0.8-3K`) und `test_a_set_register_order_is_offered_as_set`.
- `tests/test_config_flow.py`: neu `test_a_firmware_change_drops_the_register_order` (V0.0.9-3K mit `high_first` → V1.1.0-3K: Option entfernt, übrige Options erhalten, Zähler liest 100000 Wh) und `test_the_same_firmware_keeps_the_register_order`.
- `tests/test_firmware.py`: neu `test_v1_0_4_sits_between_v0_0_10_and_v1_1_0`; Parametrisierung in `test_options_flow.py` um `V1.0.4-3K` erweitert.
- `tests/test_config_file.py`: neu `test_a_meter_dropping_out_and_back_never_compares_two_counters` und `test_a_heat_pump_that_stops_answering_starts_its_counting_over`; beide schlagen mit dem vorherigen Code fehl.
- Die neuen Tests schlagen ohne den Fix fehl. Gesamte Suite: 158/158 bestanden.

### [3.5.6] - 2026-09-15

Einen Datenverlust-Bug behoben, der jede Installation beim Upgrade von einer Vor-3.5-Version betrifft — gefunden und verifiziert über einen echten v2.8.x→3.5.x-Upgrade auf realer Hardware.

#### Behoben
- **Lifetime-Gesamtzähler fielen beim v2.8.x→3.5.x-Upgrade auf null (bzw. nur den konfigurierten Offset) zurück**: `LambdaCounterSensor._restored_value()` (`sensor.py`) hat sich ausschließlich auf Home Assistants natives Restore verlassen (`RestoreSensor`-Extradaten, dann der letzte eigene State der Entity). Beim Upgrade werden die Entities der alten Version kurz `unavailable`, während ihr Config-Entry entladen wird — genau der Moment, in dem die neue Version versucht, von ihnen wiederherzustellen — und `float("unavailable")` schlug ohne weiteren Fallback fehl, wodurch jeder `_total`-Zähler (`heating_energy_total`, `heating_thermal_energy_total`, `hot_water_energy_total`, `stby_energy_total` sowie die Zyklus-Zähler-Pendants) stillschweigend wieder bei `0.0` begann. `_restored_value()` greift jetzt zusätzlich auf `homeassistant.components.recorder.statistics.get_last_statistics()` zurück: Da es sich um `state_class: TOTAL`/`TOTAL_INCREASING`-Sensoren handelt, führt Home Assistant für sie ohnehin Langzeitstatistik, ausschließlich aus echten Werten kompiliert — der letzte Eintrag hält weiterhin, was der Zähler tatsächlich war, auch über eine `unavailable`-Lücke im reinen State-Verlauf hinweg.
- **Ein so geretteter Wert konnte den konfigurierten Offset ein zweites Mal aufaddiert bekommen**: `_applied_offset` (wie viel vom konfigurierten `energy_consumption_offsets`/`cycling_offsets` bereits in einem restaurierten Wert steckt) wurde bisher bedingungslos aus dem `applied_offset`-Attribut des letzten States gelesen — das genau wie der State selbst verschwunden ist, wenn dieser State `"unavailable"` war. `async_added_to_hass()` behandelt einen über den neuen Statistik-Fallback geretteten Wert jetzt so, als sei der heute konfigurierte Offset bereits enthalten, sodass `_apply_offset()`s Differenzrechnung auf null kommt, statt den vollen Offset nochmal draufzuaddieren.
- **Ein zweiter, unabhängiger Absturz in derselben Änderung**: `YesterdayCycleSensor` (die `*_cycling_yesterday`-Sensoren) ruft dieselbe `_restored_value()`-Hilfsfunktion auf, ihr Aufrufer war aber nicht auf den neuen Rückgabetyp umgestellt (`_Restored`, der sowohl den Wert als auch trägt, ob die Quelle für das Offset-Attribut vertrauenswürdig ist) — er wies weiterhin das gesamte Objekt `self._value` zu, und das `round()` eines nicht-numerischen Objekts warf bei jeder Wiederherstellung und danach bei jedem weiteren Coordinator-Update `TypeError: type _Restored doesn't define __round__ method`, was den Entity-Aufbau abstürzen ließ und diese fünf Sensoren `unavailable` beließ. Behoben durch Entpacken von `.value`, wie beim anderen Aufrufer.
- `manifest.json`: `after_dependencies: ["recorder"]` ergänzt (weiche Abhängigkeit — die Plattform startet nach `recorder`, falls vorhanden, ohne es vorauszusetzen).

#### Tests
- Neuer Test `tests/test_migration_restore.py::test_a_restart_from_unavailable_restores_from_statistics`: nutzt die `recorder_mock`-Fixture von `pytest_homeassistant_custom_component` plus `async_import_statistics()`, um den genauen Fehlerfall nachzustellen — ein simulierter `"unavailable"`-letzter-State ohne `RestoreSensor`-Extradaten, und eine Langzeitstatistik mit dem echten vorherigen Wert plus einem konfigurierten Offset — und prüft, dass der Zähler diesen Wert mit genau einmal angewendetem Offset restauriert. In eigener Datei belassen: `recorder_mock` muss in diesem Test-Harness vor `hass` aufgelöst werden, was mit dem modulweiten `enable_custom_integrations`-Mark der anderen Testdateien kollidiert.
- Neuer Test `tests/test_counters.py::test_yesterday_survives_a_restart`, deckt den zweiten Bug direkt ab (ein einfacher restaurierter State, kein Recorder nötig) — reproduziert den `TypeError` vor dem Fix und läuft danach grün.
- Volle Suite: 146/146 grün.
- **Gegen echte Hardware verifiziert** (Installation `.115`, Firmware `V0.0.9-3K`, Upgrade von v2.8.x): vollständigen Vorher/Nachher-Abzug aller 177 `lambda_heat_pumps`-Entities über die ha-mcp-API gezogen. Jeder Lifetime- und Zyklus-Zähler (`heating_energy_total`, `heating_thermal_energy_total`, `hot_water_energy_total`, `stby_energy_total` sowie alle fünf Zyklus-Totals, fünf davon mit echten konfigurierten Offsets zwischen 3,1 und 1500) hat den echten Upgrade mit exakt seinem vorherigen Wert und genau einmal angewendetem Offset überstanden. Der `_cycling_yesterday`-Absturz wurde zuerst live reproduziert (bestätigt die Log-Signatur oben), dann durch Redeploy des Fixes und erneuten Neustart behoben — diesmal keine Regression, und die fünf zuvor abstürzenden Sensoren liefen danach wieder sauber.

### [3.5.4] - 2026-09-09

Eine weitere Home-Assistant-Deprecation-Warnung behoben, gefunden bei der Auswertung der echten System-Logs zweier laufender Installationen nach einem Update auf Home Assistant 2026.9.1.

#### Behoben
- **`device_registry.async_get_device()` ist deprecated und wird in Home Assistant 2027.8.0 entfernt**: `LambdaCoordinator.device_info()` nutzte den Identifiers-Set-Lookup (`async_get_device(identifiers={controller})`), um das Controller-Gerät zu finden und `via_device_id` eines Untergeräts zu setzen. Home Assistant 2026.9 warnt, dass Geräte-Identifier nicht mehr über Config-Entries hinweg eindeutig garantiert sind, und verweist stattdessen auf `async_get_device_by_identifier()`, `async_get_device_by_connection()` oder `async_get_devices()`. Umgestellt auf `async_get_device_by_identifier(controller, entry.entry_id)`, was den Lookup auf diesen Config-Entry eingrenzt und damit nicht mehrdeutig sein kann — derselbe Fix aus demselben Grund wie die in 3.5.2 behobene `via_device`-Deprecation.

#### Tests
- Gegen echte Hardware auf beiden laufenden Installationen verifiziert: Die volle Testsuite (143 Tests) läuft unverändert durch; ein Live-Entfernen-und-Neuanlegen des Config-Entry (Entry, Geräte und Entities aus der Storage löschen, neu starten, Entry neu anlegen, erneut neu starten) reproduziert exakt dieselben 156 Entities auf 4 Geräten, mit korrekt aufgelöster `via_device_id` bei allen drei Untergeräten; und ein vollständiger End-to-End-Durchlauf des echten Config-Flows (`async_step_user` → `async_can_connect` → `async_create_entry` → `async_setup_entry`, inklusive echter automatischer Modul-Erkennung) gegen den echten Controller registriert dieselben 156 Entities und hinterlässt den Entry im Zustand `LOADED`.

### [3.5.3] - 2026-09-06

Eine Funktionsregression aus 3.5.0 behoben, gefunden beim Live-Test gegen echte Hardware: jeder Modbus-Schreibvorgang nutzte den falschen Funktionscode.

#### Behoben
- **Jeder Modbus-Schreibvorgang nutzte für ein einzelnes Register FC06 (Write Single Register); Lambdas eigene Modbus-Dokumentation schreibt für jeden Schreibvorgang FC16 (Write Multiple Registers) vor und implementiert FC06 überhaupt nicht** — FC06 wird mit Illegal Function (Exception 0x01) beantwortet. Dadurch scheiterte, je nach Pfad protokolliert oder still, jede schreibende Funktion: die Raumthermostat-Steuerung (Register 5004, protokolliert alle ~9s), der PV-Überschuss-Export, die Warmwasser-/Heizkreis-/Kühlkreis-Sollwerte, der Vorlauf-Offset sowie der generische `write_modbus_register`-Service. Der Vor-3.5-Code auf Basis von `pymodbus` hatte dieses Problem nie, da er ausnahmslos über `write_registers()` (FC16) schrieb, auch für ein einzelnes Register. Jedes `writable=True`-Feld in `lambda_modbus/` setzt jetzt `force_fc16=True` (ein von `modbus-connection` genau für diesen Fall vorgesehenes Flag), und die beiden Stellen mit direktem Schreibzugriff (PV-Überschuss-Writer und der generische Register-Schreib-Service in `services.py`) rufen jetzt `write_registers()` statt `write_register()` auf.
- Live gegen echte Hardware verifiziert (Firmware `V0.0.8-3K`): Der Raumtemperatur-Schreibzugriff (Register 5004) sowie eine Warmwasser-Sollwertänderung über `climate.set_temperature` kamen nach dem Fix korrekt an; zuvor scheiterten beide mit `Modbus Exception 0x01 for function code 0x06`.

#### Update-Hinweis (Statistik-Reparaturen)
- **Einheiten-Label**: `hp1_volume_flow_heat_sink` und `hp1_volume_flow_energy_source` nutzen jetzt `UnitOfVolumeFlowRate` (`L/h`, `L/min`) statt der 2.x-Strings `l/h` / `l/min`. Der Recorder kann die alten Labels nicht umrechnen, daher meldet HA die Reparaturen „Maßeinheit geändert“ und „Mittelwert-Typ geändert“ (2.x speicherte `state_class: total`, 3.5 `measurement`). Der abweichende Mittelwert-Typ blockiert neue Langzeitstatistik, bis die alte gelöscht ist; eine andere Lösung bietet HA dafür nicht an. Lösung: in der Einheiten-Reparatur „Alle alten Statistikdaten für diese Entität löschen“ wählen (oder unter Entwicklerwerkzeuge → Statistiken löschen); damit sind beide Reparaturen erledigt. „Die Maßeinheit der historischen statistischen Werte von „l/h“ auf „L/h“ aktualisieren, ohne Konvertierung.“ ändert nur das Einheiten-Label und lässt die Mittelwert-Typ-Reparatur stehen, es wird also keine Statistik aufgezeichnet; die 2.x-Statistik dieser beiden Sensoren lässt sich nicht behalten.
- **Statusklasse entfernt**: Code-artige Sensoren (`*_error_number`, `request_type`, `config_parameter_24/33/50/60`) haben in 3.5 keine state_class (`_count()` in `sensor.py`), in 2.x waren sie `total`/`measurement`. HA meldet „Statusklasse entfernt“; kann ignoriert oder die Statistik gelöscht werden.
- Umbenannte/entfernte 2.x-Entitäten erscheinen als Spook-Reparaturen „unbekannte Entitätsreferenz“ in Dashboards/Templates.
- **`hcX_flow_line_temperature_setpoint` entfällt ab Firmware-Stufe 3**: Seit 3.5.5 ([#112](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/112)) ist der Sensor auf `firmware_versions=("1-2",)` beschränkt (`sensor.py`), weil Register 5X07 ab Firmware-Stufe 3 die schreibgeschützte `target_temp_flow_line` ist. 2.x legte auf dieser Firmware beide Entitäten an; Upgrader behalten daher eine verwaiste `…_flow_line_temperature_setpoint`, und alles, was sie referenziert, bricht. Keine Registry-Migration benennt sie automatisch um (andere `unique_id`, andere Bedeutung). Um die Statistik-Kette zu erhalten: verwaiste Entität löschen, dann `…_target_temp_flow_line` die alte entity_id geben.

#### Hinweis
- Im aktuellen Modell existiert kein `PackedBitsField`/Bit-Feld-Register, daher greift der eine FC06-Sonderpfad innerhalb von `modbus-connection`s `write_register_field()` (für Read-Modify-Write gepackter Bit-Register, ignoriert `force_fc16`) hier nie.

### [3.5.2] - 2026-09-06

Nachzieharbeiten zu 3.5.0: drei Lücken, gefunden bei der Prüfung aller 2.7.x/2.8.x-Bugfixes des Vor-Rewrite-Branches `main` gegen den neu geschriebenen Code — ob sie dort noch galten.

#### Behoben
- **`via_device`-Deprecation-Warnung bei Sub-Geräten**: `LambdaCoordinator.device_info()` übergab bei Sub-Geräten weiterhin das veraltete `via_device` (Identifiers-Tupel), was bei jedem Setup eine Home-Assistant-Entfernungswarnung protokollierte (Entfernung angekündigt für 2027.8.0). Da 3.x durchgängig Home Assistant ≥ 2026.9 voraussetzt, wird jetzt immer `via_device_id` (die Registry-ID des übergeordneten Geräts) aufgelöst und gesetzt — anders als beim 2.8.5-Fix auf `main` ist dafür keine Versions-Weiche nötig.
- **0xFFFF ("keine Anforderung"/"kein externer Sensor") als echter Wert gelesen**: Die Außentemperatur (ohne eingespeisten externen Fühler) und die Anforderungsregister eines Puffers (ohne aktive Anforderung) melden `0xFFFF` (-1) statt eines Messwerts — skaliert sah das wie ein plausibler Wert aus (-0,1 °C) statt `unknown`. Dieser Sonderwert wird jetzt bei den betroffenen Feldern gefiltert (`Ambient.temperature`, `Buffer.request_type`/`request_flow_line_temp_setpoint`/`request_return_line_temp_setpoint`/`request_heat_sink_temp_diff_setpoint`/`modbus_request_heating_capacity`, `HeatingCircuit.operating_mode`) — die globale Sentinel-Filterung blieb unverändert, da -1 bei anderen Registern (z. B. Temperatur-Offsets) ein gültiger Wert ist.
- **Modbus-Lese-/Schreibvorgänge wurden nicht tatsächlich serialisiert**: Der eigene Anfrage-Pacing-Lock von `modbus-connection` greift nur, wenn der Verbindung ein `message_spacing`/`unit_spacing` größer als 0 mitgegeben wird — ohne das (dem Standard) ist er wirkungslos. Poll-Loop und der Schreib-Timer für PV-Überschuss-/Raumtemperatur-Steuerung laufen mit unabhängigen Intervallen auf derselben Verbindung; ohne diesen Fix konnte dieselbe Fehlerklasse wie in GitHub Issue #105 beschrieben (ein Schreibvorgang wird als erfolgreich geloggt, kommt am Gerät aber nie an) erneut auftreten. Beim Verbindungsaufbau wird jetzt ein `message_spacing` von 50 ms gesetzt.

#### Tests
- Regressionstest ergänzt: die COP-, Energie- und Zyklus-Zähler einer zweiten Wärmepumpe stammen aus ihren eigenen Registern, unabhängig von der ersten (ursprüngliches Symptom von Issue #107/#93).
- Regressionstest ergänzt: Neustart-Restore eines Zählers kombiniert mit einem geänderten konfigurierten Offset im selben Lauf — der Offset verschiebt den Gesamtwert exakt einmal um die Differenz.
- Regressionstest ergänzt: ein unplausibel großer Sprung eines Energiezählers in einem Poll (über der bestehenden Delta-Obergrenze) wird nicht verbucht, analog zu den bestehenden Tests für einen negativen Delta.
- Regressionstest ergänzt: die Verbindung wird immer mit einem `message_spacing` größer 0 aufgebaut.
- Bestehenden Device-Info-Test verschärft: prüft jetzt, dass der Coordinator nie das veraltete `via_device`-Kwarg übergibt, nicht nur das resultierende `via_device_id`.

### [3.5.0] - 2026-09-06

Übernahme eines von Grund auf neu geschriebenen Codes für die Integration (PR #115, „fork-takeover"), der die Modbus-Schicht und einen Großteil des Entity-Codes der `main`-2.8.x-Codebasis ersetzt.

#### Geändert
- **Modbus-Schicht**: `pymodbus` und der handgeschriebene `modbus_utils.py`-Wrapper werden durch [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection) mit dem `tmodbus`-Backend ersetzt. Das Registermodell wird jetzt je Teilsystem deklarativ beschrieben (`lambda_modbus/`), statt als datengetriebene Dictionaries.
- **Adressierung mehrerer Wärmepumpen**: Wärmepumpen (und jedes andere Modul) werden durchgehend über einen Integer-Index adressiert und als In-Process-Objekte modelliert, statt eine `entity_id` aus dem Gerätenamen zu rekonstruieren — die Fehlerklasse hinter den GitHub Issues #93/#107 (Sensoren einer zweiten Wärmepumpe wurden still auf die falsche Quelle verdrahtet oder gar nicht gefunden) kann in dieser Form nicht mehr auftreten.
- **Persistenz der Energie-/Zyklus-Zähler**: Zähler sind jetzt normale Home-Assistant-`RestoreSensor`s mit einer selbst nachgeführten Offset-Basislinie; die bisherige, vom Coordinator verwaltete Datei `cycle_energy_persist.json` (und die dort auf `main` in 2.8.4/2.8.6 behobene Fehlerklasse bei Neustart/Offset-Persistenz) existiert in dieser Form nicht mehr.
- **Mindest-Home-Assistant-Version**: jetzt 2026.9.0 (vorausgesetzt von `modbus-connection[tmodbus]`), durchgesetzt in `hacs.json`. Ältere Home-Assistant-Versionen werden von dieser Linie nicht mehr unterstützt.

#### Hinweis
- Die bei dieser Prüfung gefundenen und behobenen Lücken siehe [3.5.2](#352---2026-09-06) oben. Die [Entwickler-Dokumentation](https://guidojeuken-6512.github.io/lambda_heat_pumps/Entwickler/modbus-serialisierung/) beschreibt das neue Modbus-Serialisierungs-Design im Detail.

### [2.6.0] - 2026-06-24

#### Neue Funktionen
- **Kühlkreis-Climate-Entity**: Neue Entity `climate.<prefix>_hc<n>_cooling_circuit` je erkanntem Heizkreis, analog zur bestehenden `heating_circuit`-Climate-Entity. Nutzt dieselbe Quelle für die Ist-Temperatur (Raum-Gerätetemperatur) wie `heating_circuit`, schreibt den Sollwert aber auf das dedizierte Kühl-Sollwert-Register (Offset 52, z. B. Register 5052 für HC1, 5152 für HC2, …). Standardmäßig deaktiviert — Aktivierung über die neue Option `cooling_mode_enabled` im Options-Flow der Integration.

---

### [2.5.0] - 2026-04-16

Reines Code-Qualitäts- und Stabilitätsrelease — keine Breaking Changes, keine Auswirkung auf `unique_id`, `entity_id` oder `sensor_id`.

#### Behoben
- **Race Condition im Reload-Flag** (K-01): Fast-Path verwendet jetzt `lock.locked()` (atomar) — TOCTOU-Lücke in `async_reload_entry()` geschlossen
- **Exception-Logging im Auto-Detection-Task** (K-02, behebt #80): Log-Level auf `WARNING` + `exc_info=True` für vollständigen Traceback angehoben
- **Modbus-Locks an falschen Event-Loop gebunden** (K-03): Lazy-Initialization — Locks werden erst beim ersten Aufruf erstellt, nicht mehr beim Modul-Import
- **Entity-Registry-Listener ohne Debounce** (H-01): 250 ms Debounce verhindert redundante parallele Mapping-Updates
- **Nicht-atomares Sensor-ID-Update** (H-02): Lokale Kopien + atomarer Tausch eliminieren inkonsistente Zwischenzustände
- **Persist-Datenverlust beim Shutdown** (H-03): `_persist_counters(force=True)` beim Unload flusht Daten innerhalb des Debounce-Fensters
- **Climate State-Inkonsistenz bei Write-Fehler** (H-04): Explizite `None`-Prüfung vor lokalem State-Update; Refresh bei Fehler
- **Fragile JSON-Repair-Logik** (M-01): Regex-Reparatur entfernt; Backup-und-Reset-Strategie bei korrupten Persist-Dateien
- **Modbus-Batch-Größe zu nah am Protokoll-Limit** (M-02): Limit von 120 auf 100 Register gesenkt (sicherer Puffer unter dem Maximum von 125)
- **Fehlende Temperaturbereich-Validierung** (M-03): `min_temp >= max_temp` wird erkannt und mit Warnung auf Defaults zurückgefallen
- **Fehlendes Versionsfeld in der Persist-Datei** (M-04): `"version": 1` wird in alle neuen Persist-Dateien geschrieben

#### Code-Qualität
- Log-Level in `modbus_utils.py` und `coordinator.py` korrigiert (`INFO` → `WARNING`/`DEBUG`) (Q-01)
- ~110 Zeilen hardcodierter INT32-Debug-Code für Register 1020/1022 entfernt (Q-02)
- Dead-Code-Methode `_generate_entity_id()` entfernt (Q-03)
- Log-Präfix-Konstanten in `__init__.py` definiert (Q-04); Inline-Imports an Dateianfang verschoben (Q-05)

#### Abhängigkeiten
- `pymodbus` 3.9.2 → 3.13.0 · `packaging` ≥23.1 → ≥26.0 · `homeassistant` ≥2025.10 → ≥2026.2.3 (Test)

---

### [2.4.0] - 2026-03-29

#### Behoben
- **Kritisch: Cycling-Offset wurde bei jedem Zyklus erneut addiert**: `increment_cycling_counter()` hat den in `lambda_wp_config.yaml` konfigurierten `cycling_offsets`-Wert bei jeder erkannten Modusänderung neu aufaddiert statt einmalig beim Start. Die Offset-Logik wurde aus dieser Funktion entfernt; alleinige Verantwortung liegt jetzt bei `_apply_cycling_offset()` in `sensor.py`, das korrekt mit Differenz-Tracking arbeitet.
- **Moduserkennung für Cycling-Zähler**: Fehler durch gemeinsam genutzten Zustand behoben, der dazu führte, dass Zyklusereignisse nicht erkannt wurden.
- **NameError in `increment_cycling_counter()`**: Betriebsmodus-Übergänge wurden zwar erkannt, aber wegen eines `cycling_entity`-NameErrors nie gezählt.
- **Energie-Offsets wurden lautlos ignoriert**: `_apply_energy_offset()` wurde nicht aus `async_added_to_hass()` aufgerufen, sodass konfigurierte Energie-Offsets beim HA-Start keine Wirkung hatten.

#### Verbesserungen
- Konfigurations-Template (`lambda_wp_config.yaml`) um Beispiele für negative Offsets und thermische Energie-Offset-Schlüssel erweitert.
- Migrationssystem aktualisiert; 23 neue Tests für Offset-Szenarien hinzugefügt.
- Dokumentation aktualisiert: Verwendung negativer Offsets dokumentiert, veraltete Warnhinweise entfernt.

---

### [2.3.4] - 2026-03-21
Änderung an der Logik zur Erkennung von Kompressorstarts (Cycling): Der Sensor `compressor_unit_rating` wird verwendet und häufiger abgefragt.

---

### [2.3] - 2026-XX-XX

> ⚠️ **Vor dem Update**: Erstelle ein Backup deiner Home Assistant Konfiguration (Verzeichnis `config/`) sowie der `lambda_wp_config.yaml`. Dieses Release enthält einen Breaking Change, der Entity-IDs verändern kann.

#### Breaking Changes
- **Name-Prefix-Normalisierung**: Der konfigurierte `name_prefix` wird ab sofort automatisch in Kleinbuchstaben umgewandelt und Leerzeichen werden entfernt. Wer einen Prefix mit Großbuchstaben oder Leerzeichen verwendet hatte (z. B. `"EU08L"` oder `"Lambda WP"`), bekommt geänderte Entity-IDs — bestehende Automationen, Dashboards und Template-Sensoren müssen angepasst werden.

#### Neue Funktionen
- **COP-Sensoren** (Heizen / Kühlen / Warmwasser): Neue Sensoren für die Arbeitszahl — stündlich, täglich, monatlich und gesamt. Berechnung aus thermischem Energieertrag und elektrischem Verbrauch.
- **Thermische Energieverbrauchs-Sensoren**: Tracking der Wärmeabgabe pro Wärmepumpe — täglich, monatlich, gesamt und gestern. Optional kann ein externer Wärmemengenzähler als Quellsensor konfiguriert werden (`thermal_sensor_entity_id` in `lambda_wp_config.yaml`).
- **Vorlauftemperatur-Sollwert-Sensor**: Neuer Sensor `hp_flow_line_temperature_setpoint` für den berechneten Vorlauf-Sollwert.
- **Kompressorstarts Gestern**: Neuer Sensor `compressor_start_cycling_yesterday` für die Kompressorstarts des Vortags.

#### Behoben
- **Kompressorstart-Zähler**: Der Zähler löst jetzt bei HP-State `2` (RESTART-BLOCK) statt bei `5` (START COMPRESSOR) aus. RESTART-BLOCK ist der Sperrzeit-Zustand nach einem abgeschlossenen Kompressorlauf — damit werden abgeschlossene Zyklen gezählt, nicht gestartete.
- **Duplikat-Cleanup**: Sensoren mit `config_parameter_` im Namen wurden vom Regex `_\d+$` fälschlicherweise als HA-Duplikate erkannt (z. B. endet `config_parameter_24` auf `_24`). Diese Sensoren werden jetzt in beiden Cleanup-Phasen übersprungen.
- **Energie-Konsistenz**: Tages-, Monats- und Jahreswerte werden beim Restore und Reset geprüft — ein Vorperiodenwert kann den aktuellen Gesamtwert nicht übersteigen, damit keine negativen Differenzen entstehen.
- **Reset-Reihenfolge**: Gestern-Sensoren werden jetzt vor dem täglichen Reset aktualisiert, sodass `_yesterday` immer dem tatsächlichen Vortageswert entspricht.
- **Energieberechnung**: Differenzwerte werden jetzt direkt aus den HA-Entities gelesen statt aus internen Variablen — verhindert Inkonsistenzen nach Reloads.
- **Modbus int16-Konvertierung**: Korrektur der Vorzeichen-Konvertierung für 16-Bit-Register (Two's Complement). Neue Hilfsfunktion `clamp_to_int16` verhindert Überlauf.
- **Raumthermostat-Offset**: Offset-Bereich und Modbus-Konvertierung für vorzeichenbehaftete Werte korrigiert.
- **Maximum Boiler Temperature**: Aus den Sensor-Templates entfernt — liest dasselbe Modbus-Register wie `target_high_temperature`.

#### Verbesserungen
- **Internes Refactoring**: `const.py` in drei Module aufgeteilt (`const_base.py`, `const_sensor.py`, `const_calculated_sensors.py`); pro-Entry-Reload-Locks ersetzen eine globale Sperre; f-String-Logging durch HA-konformes `%s`-Format ersetzt; redundante `_unique_id`-Attribute aus Sensor-Klassen entfernt.

---

### [2.0.1] - 2025-01-XX

#### Neue Funktionen
- **Vorlauf-Offset Number Entity**: Hinzugefügte bidirektionale Modbus-synchronisierte Number-Entity zur Anpassung der Vorlauf-Offset-Temperatur
  - Wird automatisch für jeden Heizkreis (HC1, HC2, etc.) erstellt
  - Bereich: -10.0°C bis +10.0°C mit 0.1°C Schrittweite
  - Liest aktuellen Wert aus Modbus-Register und schreibt Änderungen direkt zurück
  - Erscheint in der Geräte-Konfiguration neben den Heizkurven-Stützpunkten
  - Modbus-Register: Register 50 (relativ zur Base-Adresse des Heizkreises)

#### Behoben
- **Heizkurven-Validierung**: Validierungslogik korrigiert, um beide Bedingungen unabhängig zu prüfen
  - `elif` zu `if` geändert, um sicherzustellen, dass beide Validierungsprüfungen durchgeführt werden
  - Meldet jetzt alle Validierungsprobleme, wenn mehrere Heizkurven-Werte falsch konfiguriert sind
  - Zuvor wurde nur das erste Problem gemeldet, wenn alle drei Temperaturpunkte in falscher Reihenfolge waren
  - Behoben: Problem wenn alle drei Heizkurven-Punkte identische Werte haben (Issue #48)
- **Warmwasser-Temperaturgrenzen**: Minimum/Maximum-Werte für Warmwasser auf Lambda-Standard (25/65°C) angepasst (Issue #50)
- **Eco-Modus in Heizkurve**: Hinzugefügte Eco-Temperaturreduktion für Heizkreise (Issue #51)
  - Neue Number-Entity `eco_temp_reduction` pro Heizkreis mit Bereich -10,0 bis 0,0°C (Standard: -1,0°C)
  - Reduziert automatisch die berechnete Vorlauftemperatur, wenn der Heizkreis im ECO-Modus ist (operating_state = 1)
  - In die Heizkurven-Berechnung integriert, zusammen mit Vorlauf-Offset und Raumthermostat-Anpassungen


### [2.0.0] - 2025-01-XX

#### Neue Funktionen
- **Geräte-Hierarchie**: Implementierte Aufteilung in Haupt- und Sub-Geräte für bessere Organisation und klarere Entity-Struktur
- **Mehrsprachige Unterstützung**: Hinzugefügte umfassende Übersetzungen in Deutsch und Englisch für alle Entity-Namen, gewährleistet ordnungsgemäße Lokalisierungsunterstützung
- **Heizkurven-Berechnung**: Implementierte intelligente Heizkurven-Berechnung mit drei Stützpunkten (Kalt, Mittel, Warm) und automatischer Vorlauftemperatur-Berechnung basierend auf Außentemperatur
  - **Kalter Punkt**: Definiert die Heizkurve bei niedrigen Außentemperaturen
  - **Mittlerer Punkt**: Definiert die Heizkurve bei mittleren Außentemperaturen
  - **Warmer Punkt**: Definiert die Heizkurve bei hohen Außentemperaturen
  - **Neuer Sensor**: `heating_curve_flow_line_temperature_calc` berechnet automatisch die optimale Vorlauftemperatur basierend auf aktueller Außentemperatur und den konfigurierten Stützpunkten
- **Kompressor-Start Cycling Sensor**: Hinzugefügter neuer Cycling-Sensor zur Verfolgung von Kompressor-Start-Ereignissen
  - **Total-Sensor**: `compressor_start_cycling_total` - Verfolgt Gesamtanzahl der Kompressor-Starts seit Installation
  - **Daily-Sensor**: `compressor_start_cycling_daily` - Verfolgt tägliche Kompressor-Starts (Reset um Mitternacht)
  - **2H-Sensor**: `compressor_start_cycling_2h` - Verfolgt 2-Stunden Kompressor-Starts (Reset alle 2 Stunden)
  - **4H-Sensor**: `compressor_start_cycling_4h` - Verfolgt 4-Stunden Kompressor-Starts (Reset alle 4 Stunden)
  - **Monthly-Sensor**: `compressor_start_cycling_monthly` - Verfolgt monatliche Kompressor-Starts (Reset am 1. des Monats)
  - **Flankenerkennung**: Verwendet HP_STATE Register (1002) statt HP_OPERATING_STATE, erkennt "START COMPRESSOR" Status (Wert 5)

#### Verbesserungen
- Verbesserte Entity-Namensgebung mit ordnungsgemäßen Geräte- und Sub-Geräte-Präfixen
- Verbesserte Übersetzungs-Ladung und -Anwendung für alle Entity-Typen
- Bessere Integration mit Home Assistants Übersetzungssystem
- **Write-Interval-Optimierung**: Reduziertes Write-Interval von 41 Sekunden auf 9 Sekunden für schnellere Reaktionszeiten
- **Externe Verbrauchssensor-Validierung**: Verbesserte Validierung externer Verbrauchssensoren mit Entity Registry Fallback-Prüfung, ermöglicht Sensoren auch dann zu akzeptieren, wenn sie beim Start noch nicht im State verfügbar sind. Runtime Retry-Mechanismus behandelt temporäre Nicht-Verfügbarkeit elegant.

### [1.4.3] - 2025-11-04
#### Fehlerbehebungen
- **ISSUE 39**  Modebus batch Reads erkennen Fehler falsch: Schnelleres Umsschalten zu individual reads, damit korrekte Sensoren wieder zur Verfügung stehen
- **ISSUE 22** Zusätzliches logging eingefügt, um Fehler zu identifizieren
- **Einheit des Sensors volume_flow_heat_sink korregiert** zu l/h

### [1.4.2] - 2025-10-24

#### Fehlerbehebungen
- **Test-Reparaturen**: Behoben fehlgeschlagene Tests durch Ersetzen von Mock-Objekten mit ordnungsgemäßen Test-Implementierungen
- **Verbesserte Test-Zuverlässigkeit**: Reduzierte false-positive Test-Fehler und verbesserte Test-Stabilität
- **Integration-Reload-Fehler**: Behoben Fehler beim Neuladen der Integration
- **Konfigurations-Fix**: Behoben `default_config` in `load_lambda_config()` um alle erforderlichen Keys einzubinden (`energy_consumption_sensors`, `energy_consumption_offsets`, `modbus`)

#### Geändert
- **Register-Order-Werte**: Konfigurationswerte von `"big"`/`"little"` auf `"high_first"`/`"low_first"` geändert für bessere Klarheit
  - Alte Werte (`big`/`little`) werden weiterhin mit automatischer Konvertierung unterstützt
  - Neuer Standard ist `"high_first"` (ersetzt `"big"`)
  - Verbesserte Dokumentation und Kommentare zur Klärung von Register-Reihenfolge vs. Byte-Endianness

#### Verbesserungen
- **Test-Optimierung**: 57 Tests erfolgreich repariert und optimiert
- **Gitignore-Korrektur**: Korrigiert .gitignore für ordnungsgemäße Einbindung aller docs-Unterverzeichnisse
- **Service-Dokumentation**: Erstellt umfassende Dokumentation für zukünftige Service-Optimierungen
- **Service-Scheduler-Optimierung**: Implementierte intelligente Service-Scheduler, die nur aktiviert werden, wenn PV-Surplus oder Raumthermostat-Steuerungsoptionen aktiviert sind, wodurch der Ressourcenverbrauch erheblich reduziert wird, wenn Services nicht benötigt werden

---



### [1.4.1] - 2025-10-21

#### Neue Funktionen
- **Massive Performance-Verbesserungen**: Dramatisch verbesserte Start- und Update-Performance der Integration
  - **Startzeit**: Reduziert um ~72% (von ~7,3s auf ~2,05s) durch intelligente Background-Auto-Detection
  - **Update-Zyklen**: Reduziert um ~50% (von >30s auf <15s) durch globale Register-Deduplizierung
  - **Modbus-Traffic**: Reduziert um ~80% durch Eliminierung von Duplikat-Register-Reads
- **Intelligente Auto-Detection**: Implementierte Background-Auto-Detection für bestehende Konfigurationen, eliminiert Startverzögerungen bei gleichzeitiger Aufrechterhaltung der Hardware-Änderungserkennung
- **Globaler Register-Cache**: Hinzugefügtes umfassendes Register-Deduplizierungssystem, das Duplikat-Modbus-Reads über alle Module (HP, Boiler, Buffer, Solar, HC) eliminiert
- **Optimiertes Batch-Reading**: Verbesserte Modbus-Batch-Reads mit größeren zusammenhängenden Register-Bereichen und reduzierten individuellen Read-Schwellenwerten
- **Paralleles Template-Setup**: Template-Sensoren laden nun in Background-Tasks, verhindert Start-Blockierung
- **Persist-I/O-Optimierung**: Hinzugefügte Debouncing- und Dirty-Flag-Mechanismen zur Reduzierung unnötiger Datei-Schreibvorgänge
- **Verbindungs-Health-Optimierung**: Reduzierte Verbindungs-Timeout von 5s auf 2s für schnellere Fehlererkennung

#### Verbesserungen
- **Erweiterte Energieverfolgung**: Verbesserte Verbrauchsverfolgung mit automatischer Einheitenkonvertierung (Wh/kWh/MWh)
- **Robuste Sensor-Behandlung**: Hinzugefügter Retry-Mechanismus für Sensor-Verfügbarkeit beim Start
- **Umfassende Protokollierung**: Hinzugefügte detaillierte Protokollierung für Sensor-Wechsel-Erkennung und Energieberechnungen
- **Monatliche & Jährliche Verbrauchssensoren**: Hinzugefügte monatliche und jährliche Energieverbrauchssensoren für Langzeitverfolgung
- **Service-Setup-Optimierung**: Dienste werden nun nur einmal eingerichtet, unabhängig von der Anzahl der Einträge
- **Konfigurationsfluss-Verbesserungen**: Erweiterte Validierung für bestehende Verbindungen und IP-Adressen, veraltete Module entfernt
- **Generalisierte Reset-Funktionen**: Implementierte generalisierte Reset-Funktionen für alle Sensor-Typen mit erweiterten Tests
- **Code-Bereinigung**: Bereinigt const.py, YAML-Templates und allgemeine Codestruktur
- **Dokumentations-Updates**: Aktualisierte Dokumentation und erstellte Programmablaufdiagramme

#### Technische Änderungen
- Automatische `lambda_wp_config.yaml`-Erstellung aus `LAMBDA_WP_CONFIG_TEMPLATE`
- Integration der Konfigurationsdatei-Erstellung in bestehende Migrations-Pipeline
- Erweiterte Fehlerbehandlung in `LambdaDataUpdateCoordinator`
- Verbesserte Sensor-Attribut-Ladung mit besserer Fehlerwiederherstellung

---

### [1.4.0] - 2025-10-05

#### Neue Funktionen
- **Verbrauchssensoren nach Betriebsart**: Hinzugefügte konfigurierbare Verbrauchssensoren, die den Energieverbrauch nach Betriebsart (Heizen, Warmwasser, Kühlen, Abtauen) mit anpassbaren Quellsensoren verfolgen (Issue #21)
- **Register-Reihenfolge-Konfiguration**: Hinzugefügte Register-Reihenfolge-Konfiguration in `lambda_wp_config.yaml` für ordnungsgemäße 32-Bit-Wert-Interpretation aus mehreren 16-Bit-Registern (Issue #22)
- **Sensor-Wechsel-Erkennung**: Implementierte automatische Erkennung von Energie-Sensor-Wechseln mit intelligenter Behandlung von Sensor-Wert-Übergängen zur Vermeidung falscher Verbrauchsberechnungen

#### Fehlerbehebungen
- **Register-Reihenfolge-Fix**: Behoben Register-Reihenfolge-Probleme für 32-Bit-Werte mit initialem Quick-Fix-Ansatz (Issue #22)
- **Daily-Sensor-Reset-Automatisierung**: Behoben Fehler in der Automatisierung zum Zurücksetzen der täglichen Sensoren (Issue #29)
- **Auto-Detection**: Behoben Auto-Detection erkannte bestehende Konfigurationen (IP/Port/SlaveId) nicht
- **DCHP Discovery**: Behoben DCHP Discovery Fehlermeldungen
- **HASS Validation**: Behoben Home Assistant Validierungsfehler
- **Daily Reset Funktion**: Repariert Daily Reset-Funktion für Sensoren

#### Verbesserungen
- **Erweiterte Energieverfolgung**: Verbesserte Verbrauchsverfolgung mit automatischer Einheitenkonvertierung (Wh/kWh/MWh)
- **Robuste Sensor-Behandlung**: Hinzugefügter Retry-Mechanismus für Sensor-Verfügbarkeit beim Start
- **Umfassende Protokollierung**: Hinzugefügte detaillierte Protokollierung für Sensor-Wechsel-Erkennung und Energieberechnungen
- **Monatliche & Jährliche Verbrauchssensoren**: Hinzugefügte monatliche und jährliche Energieverbrauchssensoren für Langzeitverfolgung
- **Service-Setup-Optimierung**: Dienste werden nun nur einmal eingerichtet, unabhängig von der Anzahl der Einträge
- **Konfigurationsfluss-Verbesserungen**: Erweiterte Validierung für bestehende Verbindungen und IP-Adressen, veraltete Module entfernt
- **Generalisierte Reset-Funktionen**: Implementierte generalisierte Reset-Funktionen für alle Sensor-Typen mit erweiterten Tests
- **Code-Bereinigung**: Bereinigt const.py, YAML-Templates und allgemeine Codestruktur
- **Dokumentations-Updates**: Aktualisierte Dokumentation und erstellte Programmablaufdiagramme

#### Technische Änderungen
- Automatische `lambda_wp_config.yaml`-Erstellung aus `LAMBDA_WP_CONFIG_TEMPLATE`
- Integration der Konfigurationsdatei-Erstellung in bestehende Migrations-Pipeline
- Erweiterte Fehlerbehandlung in `LambdaDataUpdateCoordinator`
- Verbesserte Sensor-Attribut-Ladung mit besserer Fehlerwiederherstellung

---

### [1.3.0] - 2025-01-03

#### Neue Funktionen
- **Neue 2H/4H Cycling-Sensoren**: Hinzugefügte 2-Stunden- und 4-Stunden-Cycling-Sensoren für detaillierte Wärmepumpen-Betriebsüberwachung
- **Erweiterte Cycling-Offsets**: Verbesserte Cycling-Counter-Offset-Funktionalität für Gesamtsensor-Anpassungen beim Austausch von Wärmepumpen oder Zurücksetzen von Zählern
- **Robuste Flankenerkennung**: Implementierung einer robusten Flankenerkennung für Wärmepumpen-Betriebszustände mit verbesserter Zuverlässigkeit
- **Dynamische Fehlerbehandlung**: Erweiterte Batch-Read-Fehlerbehandlung mit automatischem Fallback auf Einzel-Lesevorgänge nach Schwellenwert-Fehlern
- **Cycling-Warnungen-Management**: Hinzugefügte Cycling-Warnungen-Unterdrückungslogik zur Verwaltung von Entity-Registrierungsproblemen

#### Fehlerbehebungen
- **Konfigurationsdatei-Erstellung**: Behoben, dass `lambda_wp_config.yaml` nicht automatisch aus der Vorlage erstellt wurde, um eine ordnungsgemäße Konfiguration sicherzustellen
- **Tägliche Cycling-Sensoren**: Behoben, dass tägliche Cycling-Sensoren nun ordnungsgemäß Werte anzeigen und korrekt funktionieren

#### Verbesserungen
- **Coordinator-Initialisierung**: Verbesserter Coordinator-Initialisierungsprozess mit erweiterter Fehlerbehandlung
- **Debug-Protokollierung**: Umfassende Debug-Protokolle für die Nachverfolgung von Offset-Änderungen und Systemverhalten hinzugefügt
- **Dokumentation**: Aktualisierte Dokumentation zur Widerspiegelung neuer Funktionen und Konfigurationsoptionen
- **Modbus-Konfiguration**: Erweiterte Lambda Heat Pumps Integration mit spezifischen Modbus-Konfigurationen

#### Technische Änderungen
- Automatische `lambda_wp_config.yaml`-Erstellung aus `LAMBDA_WP_CONFIG_TEMPLATE`
- Integration der Konfigurationsdatei-Erstellung in bestehende Migrations-Pipeline
- Erweiterte Fehlerbehandlung in `LambdaDataUpdateCoordinator`
- Verbesserte Sensor-Attribut-Ladung mit besserer Fehlerwiederherstellung

---

### [1.2.2] - 2025-08-18

#### ⚠️ BREAKING CHANGES IN DIESER VERSION - BACKUP ERFORDERLICH

Diese Version enthält wesentliche Änderungen an der Entity Registry und den Sensor-Namenskonventionen. **Bitte erstellen Sie ein vollständiges Backup Ihrer Home Assistant-Konfiguration vor dem Update.**

**Was sich ändern wird:**
- Automatische Migration bestehender Sensor-Entities zur Vermeidung von Duplikaten
- Aktualisiertes unique_id-Format für bessere Konsistenz
- Sensor-Filterung basierend auf Firmware-Kompatibilität

**Nach der Migration bitte überprüfen:**
- Sensor-Namen und Langzeitdaten sind korrekt erhalten
- Keine doppelten Entities in Ihrem System vorhanden
- Alle Sensoren funktionieren wie erwartet
- **Automatisierungen müssen möglicherweise aktualisiert werden**, wenn sie auf migrierte Sensor-Entities verweisen

**Eine Kopie der core.config_entries, core.device_registry und core.entity_registry wird vor der Sensor-Migration erstellt und kann aus dem /lambda_heat_pumps-Ordner in den versteckten .storage-Ordner kopiert werden, um die Änderungen rückgängig zu machen. Allerdings muss dann Version 1.0.9 der Integration neu installiert werden, damit das System ordnungsgemäß funktioniert.**

---

### [1.1.0] - 2025-08-03

#### Wichtige Änderungen
- **Wechsel zu asynchronen Modbus-Clients** - Vollständige Migration von synchroner zu asynchroner Modbus-Kommunikation für bessere Kompatibilität mit anderen Integrationen
- **Runtime API-Kompatibilität** - Automatische Erkennung und Anpassung an verschiedene pymodbus-Versionen (1.x, 2.x, 3.x)
- **Leistungsverbesserungen** - Nicht-blockierende Modbus-Operationen für bessere Systemleistung
- **Entity Registry Migration** - Automatische Migration von allgemeinen und Klima-Sensoren zur Vermeidung doppelter Entities mit konsistentem unique_id-Format

#### Hinzugefügt
- Asynchrone Modbus-Wrapper-Funktionen in `modbus_utils.py`
- Runtime API-Kompatibilitätserkennung für pymodbus-Versionen
- Umfassende Fehlerbehandlung für asynchrone Modbus-Operationen
- Erweiterte Cycling-Counter mit täglichen, gestrigen und Gesamtwerten für alle Betriebsarten

#### Geändert
- Alle Modbus-Operationen zu `AsyncModbusTcpClient` migriert
- Coordinator, config_flow, services und climate Module für asynchrone Operationen aktualisiert
- `async_add_executor_job`-Wrapper zugunsten direkter asynchroner Aufrufe entfernt

#### Behoben
- RuntimeWarning: "coroutine was never awaited" in der Automatisierungseinrichtung
- Callback-Funktionsimplementierung korrigiert
- Code-Qualitätsverbesserungen und Linting-Probleme behoben
- Doppelte Sensor-Entities mit "_2"-Suffix nach Updates
- Inkonsistentes unique_id-Format für allgemeine und Klima-Sensoren
- Sensor-Filterung basierend auf Firmware-Einstellungen

#### Entfernt
- **`use_legacy_modbus_names` Konfigurationsoption** - Diese Option wurde entfernt, da sie nach der automatischen Migration aller Sensoren zum Legacy-Namensschema (`use_legacy=true`) obsolet wurde. Alle bestehenden Installationen verwenden automatisch das Legacy-Namensformat.

---

### [1.0.9] - 2024-12-19

#### Hinzugefügt
- Kompatibilität mit pymodbus >= 3.6.0
- Zähler für Wärmepumpen-Cycling nach Betriebsart
- Erweiterte Statistiken für verschiedene Betriebsarten

#### Geändert
- Aktualisiert auf neue pymodbus API (3.x)
- Redundante Parameter in `read_holding_registers`-Aufrufen entfernt
- Synchrone `connect()`-Aufrufe statt asynchroner
- Code-Stil-Verbesserungen (flake8-kompatibel)

#### Behoben
- Import-Fehler in allen Modulen behoben
- Leerzeichen-Probleme gelöst
- HACS-Validierungsfehler korrigiert
- Manifest-Schlüssel ordnungsgemäß sortiert

---

### [1.0.0] - Erste Version

#### Hinzugefügt
- Erste Version der Lambda Heat Pumps Integration
- Modbus-Kommunikation für Wärmepumpen
- Cycle Counter-Erkennung
- Climate Entity für Wärmepumpen-Steuerung

<!-- /lang:de -->
