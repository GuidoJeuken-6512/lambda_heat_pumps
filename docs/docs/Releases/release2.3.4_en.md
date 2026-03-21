# Release 2.3.4

*Last modified: 2026-03-21*

> Version 2.3.1/3 were skipped.

---

## Improvements

### Edge detection: compressor start sensor changed (`4b1dddd`)

The sensor used to detect a compressor start has been changed:

| | Before (2.3) | Now (2.3.4) |
|---|---|---|
| **Source** | `HP_STATE` (register 1002) | `compressor_unit_rating` (register 1010) |
| **Detection condition** | Transition to state `2` (RESTART-BLOCK) | Rise from `0 → >0` (rising edge) |
| **Semantics** | Counts completed cycles (after lockout) | Counts active compressor starts (at turn-on moment) |

`compressor_unit_rating` returns the current compressor power in percent (0–100%). A rising edge from 0 to a value greater than 0 indicates that the compressor has just started. This is more precise and less dependent on internal HP state transitions.

```
Compressor off:  rating = 0
Compressor on:   rating > 0  ← edge here, counter is incremented
```

---

### Fast polling for edge detection (`4b1dddd`)

Edge detection has been decoupled from the regular 30-second update and moved into a dedicated fast polling loop with a **2-second interval**.

#### Architecture

```
┌──────────────────────────────────────────────────────────┐
│  _async_fast_update()  [every 2 seconds]                │
│    └─ reads only registers 1003 + 1010 per heat pump      │
│    └─ _run_cycling_edge_detection()                      │
│         └─ increment_cycling_counter()                     │
├──────────────────────────────────────────────────────────┤
│  _async_update_data()  [every 30 seconds, configurable]  │
│    └─ full Modbus read of all registers                  │
│    └─ energy integration (kWh) — no edge detection       │
└──────────────────────────────────────────────────────────┘
```

#### Why fast polling?

Short operating-mode transitions (e.g. brief defrost phases or rapid successive starts) could be missed in the 30-second grid. With 2-second polling, every edge is captured reliably and hourly sensors are more accurate.

#### What is read in the fast poll?

Per heat pump, only **two registers** are read:

| Register | Address | Content | Use |
|----------|---------|---------|-----|
| `HP_OPERATING_STATE` | 1003 | Operating mode (heating / DHW / cooling / defrost) | Mode edge detection |
| `compressor_unit_rating` | 1010 | Compressor power in % | Compressor start detection |

#### New constant

```python
DEFAULT_FAST_UPDATE_INTERVAL = 2  # seconds
```

The interval is fixed and not configurable in the UI.

#### Collision protection with full update

A `_full_update_running` flag prevents the fast poll from interfering with an ongoing 30-second full update:

```python
self._full_update_running = False  # True while _async_update_data holds the Modbus connection
self._unsub_fast_poll = None       # Handle to cancel the fast-poll timer
```

---

## Fixes

### Translation `vda_rating`: “Max” added

The `vda_rating` sensor shows the **maximum** VdA power value of the heat pump. The labels have been corrected in both languages:

| Language | Before | After |
|----------|--------|-------|
| English | `VdA Rating` | `VdA Rating Max` |
| German | `VdA Leistung` | `VdA Leistung Max` |

---

## Internal refactorings

### `_run_cycling_edge_detection()` as a dedicated method

Edge detection has been extracted into the dedicated method `_run_cycling_edge_detection()`. It is called only from `_async_fast_update()` and updates `_last_operating_state` and `_last_compressor_rating`.

### `_last_state` renamed to `_last_compressor_rating`

The internal state-tracking dictionary for compressor start was renamed from `_last_state` to `_last_compressor_rating` to reflect the new sensor (`compressor_unit_rating`) semantically.

```python
# Before
self._last_state = {}  # HP_STATE edge detection

# After
self._last_compressor_rating = {}  # compressor_unit_rating edge detection (0 → >0)
```
