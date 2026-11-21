# Telemetry Contract (Milestone B — Minimal Serial Schema)

This document defines the minimal, sensor-neutral JSON telemetry contract (`schema_version: 1`) emitted over Serial by the Arduino Uno and consumed by the Python validation tools and FastAPI backend.

---

## 1. Complete Record Examples

### Valid Potentiometer Record

```json
{
  "schema_version": 1,
  "device_id": "node-01",
  "sequence": 0,
  "uptime_ms": 1500,
  "sensor_id": "pot-01",
  "sensor_type": "potentiometer",
  "metric": "raw_adc",
  "value": 620,
  "unit": "count",
  "quality": "ok"
}
```

### Unavailable-Measurement Record

When a reading cannot be trusted or acquired, the full record envelope is still emitted, with `value` set to `null` and `quality` set to `"unavailable"`:

```json
{
  "schema_version": 1,
  "device_id": "node-01",
  "sequence": 1,
  "uptime_ms": 2500,
  "sensor_id": "pot-01",
  "sensor_type": "potentiometer",
  "metric": "raw_adc",
  "value": null,
  "unit": "count",
  "quality": "unavailable"
}
```

---

## 2. Field Reference and Expected Types

Every emitted record must contain all 10 fields below:

| Field | JSON Type | Allowed / Initial Values | Meaning |
| :--- | :--- | :--- | :--- |
| `schema_version` | `integer` | `1` | Version of this telemetry payload contract. |
| `device_id` | `string` | `"node-01"` (non-empty) | Configured identifier for the microcontroller node emitting the record. |
| `sequence` | `integer` | `>= 0` (`0, 1, 2, ...`) | Record counter starting at `0` on boot and incrementing by `1` per emitted record. |
| `uptime_ms` | `integer` | `>= 0` | Milliseconds elapsed since the device booted (`millis()`), not wall-clock time. |
| `sensor_id` | `string` | `"pot-01"` (non-empty) | Identifier for the specific sensor instance wired to the node. |
| `sensor_type` | `string` | `"potentiometer"` | Hardware adapter category producing the reading. |
| `metric` | `string` | `"raw_adc"` | What the numeric reading actually measures. |
| `value` | `integer \| number \| null` | `0`–`1023` (for Uno ADC) or `null` | The measured sensor value when `quality` is `"ok"`, or `null` when `"unavailable"`. |
| `unit` | `string` | `"count"` | Unit of measurement corresponding to `metric`. |
| `quality` | `string` | `"ok"` \| `"unavailable"` | Usability status of the current measurement. |

---

## 3. Initial Contract Rules

1. **One JSON Object per Serial Line (NDJSON):**
   - Each line printed over Serial must be a single, complete, valid JSON object terminated by a newline (`\n`).
   - Human-readable debug Banners or multi-line `Serial.println()` diagnostics must not be mixed into the telemetry stream.
2. **Honest First Measurement (Raw Potentiometer Input):**
   - The initial supported input is the potentiometer's raw analog-to-digital converter reading (`"metric": "raw_adc"`, `"unit": "count"`), not physical or simulated distance.
3. **Sequence Counter Policy:**
   - `sequence` initializes to `0` for the first emitted record after startup and increments by `1` for every record emitted (whether `"ok"` or `"unavailable"`).
4. **Reset Behavior:**
   - Both `sequence` and `uptime_ms` reset to their initial startup values whenever the Arduino resets or reboots.
5. **Value and Quality Consistency:**
   - When `quality` is `"ok"`, `value` **must** be a valid number (e.g., `0`–`1023` for the Uno's 10-bit ADC) and must never be `null`.
   - When `quality` is `"unavailable"`, `value` **must** be `null` (never a fake numeric fallback like `0` or `-1`).
   - Note that a record with `"quality": "unavailable"` and `"value": null` is still a **valid telemetry message** describing an unavailable sensor reading.
6. **Deferred Features (Out of Scope for Milestone B/C):**
   - **Boot Identification & Deduplication:** `boot_id` and duplicate-record suppression on the backend are deferred until networked/ESP32 delivery.
   - **Additional Sensors & Derived Classifications:** Support for the VL53L1X distance sensor, rain module (`RainDropModule`), ultrasonic sensor, and optional derived state fields (such as proximity classifications from `proximity.c`) will be layered on after this baseline pipeline is verified end to end.
