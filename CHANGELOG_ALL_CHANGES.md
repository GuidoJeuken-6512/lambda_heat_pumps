# Changelog

**Deutsche Version siehe unten / [German version see below](#deutsche-version)**

<!-- lang:en -->
## English Version

> **📚 Documentation**: A German documentation is currently being built at [https://guidojeuken-6512.github.io/lambda_heat_pumps](https://guidojeuken-6512.github.io/lambda_heat_pumps)

### [2.8.3] - 2026-08-08

#### Bug Fixes
- **[#107](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/107) was not actually fixed by 2.8.2** (2.8.2 has been pulled from releases): the 2.8.2 fix only corrected the *read* side — resolving the integration's own internal accumulated Modbus sensor via `unique_id` instead of a reconstructed name. It did not touch the *write* side: `increment_energy_consumption_counter()` and `increment_cycling_counter()` (`utils.py`) still located their target sensors (`hot_water_energy_daily/total`, `stby_energy_*`, `cooling_energy_*`, `defrost_energy_*`, all `*_cycling_total/daily/2h/4h`) by reconstructing an `entity_id` from the device name and matching it textually against the entity registry. For any installation upgraded from 2.6.0 or earlier — whose entities keep their original, correctly-named `entity_id` — that reconstructed text never matched, so `entity_registry.async_get(entity_id)` returned nothing and the increment was silently skipped on every poll, for every affected sensor. Both functions now resolve their target entity via `unique_id` through the entity registry (same mechanism as the 2.8.2 fix, factored into a shared helper `resolve_entity_id_by_unique_id()`), with the previous text-based construction kept only as a self-healing fallback for the first cycle after an entity is newly created.
- **Root cause fixed properly this time**: `slugify_name_prefix_for_lookup()` called `slugify(name, separator="")`, which collapses *every* separator character (space, `_`, `-`, `.`, parentheses) uniformly — unlike `normalize_name_prefix()` (used for `unique_id`), which only removes spaces and leaves `_` untouched. Switching to `separator="_"` would have fixed underscores but broken names with spaces (e.g. `"Lambda WP"` would have gained an unwanted `_`). The function now decouples the two concerns: unicode transliteration (umlauts etc., via the same `unidecode` library `homeassistant.util.slugify()` already depends on internally) is applied first, then the existing, unchanged `normalize_name_prefix()` separator rule — so `entity_id` and `unique_id` agree on underscores again without regressing the space-handling case fixed in 2.7.0. Verified against the full existing `slugify_name_prefix_for_lookup` test suite plus new regression tests for the exact reported case (`"Lambda_EU10L"`).
- Known, documented, out-of-scope residual gap: a literal hyphen/dot/parenthesis in the device name is still passed through as-is in `entity_id` rather than collapsed to `_` — technically not a valid HA `entity_id` character, but consistent with `unique_id` handling and not part of what was reported in #107 (underscores, spaces, umlauts).
- **`Template not found for <mode>_energy_hourly` logged at `WARNING` on every setup/reload for `cooling`/`defrost`/`hot_water`/`stby`**: harmless log noise, not a missing sensor. `ENERGY_CONSUMPTION_PERIODS` is computed across all modes combined, so `"hourly"` counts as a globally valid period even though a template for it only exists for `heating`. The guard in `sensor.py` correctly skips creating a sensor for the other four modes, it just logged at the wrong level while doing so. Downgraded to `DEBUG` so it no longer looks like an error to end users.
- **Energy/cycling counters still stopped updating for a second heat pump (`hp2`) even after the fix above**: a separate, closely related bug in an in-memory entity cache. `sensor.py` stores each created entity in `energy_entities`/`cycling_entities` (`hass.data`) keyed by the entity's own `entity_id` attribute — read *before* `async_add_entities()` has actually registered the entity with Home Assistant (that call isn't awaited; entity registration happens later, asynchronously). For an entity that already exists in the registry under a *different* `entity_id` than what's freshly computed now (e.g. a device discovered by auto-detection while an older/buggy version was still running, or any entity renamed by the user), the entity's `entity_id` attribute at cache-population time therefore doesn't match the one the entity actually ends up using. `increment_energy_consumption_counter()`/`increment_cycling_counter()` resolve the correct real `entity_id` via the registry (unaffected), but then looked up the entity *instance* in this cache using that resolved `entity_id` — a miss, since the cache was keyed by the different, pre-registration value. For cycling counters this silently fell back to a plain `hass.states.async_set()` (visible in the log as `[state only]` instead of `[entity updated]`); for energy counters there is deliberately no such fallback (an entity's restored state can lag behind its true internal counter after a restart, so blindly trusting `hass.states.get()` risks corrupting the value) — the update was skipped entirely, with no log output at the default log level. Fixed by keying both caches by `unique_id` instead (stable by construction, identical whether or not the entity's `entity_id` has drifted) — the same principle behind the `unique_id`-based registry lookups above, now applied consistently to this internal cache too, including its other consumers (the daily "yesterday" sensor rollover in `automations.py`, and the energy-state persistence used to survive restarts in `coordinator.py`).
- **Template sensors read their source entities from a reconstructed name — fourth and last place of the same bug class**: `template_sensor.py` built the `entity_id` of every entity it depends on from the device name instead of resolving it via the stable `unique_id`. Two user-visible consequences on the affected installations (second heat pump / second heating circuit, or any entity whose registered `entity_id` diverges from what fresh code computes): the **calculated COP** (`*_cop_calc`) was stuck at `0.0` forever, because the generated template referenced `sensor.<name>_hp2_compressor_*_accumulated` while the registered entity is `sensor.<name-without-underscore>_hp2_…`; and the **heating curve** (`*_heating_curve_flow_line_temperature_calc`) silently fell back to the built-in default set points instead of the values configured in the `number.*_heating_curve_cold/mid/warm_outside_temp` entities, while the **ECO reduction** never applied at all (`operating_state` and `eco_temp_reduction` were equally unreachable). Fixed with two new shared helpers in `utils.py`: `resolve_sensor_entity_id()` bundles the recurring "generate names → adjust domain → resolve via `unique_id`" pattern (including the `_number` suffix that `number.py` appends to its `unique_id`), and `resolve_template_entity_ids()` resolves entity references inside a rendered template string generically, without touching the template definitions themselves. Where the registry has no match, the previous name-based form is kept, so behaviour is unchanged there and self-heals on the next start.
- **All COP sensors (`*_cop_daily/monthly/yearly/total/hourly`) permanently `unknown` for a second heat pump (`hp2`)**: the same root cause as the cache bug above, in a third, independent place. `LambdaCOPSensor` reads its thermal/electrical source sensors via `self._thermal_energy_entity_id`/`self._electrical_energy_entity_id`, set once at construction from the text `generate_sensor_names()` computes — never corrected against the entity registry. For a heat pump whose source energy sensors are registered under a different `entity_id` than what's freshly computed now, every `hass.states.get()` call inside `LambdaCOPSensor` looked up a non-existent entity_id, and the `async_track_state_change_event()` subscription used to trigger recalculation never fired either — so the COP sensor never had a chance to compute anything, even though its own source energy sensors (fixed above) were updating correctly. Fixed by resolving both source `entity_id`s via the entity registry (the same `resolve_entity_id_by_unique_id()` helper, called once in `async_setup_entry()` before constructing each `LambdaCOPSensor`) instead of passing through the raw `generate_sensor_names()` text.

#### Internal (no functional change, no `entity_id`/`unique_id` changes)
- Review of everything that changed since 2.6.0, aimed at reusing Home Assistant's own building blocks and removing duplication. `get_int32_register_order()` now uses the existing `utils.get_firmware_version()` instead of rebuilding its options→data→default cascade (and drops a dead import); the six identical constructions of the internal accumulated energy sensor's `entity_id` in `coordinator.py` moved into one helper; the five identical blocks filling the cycling entity cache in `sensor.py` became one loop; `LambdaCyclingSensor._handle_reset()` collapsed five identical `if/elif` branches into a single condition; and the sevenfold `[65535]` literal in the sensor templates became the named constant `SENTINEL_NO_REQUEST`.
- Deliberately *not* changed after review: the shared `asyncio.Lock` in `modbus_utils.py`, the `MAX_ENERGY_DELTA_WH` constant and the `FIRMWARE_CONFIG` structure were already using the right building blocks. `slugify_name_prefix_for_lookup()` was verified against the installed Home Assistant version and must **not** be replaced by `homeassistant.util.slugify()` — no parameter combination reproduces the asymmetric separator handling required here, so it would reintroduce the #107 regression. The six sensor-change-detection sites in `coordinator.py` deliberately keep their name-based form: their result is compared against a persisted value and written back, so resolving them via the registry would report a spurious sensor change on existing installations and reset the energy baseline.

---

### [2.8.2] - 2026-08-05 (retracted — superseded by 2.8.3, see above)

#### Bug Fixes
- **`ambient_temperature` (register 0002) was hidden on the two newest firmware versions** ([#108](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/108)): Release 2.8.0 restricted the sensor to firmware range `["1-7"]` (up to `V0.0.9-3K`) on the assumption that newer controllers no longer return a usable value. That is not the case — users feeding an external temperature in via Modbus reported valid readings on `V0.0.10-3K` and `V1.1.0-3K`, where the sensor was now missing entirely. The range is extended to `["1-9"]`, so the sensor is available again up to and including `V1.1.0-3K`. Invalid readings remain covered by the existing sentinel check (`0xFFFF` / `-1` = "no external sensor connected"), which is the appropriate mechanism here — a firmware range cannot distinguish "register absent" from "register present but unused".
- **Mode-dependent energy values stopped updating when the device name contains a special character** ([#107](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/107)): If the integration's device name contained a `_`, `-`, `.`, parentheses or an umlaut (e.g. `Lambda_EU10L`), all mode-dependent consumption values (heating, hot water, cooling, defrost) silently stopped advancing. `_track_hp_energy_type_consumption()` reconstructed the `entity_id` of the integration's own accumulated energy sensor from the device name via `slugify_name_prefix_for_lookup()`, which strips those characters — while the actually registered entity keeps them. `hass.states.get()` therefore returned `None` on every poll and the function aborted (DEBUG log only, no warning, no unavailable entity) before `_energy_last_operating_state` or `_last_energy_reading` were ever set. The underlying Modbus sensors were unaffected, since they are read directly from the register and need no lookup — which is what made this hard to spot.
  The `entity_id` is no longer guessed but resolved via the entity's **`unique_id`** in the entity registry (`async_get_entity_id()`). The `unique_id` has always been built with `normalize_name_prefix()` and is therefore stable, regardless of when the entity was created. This also covers umlauts (cf. [#93](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/93)) and entities the user renamed manually — the latter can never be found by any name-based construction. If the entity is not (yet) in the registry, e.g. during the first cycle after startup, the previous name-based construction is used as a fallback; behaviour there is unchanged and self-heals on the next poll.
  Regression introduced in **2.7.0** (the fix for [#93](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/93)): switching the lookup from `normalize_name_prefix()` to `slugify_name_prefix_for_lookup()` correctly fixed umlauts but newly broke every other special character. Installations whose entities were created on **2.7.0 or earlier** were affected; entities created on 2.8.0+ happened to match because entity creation uses the same slugified form.
  New developer documentation: [Energie-Sensor-Lookup über die Entity Registry](https://guidojeuken-6512.github.io/lambda_heat_pumps/Entwickler/energie-sensor-lookup-registry/).

---

### [2.8.0] - 2026-07-25

#### New Features
- **Range notation for `firmware_versions`**: Sensor templates can now restrict availability to a firmware *range* instead of only a minimum version, e.g. `"firmware_versions": ["1-7"]` (versions 1 through 7 inclusive) or `["-3"]` (exclude version 3). New helper `_parse_firmware_versions()` in `utils.py`; `get_compatible_sensors()` now checks `firmware_versions` (range notation) first, then falls back to the existing `firmware_version` (minimum) field, then "always active" if neither is set. Fully backward compatible — all existing `firmware_version: X` sensors are unaffected.
- **Opt-in sentinel values per sensor**: `is_sentinel_value()` gained an `extra_sentinels` parameter, fed from a new `sentinel_values` field on a sensor template (e.g. `"sentinel_values": [65535]`). Lets an individual sensor treat `0xFFFF` (`-1`) as "not available" without affecting other sensors where `-1` is a legitimate reading (e.g. temperature offsets). Applied to the defined request registers where `-1` means "no request": buffer registers 3005-3009 and HC register 5006 (`operating_mode`).

#### Bug Fixes ([#100](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/100))
- **`calculate_energy_delta` clamped implausible jumps instead of discarding them**: A delta exceeding `max_delta` (e.g. after a register-order change) was clamped to `max_delta` and booked as real consumption. It now returns `None`; the caller resets the reference reading and books nothing.
- **Lambda sentinel raw values were never filtered**: Raw register values `32768` (`0x8000`, "register not available") and `62536` (`-3000` as `int16`, "sensor disconnected") were scaled and stored as if they were real readings. Both are now filtered before scaling everywhere a register is read (batch read, single-register fallback, boiler, buffer, solar), with an `INFO` log entry when a sentinel is detected. `-1` (`0xFFFF`) is deliberately **not** a global sentinel (see opt-in mechanism above).
- **`ambient_temperature` (register 0002) returns an invalid reading on some firmware**: The register is documented as write-only from a certain firmware generation onward and returns `0xFFFF` (= -300°C) when read; on older firmware it can return a real value. It is now only available up to `V0.0.9-3K` (`firmware_versions: ["1-7"]`) and additionally opts into `65535` as a sentinel for this sensor specifically.
- **PV-surplus / room-temperature writes could sporadically never reach the device** ([#105](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/105)): The connection-stability health check performed before every write (`wait_for_stable_connection`) used its own, separate lock (`_health_check_lock`), while the actual Modbus reads and writes shared a different lock (`_modbus_read_lock`). Since these two locks didn't exclude each other, a health-check read could run concurrently with a real coordinator read or write on the same connection — desyncing Modbus transactions on the wire, so a write could be logged as successful (`✅ MODBUS WRITE SUCCESS`) while the device never actually received it. The health check now uses the same shared `_modbus_read_lock`, strictly serializing it against all other Modbus operations on the connection.
- **General sensors were never filtered by firmware version**: Unlike HP/boiler/buffer/solar/heating-circuit sensors, the general sensor group (`SENSOR_TYPES`) was never passed through `get_compatible_sensors()` — neither for entity creation (`sensor.py`) nor for register reads (`coordinator.py`). Any `firmware_version`/`firmware_versions` field on a general sensor (including `ambient_temperature` above) therefore had no effect. Both call sites now filter correctly.

---

### [2.7.0] - 2026-07-12

#### Bug Fixes
- **Umlauts in device name no longer break energy sensor lookup** ([#93](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/93)): When the integration's device name contained umlauts (e.g. `Wärmepumpe`), the internal fallback lookup for the own energy consumption sensor always returned `None`. Home Assistant's entity registry silently transliterates umlauts on first entity creation (e.g. `ä` → `a`), so the actual entity ID was `sensor.warmepumpe_hp1_…` while the lookup constructed `sensor.wärmepumpe_hp1_…`. A new helper function `slugify_name_prefix_for_lookup()` now applies the same transliteration for read-only state lookups, so the names match. The fix is limited to the two read-only lookup sites (`coordinator.py`); all `unique_id`-generating paths remain unchanged to avoid orphaning existing entities.
- **Wrong 32-bit register order default on newest firmware**: The firmware-dependent default for `int32_register_order` (introduced in this release) was `"high_first"` for every firmware entry, including the two newest (`V1.1.0-3K`, `V0.0.10-3K`). Those two now default to `"low_first"` in `FIRMWARE_CONFIG`, matching the register order actually used by that firmware generation. A manual `int32_register_order` override in `lambda_wp_config.yaml` still takes precedence and is unaffected.
- **Umlauts in device name still produced an invalid entity_id** (follow-up to [#93](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/93)): The original fix above only corrected read-only state *lookups*. Entity *creation* was still affected — `generate_sensor_names()` only lowercased `name_prefix` without transliterating umlauts, so devices with e.g. `Wärmepumpe` in the name got entities explicitly assigned an invalid `entity_id` (e.g. `sensor.eu08ü_hp1_flow_line_temperature`). Home Assistant logs a deprecation warning for this today and will reject it from HA 2027.2.0. `entity_id` generation now uses the same ASCII-safe transliteration (`slugify_name_prefix_for_lookup()`) as the read-only lookups. `unique_id` generation is deliberately left untouched to avoid orphaning already-registered entities.

---

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

### [2.8.3] - 2026-08-08

#### Fehlerbehebungen
- **[#107](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/107) wurde durch 2.8.2 nicht tatsächlich behoben** (2.8.2 wurde aus den Releases zurückgezogen): Der 2.8.2-Fix korrigierte nur die *Lese*-Seite — die Auflösung des integrationseigenen, akkumulierten Modbus-Sensors über die `unique_id` statt über einen rekonstruierten Namen. Die *Schreib*-Seite blieb unangetastet: `increment_energy_consumption_counter()` und `increment_cycling_counter()` (`utils.py`) suchten ihre Ziel-Sensoren (`hot_water_energy_daily/total`, `stby_energy_*`, `cooling_energy_*`, `defrost_energy_*`, alle `*_cycling_total/daily/2h/4h`) weiterhin, indem sie eine `entity_id` aus dem Gerätenamen rekonstruierten und textuell gegen die Entity Registry abglichen. Bei jeder von v2.6.0 oder früher hochgezogenen Installation — deren Entities ihre ursprüngliche, korrekt benannte `entity_id` behalten — traf dieser rekonstruierte Text nie zu, sodass `entity_registry.async_get(entity_id)` nichts fand und das Inkrement bei jedem Poll für jeden betroffenen Sensor still übersprungen wurde. Beide Funktionen lösen ihre Ziel-Entity jetzt über die `unique_id` in der Entity Registry auf (derselbe Mechanismus wie im 2.8.2-Fix, ausgelagert in eine gemeinsame Hilfsfunktion `resolve_entity_id_by_unique_id()`); die bisherige textbasierte Konstruktion dient nur noch als selbstheilender Fallback für den ersten Zyklus nach Neuanlage einer Entity.
- **Ursache diesmal korrekt behoben**: `slugify_name_prefix_for_lookup()` rief `slugify(name, separator="")` auf, was *jedes* Trennzeichen (Leerzeichen, `_`, `-`, `.`, Klammern) einheitlich kollabiert — anders als `normalize_name_prefix()` (für `unique_id`), die nur Leerzeichen entfernt und `_` unangetastet lässt. Ein Wechsel auf `separator="_"` hätte Unterstriche repariert, aber Namen mit Leerzeichen neu gebrochen (z. B. hätte `"Lambda WP"` einen ungewollten `_` bekommen). Die Funktion trennt jetzt beide Anliegen: zuerst Unicode-Transliteration (Umlaute etc., über dieselbe `unidecode`-Bibliothek, auf die `homeassistant.util.slugify()` intern ohnehin schon aufbaut), danach die bestehende, unveränderte Trennzeichen-Regel aus `normalize_name_prefix()` — `entity_id` und `unique_id` stimmen bei Unterstrichen wieder überein, ohne den in 2.7.0 behobenen Leerzeichen-Fall erneut zu brechen. Verifiziert gegen die vollständige bestehende `slugify_name_prefix_for_lookup`-Testsuite plus neue Regressionstests für den exakt gemeldeten Fall (`"Lambda_EU10L"`).
- Bekannte, dokumentierte und bewusst nicht behobene Restlücke: ein literaler Bindestrich/Punkt/Klammer im Gerätenamen wird in der `entity_id` weiterhin unverändert durchgereicht statt zu `_` kollabiert — technisch kein gültiges HA-`entity_id`-Zeichen, aber konsistent mit der `unique_id`-Behandlung und nicht Teil des in #107 gemeldeten Falls (Unterstriche, Leerzeichen, Umlaute).
- **`Template not found for <mode>_energy_hourly` wurde bei jedem Setup/Reload als `WARNING` geloggt, für `cooling`/`defrost`/`hot_water`/`stby`**: harmloses Log-Rauschen, kein fehlender Sensor. `ENERGY_CONSUMPTION_PERIODS` wird modus-übergreifend berechnet, wodurch `"hourly"` als global gültige Periode zählt, obwohl dafür nur bei `heating` ein Template existiert. Der Guard in `sensor.py` überspringt die Sensor-Erzeugung für die anderen vier Modi korrekt, loggte dabei aber auf der falschen Stufe. Auf `DEBUG` heruntergestuft, damit es für Endnutzer nicht wie ein Fehler aussieht.
- **Energie-/Zyklus-Zähler blieben für eine zweite Wärmepumpe (`hp2`) auch nach obigem Fix stehen**: ein separater, eng verwandter Bug in einem In-Memory-Entity-Cache. `sensor.py` speichert jede erzeugte Entity in `energy_entities`/`cycling_entities` (`hass.data`), geschlüsselt über das eigene `entity_id`-Attribut der Entity — ausgelesen **bevor** `async_add_entities()` die Entity überhaupt bei Home Assistant registriert hat (der Aufruf wird nicht awaited; die eigentliche Registrierung passiert erst später, asynchron). Bei einer Entity, die bereits unter einer **anderen** `entity_id` in der Registry existiert als der gerade frisch berechneten (z. B. ein Gerät, das von der Auto-Erkennung gefunden wurde, während noch eine ältere/fehlerhafte Version lief, oder eine vom Nutzer umbenannte Entity), stimmt das `entity_id`-Attribut zum Zeitpunkt der Cache-Befüllung deshalb nicht mit dem überein, was die Entity am Ende tatsächlich verwendet. `increment_energy_consumption_counter()`/`increment_cycling_counter()` lösen die reale `entity_id` korrekt über die Registry auf (davon unbetroffen), suchten die Entity-**Instanz** in diesem Cache aber über genau diese aufgelöste `entity_id` — ein Fehltreffer, da der Cache unter dem abweichenden, vor der Registrierung gültigen Wert geschlüsselt war. Bei den Zyklus-Zählern führte das still zu einem Fallback auf reines `hass.states.async_set()` (im Log als `[state only]` statt `[entity updated]` sichtbar); bei den Energie-Zählern gibt es diesen Fallback bewusst nicht (der wiederhergestellte State kann nach einem Neustart hinter dem echten internen Zähler zurückliegen, ein blindes Vertrauen auf `hass.states.get()` riskiert eine Verfälschung des Werts) — das Update wurde komplett übersprungen, ohne Log-Ausgabe auf der Standard-Log-Stufe. Behoben, indem beide Caches stattdessen über die `unique_id` geschlüsselt werden (baubedingt stabil, unabhängig davon, ob die `entity_id` der Entity abgewichen ist) — dasselbe Prinzip wie bei den `unique_id`-basierten Registry-Lookups oben, jetzt konsequent auch auf diesen internen Cache angewendet, inklusive seiner weiteren Konsumenten (der tägliche "Yesterday"-Sensor-Rollover in `automations.py` sowie die Energie-State-Persistenz für Neustarts in `coordinator.py`).
- **Template-Sensoren lasen ihre Quell-Entities aus einem rekonstruierten Namen — vierte und letzte Stelle derselben Bugklasse**: `template_sensor.py` baute die `entity_id` jeder Entity, von der es abhängt, aus dem Gerätenamen zusammen, statt sie über die stabile `unique_id` aufzulösen. Zwei für Nutzer sichtbare Folgen auf betroffenen Installationen (zweite Wärmepumpe / zweiter Heizkreis, oder jede Entity, deren registrierte `entity_id` von der frisch berechneten abweicht): der **berechnete COP** (`*_cop_calc`) stand dauerhaft auf `0.0`, weil das erzeugte Template `sensor.<name>_hp2_compressor_*_accumulated` referenzierte, während die registrierte Entity `sensor.<name-ohne-unterstrich>_hp2_…` heißt; und die **Heizkurve** (`*_heating_curve_flow_line_temperature_calc`) fiel still auf die eingebauten Default-Stützpunkte zurück statt die in den `number.*_heating_curve_cold/mid/warm_outside_temp`-Entities konfigurierten Werte zu verwenden, während die **ECO-Absenkung** überhaupt nie griff (`operating_state` und `eco_temp_reduction` waren gleichermaßen unerreichbar). Behoben mit zwei neuen gemeinsamen Hilfsfunktionen in `utils.py`: `resolve_sensor_entity_id()` bündelt das wiederkehrende Muster "Namen erzeugen → Domain anpassen → über `unique_id` auflösen" (inklusive des `_number`-Suffix, das `number.py` an seine `unique_id` anhängt), und `resolve_template_entity_ids()` löst die in einem fertig formatierten Template-String referenzierten Entities generisch auf, ohne die Template-Definitionen selbst anzufassen. Findet die Registry keinen Treffer, bleibt die bisherige namensbasierte Form erhalten — das Verhalten ist dort unverändert und heilt sich beim nächsten Start selbst.
- **Alle COP-Sensoren (`*_cop_daily/monthly/yearly/total/hourly`) dauerhaft `unbekannt` für eine zweite Wärmepumpe (`hp2`)**: dieselbe Ursache wie der Cache-Bug oben, an einer dritten, unabhängigen Stelle. `LambdaCOPSensor` liest seine thermischen/elektrischen Quell-Sensoren über `self._thermal_energy_entity_id`/`self._electrical_energy_entity_id`, einmalig bei der Erzeugung aus dem von `generate_sensor_names()` berechneten Text gesetzt — nie gegen die Entity Registry korrigiert. Bei einer Wärmepumpe, deren Quell-Energiesensoren unter einer anderen `entity_id` registriert sind als der gerade frisch berechneten, ging jeder `hass.states.get()`-Aufruf in `LambdaCOPSensor` ins Leere, und auch das `async_track_state_change_event()`-Abonnement zur Neuberechnung feuerte nie — der COP-Sensor bekam dadurch nie eine Chance, irgendetwas zu berechnen, obwohl seine eigenen Quell-Energiesensoren (siehe oben) längst korrekt liefen. Behoben, indem beide Quell-`entity_id`s über die Entity Registry aufgelöst werden (dieselbe `resolve_entity_id_by_unique_id()`-Hilfsfunktion, einmalig in `async_setup_entry()` vor der Erzeugung jedes `LambdaCOPSensor` aufgerufen) statt den rohen `generate_sensor_names()`-Text durchzureichen.

#### Intern (keine Funktionsänderung, keine `entity_id`/`unique_id`-Änderungen)
- Durchsicht aller Änderungen seit 2.6.0 mit dem Ziel, Home Assistants eigene Bordmittel zu nutzen und Duplikate zu entfernen. `get_int32_register_order()` verwendet jetzt das vorhandene `utils.get_firmware_version()`, statt dessen options→data→Default-Kaskade nachzubauen (und verliert dabei einen toten Import); die sechs identischen Konstruktionen der `entity_id` des internen akkumulierten Energiesensors in `coordinator.py` liegen jetzt in einer Hilfsfunktion; die fünf identischen Blöcke zur Befüllung des Cycling-Entity-Caches in `sensor.py` sind eine Schleife geworden; `LambdaCyclingSensor._handle_reset()` fasst fünf identische `if/elif`-Zweige zu einer Bedingung zusammen; und das siebenfache `[65535]`-Literal in den Sensor-Templates ist die benannte Konstante `SENTINEL_NO_REQUEST` geworden.
- Nach Prüfung bewusst *nicht* geändert: der geteilte `asyncio.Lock` in `modbus_utils.py`, die Konstante `MAX_ENERGY_DELTA_WH` und die `FIRMWARE_CONFIG`-Struktur nutzten bereits die richtigen Bordmittel. `slugify_name_prefix_for_lookup()` wurde gegen die installierte Home-Assistant-Version geprüft und darf **nicht** durch `homeassistant.util.slugify()` ersetzt werden — keine Parameterkombination bildet die hier nötige asymmetrische Trennzeichen-Behandlung nach, es käme die #107-Regression zurück. Die sechs Stellen der Sensor-Wechsel-Erkennung in `coordinator.py` behalten bewusst ihre namensbasierte Form: ihr Ergebnis wird mit einem persistierten Wert verglichen und wieder zurückgeschrieben, eine Auflösung über die Registry würde auf Bestandsanlagen einen Sensor-Wechsel melden und die Energie-Basislinie zurücksetzen.

---

### [2.8.2] - 2026-08-05 (zurückgezogen — abgelöst durch 2.8.3, siehe oben)

#### Fehlerbehebungen
- **`ambient_temperature` (Register 0002) war auf den beiden neuesten Firmware-Versionen ausgeblendet** ([#108](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/108)): Release 2.8.0 hatte den Sensor auf den Firmware-Bereich `["1-7"]` (bis `V0.0.9-3K`) beschränkt — unter der Annahme, dass neuere Steuerungen keinen brauchbaren Wert mehr liefern. Das trifft nicht zu: Nutzer, die eine externe Temperatur per Modbus einspeisen, meldeten gültige Werte auf `V0.0.10-3K` und `V1.1.0-3K`, wo der Sensor nun vollständig fehlte. Der Bereich wird auf `["1-9"]` erweitert, der Sensor ist damit bis einschließlich `V1.1.0-3K` wieder verfügbar. Ungültige Werte fängt weiterhin die bestehende Sentinel-Prüfung ab (`0xFFFF` / `-1` = "kein externer Sensor eingespeist") — das ist hier auch der passende Mechanismus, denn ein Firmware-Bereich kann nicht zwischen "Register nicht vorhanden" und "Register vorhanden, aber ungenutzt" unterscheiden.
- **Betriebsart-abhängige Energiewerte aktualisierten sich nicht bei Sonderzeichen im Gerätenamen** ([#107](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/107)): Enthielt der Gerätename der Integration ein `_`, `-`, `.`, Klammern oder Umlaute (z. B. `Lambda_EU10L`), blieben sämtliche betriebsart-abhängigen Verbrauchswerte (Heizen, Warmwasser, Kühlen, Abtauen) stehen. `_track_hp_energy_type_consumption()` rekonstruierte die `entity_id` des integrationseigenen akkumulierten Energiesensors aus dem Gerätenamen via `slugify_name_prefix_for_lookup()` — diese Funktion entfernt genau diese Zeichen, während die tatsächlich registrierte Entity sie behält. `hass.states.get()` lieferte dadurch bei jedem Poll `None`, und die Funktion brach ab (nur DEBUG-Log, keine Warnung, kein unavailable-Sensor), **bevor** `_energy_last_operating_state` bzw. `_last_energy_reading` je gesetzt wurden. Die zugrundeliegenden Modbus-Sensoren waren nicht betroffen, da sie direkt aus dem Register gelesen werden und keinen Lookup brauchen — was die Diagnose erschwerte: die Rohwerte stiegen sichtbar korrekt, nur die abgeleiteten Werte standen still.
  Die `entity_id` wird jetzt nicht mehr geraten, sondern über die **`unique_id`** in der Entity Registry aufgelöst (`async_get_entity_id()`). Die `unique_id` wird seit jeher mit `normalize_name_prefix()` gebildet und ist damit stabil — unabhängig davon, wann die Entity angelegt wurde. Das deckt zusätzlich Umlaute (vgl. [#93](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/93)) und vom Nutzer manuell umbenannte Entities ab; letztere findet eine namensbasierte Konstruktion grundsätzlich nie. Steht die Entity (noch) nicht in der Registry, z. B. im ersten Zyklus nach dem Start, greift die bisherige namensbasierte Konstruktion als Fallback; das Verhalten ist dort unverändert und heilt sich im nächsten Poll-Zyklus selbst.
  Die Regression entstand in **2.7.0** (dem Fix für [#93](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/93)): Die Umstellung des Lookups von `normalize_name_prefix()` auf `slugify_name_prefix_for_lookup()` behob Umlaute korrekt, brach aber alle übrigen Sonderzeichen neu. Betroffen waren Installationen, deren Entities unter **2.7.0 oder früher** angelegt wurden; bei Entities aus 2.8.0+ passten beide Formen zufällig zusammen, weil die Entity-Erzeugung dieselbe slugifizierte Form verwendet.
  Neue Entwickler-Dokumentation: [Energie-Sensor-Lookup über die Entity Registry](https://guidojeuken-6512.github.io/lambda_heat_pumps/Entwickler/energie-sensor-lookup-registry/).

---

### [2.8.0] - 2026-07-25

#### Neue Funktionen
- **Range-Notation für `firmware_versions`**: Sensor-Templates können die Verfügbarkeit jetzt auf einen Firmware-*Bereich* statt nur ein Minimum beschränken, z. B. `"firmware_versions": ["1-7"]` (Versionen 1 bis 7 inklusive) oder `["-3"]` (Version 3 ausschließen). Neue Hilfsfunktion `_parse_firmware_versions()` in `utils.py`; `get_compatible_sensors()` prüft zuerst `firmware_versions` (Range-Notation), dann als Fallback das bestehende `firmware_version`-Feld (Minimum), sonst "immer aktiv". Vollständig rückwärtskompatibel — alle bestehenden `firmware_version: X`-Sensoren bleiben unverändert.
- **Opt-in Sentinel-Werte pro Sensor**: `is_sentinel_value()` hat einen neuen Parameter `extra_sentinels`, gespeist aus einem neuen `sentinel_values`-Feld im Sensor-Template (z. B. `"sentinel_values": [65535]`). Damit kann ein einzelner Sensor `0xFFFF` (`-1`) als "nicht verfügbar" behandeln, ohne andere Sensoren zu beeinflussen, bei denen `-1` ein gültiger Wert ist (z. B. Temperatur-Offsets). Angewendet auf die definierten Anforderungsregister, bei denen `-1` "keine Anforderung" bedeutet: Buffer-Register 3005–3009 und HC-Register 5006 (`operating_mode`).

#### Fehlerbehebungen ([#100](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/100))
- **`calculate_energy_delta` kappte implausible Sprünge statt sie zu verwerfen**: Ein Delta über `max_delta` (z. B. nach einer geänderten Register-Reihenfolge) wurde auf `max_delta` gekappt und als echter Verbrauch gebucht. Die Funktion gibt jetzt `None` zurück; der Caller setzt die Referenz zurück und bucht nichts.
- **Lambda-Sentinel-Rohwerte wurden nie gefiltert**: Die Rohwerte `32768` (`0x8000`, "Register nicht vorhanden") und `62536` (`-3000` als `int16`, "Fühler nicht angeschlossen") wurden skaliert und als echte Messwerte gespeichert. Beide werden jetzt überall vor der Skalierung gefiltert (Batch-Read, Einzel-Read-Fallback, Boiler, Puffer, Solar), inkl. `INFO`-Log-Eintrag bei erkanntem Sentinel. `-1` (`0xFFFF`) ist bewusst **kein** globaler Sentinel (siehe Opt-in-Mechanismus oben).
- **`ambient_temperature` (Register 0002) liefert auf mancher Firmware einen ungültigen Wert**: Das Register ist ab einer bestimmten Firmware-Generation als W-only dokumentiert und liefert beim Lesen `0xFFFF` (= −300 °C); auf älterer Firmware kann es echte Werte liefern. Es ist jetzt nur noch bis `V0.0.9-3K` verfügbar (`firmware_versions: ["1-7"]`) und nutzt zusätzlich `65535` als sensorspezifischen Opt-in-Sentinel.
- **PV-Überschuss-/Raumtemperatur-Schreibvorgänge kamen sporadisch nie am Gerät an** ([#105](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/105)): Der Verbindungs-Stabilitäts-Check vor jedem Schreibvorgang (`wait_for_stable_connection`) nutzte einen eigenen, separaten Lock (`_health_check_lock`), während die eigentlichen Modbus-Reads und -Writes einen anderen Lock (`_modbus_read_lock`) teilten. Da sich diese beiden Locks nicht gegenseitig ausschlossen, konnte ein Health-Check-Read parallel zu einem echten Coordinator-Read oder -Write auf derselben Verbindung laufen — das konnte Modbus-Transaktionen auf der Leitung desynchronisieren, sodass ein Schreibvorgang als erfolgreich geloggt wurde (`✅ MODBUS WRITE SUCCESS`), das Gerät ihn aber nie erhielt. Der Health-Check nutzt jetzt denselben `_modbus_read_lock` und ist damit strikt gegen alle anderen Modbus-Operationen auf der Verbindung serialisiert.
- **General Sensors wurden nie nach Firmware-Version gefiltert**: Anders als HP-/Boiler-/Puffer-/Solar-/Heizkreis-Sensoren lief die General-Sensor-Gruppe (`SENSOR_TYPES`) nie durch `get_compatible_sensors()` — weder bei der Entity-Erzeugung (`sensor.py`) noch beim Register-Read (`coordinator.py`). Ein `firmware_version`/`firmware_versions`-Feld bei einem General Sensor (inkl. `ambient_temperature` oben) hatte dadurch nie eine Wirkung. Beide Stellen filtern jetzt korrekt.

---

### [2.7.0] - 2026-07-12

#### Fehlerbehebungen
- **Umlaute im Gerätenamen führen nicht mehr zu fehlgeschlagenem Energie-Sensor-Lookup** ([#93](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/93)): Enthielt der Gerätename der Integration Umlaute (z. B. `Wärmepumpe`), lieferte der interne Fallback-Lookup für den eigenen Energieverbrauchs-Sensor stets `None`. Home Assistants Entity Registry transliteriert Umlaute beim ersten Anlegen einer Entity intern (z. B. `ä` → `a`), sodass die tatsächliche Entity-ID `sensor.warmepumpe_hp1_…` lautete, der Lookup aber `sensor.wärmepumpe_hp1_…` konstruierte. Eine neue Hilfsfunktion `slugify_name_prefix_for_lookup()` wendet nun dieselbe Transliteration für rein lesende Status-Lookups an, sodass die Namen übereinstimmen. Der Fix beschränkt sich auf die zwei rein lesenden Lookup-Stellen (`coordinator.py`); alle `unique_id`-erzeugenden Pfade bleiben unverändert, um bestehende Entities nicht zu verwaisen.
- **Falscher Default für 32-Bit-Register-Reihenfolge bei neuester Firmware**: Der in diesem Release eingeführte firmware-abhängige Default für `int32_register_order` stand für alle Firmware-Einträge auf `"high_first"`, auch für die beiden neuesten (`V1.1.0-3K`, `V0.0.10-3K`). Diese beiden stehen in `FIRMWARE_CONFIG` nun auf `"low_first"`, passend zur tatsächlich von dieser Firmware-Generation verwendeten Register-Reihenfolge. Ein manueller `int32_register_order`-Override in `lambda_wp_config.yaml` hat weiterhin Vorrang und ist davon nicht betroffen.
- **Umlaute im Gerätenamen erzeugten weiterhin eine ungültige entity_id** (Nachzügler zu [#93](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/93)): Der ursprüngliche Fix oben korrigierte nur rein lesende Status-*Lookups*. Die Entity-*Erzeugung* war weiterhin betroffen — `generate_sensor_names()` wendete auf `name_prefix` nur `.lower()` an, ohne Umlaute zu transliterieren. Geräte mit z. B. `Wärmepumpe` im Namen bekamen dadurch Entities mit explizit gesetzter, ungültiger `entity_id` (z. B. `sensor.eu08ü_hp1_flow_line_temperature`). Home Assistant protokolliert dafür aktuell eine Deprecation-Warnung und wird das ab HA 2027.2.0 ablehnen. Die `entity_id`-Erzeugung nutzt nun dieselbe ASCII-sichere Transliteration (`slugify_name_prefix_for_lookup()`) wie die Lookups. Die `unique_id`-Erzeugung bleibt bewusst unverändert, um bestehende Entities nicht zu verwaisen.

---

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
