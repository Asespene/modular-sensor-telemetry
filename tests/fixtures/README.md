# Telemetry Test Fixtures Guide

This document explains the test fixtures located in `tests/fixtures/` used to verify `tools/validate_telemetry.py`.

---

## 1. `tests/fixtures/potentiometer-valid.ndjson`
Contains 4 valid records that must 100% pass without errors:

| Line | Record Feature | Why it matters |
| :---: | :--- | :--- |
| **1** | Mid-range reading (`value: 620`, `quality: "ok"`) | Standard baseline telemetry reading. |
| **2** | Lower bound reading (`value: 0`, `quality: "ok"`) | Verifies `0` is accepted as a valid integer and not falsely flagged as empty/falsy. |
| **3** | Upper bound reading (`value: 1023`, `quality: "ok"`) | Verifies the maximum 10-bit ADC value passes boundary checks. |
| **4** | Unavailable reading (`value: null`, `quality: "unavailable"`) | Verifies that sensor-failure envelopes pass when `value` is explicitly `null`. |

---

## 2. `tests/fixtures/telemetry-invalid.ndjson`
Contains 9 lines that must each be rejected with line-specific errors:

| Line | Defect in Fixture | Why this Edge Case is Important | Expected Validator Error |
| :---: | :--- | :--- | :--- |
| **1** | Missing `"sensor_id"` | Tests that all 10 required envelope fields are strictly enforced. Prevents anonymous data. | `missing required field 'sensor_id'` |
| **2** | `"sequence": "1"` (string) | **Type Coercion Trap:** Tests that the validator does *not* quietly convert strings to ints. In embedded telemetry, a string sequence means firmware serialization broke. | `field 'sequence' must be an integer` |
| **3** | `"quality": "ok"`, `"value": null` | **Cross-field Invariant:** If quality is `ok`, there *must* be a physical reading. An `ok` with `null` is a contract contradiction. | `quality 'ok' requires a numeric value, got null` |
| **4** | `"quality": "unavailable"`, `"value": 500` | **Cross-field Invariant:** If quality is `unavailable`, `value` *must* be `null`. Sending a number when unavailable means stale or phantom data. | `quality 'unavailable' requires value to be null` |
| **5** | `"schema_version": 2` | **Version Negotiation:** Tests that the validator rejects unsupported schema versions rather than misinterpreting fields. | `unsupported 'schema_version': expected 1, got 2` |
| **6** | `"value": 1024` | **ADC Range Overflow:** Arduino Uno has a 10-bit ADC ($2^{10} - 1 = 1023$). 1024 is physically impossible on an Uno; flags firmware math or ADC scaling bugs. | `value 1024 is out of expected ADC range [0, 1023]` |
| **7** | `[1, 2, 3]` (JSON Array) | **Top-Level Structural Check:** Valid JSON syntax, but it's an array instead of a JSON object (`dict`). | `Top-level record must be a JSON object` |
| **8** | `"value": true` (Boolean) | **The Python `isinstance` Trap:** In Python, `isinstance(True, int)` is `True` because `bool` inherits from `int`. Must reject booleans. | `quality 'ok' requires a numeric value, got bool` |
| **9** | Unfinished JSON `{"schema_ver...` | **Syntax / Buffer Truncation:** Mimics what happens when an Arduino `Serial.println()` gets cut off by a serial timeout or reset mid-print. Tests `json.JSONDecodeError` handling so the validator doesn't crash. | `malformed JSON: Expecting ...` |
