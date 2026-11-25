# Modular Sensor Telemetry Platform

An end-to-end embedded-to-web telemetry system built around a shared JSON measurement contract, modular firmware sensor adapters, a Python/FastAPI ingestion backend with SQLite persistence, and a planned live React/TypeScript dashboard.

The architecture decouples **sensor acquisition** (`SensorReading`) from **envelope serialization** (`transformToJson`), **contract validation** (`backend/validation.py`), **persistent storage** (`backend/storage.py`), and **visualization** so new sensors and boards can plug into the same pipeline without rewriting downstream layers.

---

## End-to-End Architecture

```text
Physical Sensor (Potentiometer verified; VL53L1X / Rain module planned)
      │
      ▼
Firmware Sensor Adapter (firmware/src/main.cpp)
      ├── readPotentiometer() -> SensorReading { value, is_valid }
      ├── Envelope assembly (device_id, sensor_id, sequence, uptime_ms, quality)
      └── transformToJson() -> 1 NDJSON line/sec over Serial (ESP32 Wi-Fi planned)
      │
      ▼
Contract Validation & Ingestion (backend/ & tools/)
      ├── Shared contract rules: backend/validation.py (validate_record)
      ├── CLI batch validator:   tools/validate_telemetry.py
      └── HTTP ingestion API:    POST /telemetry (stamps UTC received_at)
      │
      ▼
Persistent Storage (backend/storage.py — SQLite)
      ├── Stores accepted records (never stores rejected payloads)
      └── Queries latest state:  GET /devices/{device_id}/sensors/{sensor_id}/latest
      │
      ▼
Live Dashboard (Planned — React + TypeScript + WebSockets)
```

---

## Repository Structure

```text
.
├── README.md
├── PLATFORMIO_SETUP_GUIDE.md
├── backend/                        # FastAPI ingestion API, contract validation & SQLite storage
│   ├── __init__.py
│   ├── app.py                      # FastAPI routes (GET /health, POST /telemetry, GET .../latest)
│   ├── storage.py                  # SQLite schema (init_db, insert_telemetry, get_latest_record)
│   └── validation.py               # Single-source-of-truth record validator (validate_record)
├── tools/
│   └── validate_telemetry.py       # CLI NDJSON validator reusing backend.validation
├── tests/
│   ├── db/
│   │   └── test_db.py              # SQLite storage layer pytest suite
│   └── fixtures/                   # Valid, invalid, and live Uno Serial NDJSON captures
│       ├── README.md
│       ├── potentiometer-valid.ndjson
│       ├── telemetry-invalid.ndjson
│       └── uno-live-capture.ndjson
├── firmware/                       # PlatformIO firmware (Arduino Uno verified, ESP32 planned)
│   ├── platformio.ini
│   ├── lib/proximity/              # Portable C proximity classifier module
│   └── src/main.cpp                # SensorReading adapter + JSON Serial emitter
├── c-prac/
│   └── distance-classifier/        # Standalone portable C classifier & unit tests
└── arduino_practice/               # Standalone hardware experiments & checkpoints
```

---

## Shared Telemetry Contract (Schema v1)

Every telemetry record contains **10 required fields**:

```json
{
  "schema_version": 1,
  "device_id": "node-01",
  "sequence": 15,
  "uptime_ms": 18391,
  "sensor_id": "pot-01",
  "sensor_type": "potentiometer",
  "metric": "raw_adc",
  "value": 289,
  "unit": "count",
  "quality": "ok"
}
```

When accepted by `POST /telemetry`, the backend appends an authoritative UTC receipt timestamp:

```json
{
  "received_at": "2026-11-24T19:54:15.269864+00:00"
}
```

### Contract Invariants
- **Strict types:** `schema_version` (`1`), `sequence` (`>= 0`), and `uptime_ms` (`>= 0`) must be strict integers (booleans rejected).
- **Non-empty identifiers:** `device_id` and `sensor_id` must be non-empty strings.
- **Supported sensor metadata:** Currently `sensor_type: "potentiometer"`, `metric: "raw_adc"`, `unit: "count"`.
- **Quality & value consistency:**
  - `"quality": "ok"` requires a finite numeric `value` within `[0, 1023]` (`0` and `1023` are valid boundary readings).
  - `"quality": "unavailable"` requires `"value": null`.
- **Formatting failure vs. unavailable measurement:**
  - Sensor read unusable (`is_valid == false`) → firmware emits a complete JSON record with `"quality": "unavailable", "value": null`.
  - Buffer/formatting failure (`transformToJson()` returns `false`) → firmware emits nothing rather than a truncated line.

---

## Quick Start & Commands

### 1. Firmware (PlatformIO / Arduino Uno)
```bash
# Compile firmware
pio run -d firmware

# Flash to connected Arduino Uno
pio run -d firmware -t upload
```

### 2. Python Environment & CLI Validator
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn httpx pytest

# Validate NDJSON fixtures & live Uno capture
python3 tools/validate_telemetry.py tests/fixtures/potentiometer-valid.ndjson
python3 tools/validate_telemetry.py tests/fixtures/telemetry-invalid.ndjson
python3 tools/validate_telemetry.py tests/fixtures/uno-live-capture.ndjson
```

### 3. FastAPI Backend & Tests
```bash
# Run the local API server (http://127.0.0.1:8000 / http://127.0.0.1:8000/docs)
uvicorn backend.app:app --reload

# Run automated pytest suite
python -m pytest -v
```

### 4. Portable C Module Tests
```bash
cd c-prac/distance-classifier
gcc -Wall -Wextra -std=c11 proximity.c test_proximity.c -o test && ./test
```

---

## Project Milestones

- [x] **Milestone A — Portable C & Hardware Foundations:** Pure C proximity classifier (`proximity.c`/`proximity.h`), desktop unit tests, and initial Uno integration.
- [x] **Milestone B — Telemetry Contract (v1):** Locked 10-field JSON schema, quality/value rules, and sequence semantics.
- [x] **Milestone C — Modular Firmware JSON Output:** Implemented `SensorReading` boundary, `readPotentiometer()`, and safe `transformToJson()` over Serial.
- [x] **Milestone D — Python Validator & Live Uno Capture:** Built `tools/validate_telemetry.py`, test fixtures, and validated a 25-record live Uno potentiometer sweep (`tests/fixtures/uno-live-capture.ndjson`).
- [ ] **Milestone E/F — FastAPI Ingestion & SQLite Persistence (In Progress):** Shared `backend/validation.py`, `POST /telemetry`, SQLite `backend/storage.py`, `GET /devices/{device_id}/sensors/{sensor_id}/latest`, and `pytest` coverage.
- [ ] **Milestone G — Live Producer Bridge:** Stream real-time records via a Serial-to-HTTP bridge (and later ESP32 over Wi-Fi).
- [ ] **Milestone H — Live React/TypeScript Dashboard:** Modular sensor cards, freshness tracking (`ONLINE` / `STALE` / `OFFLINE`), and WebSocket updates.
- [ ] **Milestone I — Second Sensor Adapter & Cloud Deployment:** Add a second verified sensor and deploy to Render.
