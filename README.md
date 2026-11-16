# Modular Sensor Telemetry Platform

An embedded-to-web telemetry project designed around configurable sensor inputs, a shared numeric measurement contract, a Python/FastAPI backend, persistent storage, and a live React/TypeScript dashboard.

The architecture separates sensor-specific hardware acquisition from portable C processing, backend validation, storage, and frontend visualization so that additional supported sensors can reuse the same end-to-end pipeline.

---

## Project Status

This repository distinguishes **completed, verified work** from **planned milestones**.

### Confirmed Completed Work
- **Portable C Proximity & History Module (`c-prac/distance-classifier/`, `firmware/lib/proximity/`):**
  - Pure C implementation (`proximity.h`, `proximity.c`) with zero Arduino dependencies.
  - Defines `ProximityState` (`FAR`, `MEDIUM`, `NEAR`, `TOO_CLOSE`, `ERROR`), `SensorData`, and `SensorHistory`.
  - Implements `classifyDistance()`, `enumToString()`, and pointer-based `updateHistory()` tracking valid readings, invalid readings, and state transitions without dynamic memory allocation (`malloc`/`free`).
  - Verified on desktop via standalone demo (`main.c`) and automated `assert`-based unit tests (`test_proximity.c`).
- **Arduino Uno + Potentiometer Integration (`firmware/`):**
  - Integrates the portable C `proximity` library into an Arduino/PlatformIO sketch (`firmware/src/main.cpp`) using `extern "C"`.
  - Reads live analog input (`A0`) from a potentiometer, maps readings into test range values (including fault-injection negative values), updates `SensorHistory`, and prints classifications and counters over Serial.
- **Arduino Foundations & Checkpoints (`arduino_practice/Arduino/`):**
  - Introductory GPIO, PWM, analog input, and binary LED state indicator exercises (`checkpoints/001-checkpoint-ledStateIndicator`).
- **Component Side-Experiments (`arduino_practice/Arduino/Components/`):**
  - Dedicated workspace for testing standalone Arduino sensor/component implementations (`UltrasonicSensor`, `RainDropModule` with `RainTrack.c` / `RainTrack.h`) independently of the main telemetry pipeline.
  - *Ultrasonic sensor note:* Produced short-range readings (~1–4 inches) and later appeared stuck at a fixed reading. The root cause is currently unverified (neither confirmed broken hardware nor confirmed normal behavior). Main pipeline development proceeds using the verified potentiometer input while preserving these component experiments.

### Planned (Not Yet Implemented)
- Newline-delimited JSON telemetry output over Serial.
- Python CLI validator (`tools/validate_telemetry.py`) and sample captures.
- Python/FastAPI ingestion server, validation, and persistent database storage.
- ESP32 Wi-Fi / HTTPS telemetry producer (or optional local USB-to-HTTP Serial bridge).
- Live React/TypeScript dashboard with WebSocket updates.
- Second verified sensor adapter reusing the common pipeline.
- Cloud deployment on Render.

---

## Repository Structure

```text
.
├── README.md
├── .gitignore
├── c-prac/
│   └── distance-classifier/        # Desktop-compiled portable C module & unit tests
│       ├── proximity.h
│       ├── proximity.c
│       ├── main.c
│       └── test_proximity.c
├── firmware/                       # PlatformIO firmware (Uno verified, ESP32 planned)
│   ├── platformio.ini
│   ├── lib/
│   │   └── proximity/              # Shared portable C proximity module
│   └── src/
│       └── main.cpp                # Live potentiometer + C classifier loop
└── arduino_practice/
    └── Arduino/
        ├── checkpoints/            # Hardware state indicator checkpoint & learning log
        ├── mini_hw/                # Introductory Arduino sketches
        └── Components/             # Standalone sensor/component side-projects
            ├── RainDropModule/
            └── UltrasonicSensor/
```

---

## Target System Architecture

```text
Supported Sensor Input (Potentiometer first, second verified sensor later)
      │
      ▼
Acquisition Firmware (Uno Serial prototype → ESP32 Wi-Fi node)
      │  (Optional portable C processing / state tracking)
      ▼
Common JSON Telemetry Record
      │  HTTPS POST
      ▼
Python / FastAPI Backend
      ├── Schema & quality/value consistency validation
      ├── Server receipt timestamp (received_at)
      ├── Persistent storage (latest state + bounded history)
      └── WebSocket broadcast (/ws/telemetry)
      │
      ▼
React + TypeScript Dashboard
```

### Technology Stack

| Layer | Technology | Status |
| :--- | :--- | :--- |
| Portable Logic | C (`proximity.h` / `proximity.c`) | Implemented & tested |
| Firmware | C/C++, Arduino framework, PlatformIO | Uno + potentiometer working; ESP32 planned |
| Telemetry Format | Newline-delimited JSON (Serial) / JSON over HTTPS | Planned (Next milestone) |
| Backend | Python, FastAPI, Pydantic | Planned |
| Storage | Local persistence → PostgreSQL / Supabase | Planned |
| Frontend | React, TypeScript, WebSockets | Planned |
| Hosting | Render (Web Service + Static Site) | Planned |

---

## Implemented C Module Reference (`proximity`)

The current C classifier (`classifyDistance(int distance)`) uses the following integer bounds:

| `ProximityState` | Condition | `isValid` |
| :--- | :--- | :--- |
| `TOO_CLOSE` | `0 <= distance <= 10` | `true` |
| `NEAR` | `11 <= distance <= 30` | `true` |
| `MEDIUM` | `31 <= distance <= 100` | `true` |
| `FAR` | `101 <= distance <= 400` | `true` |
| `ERROR` | `distance < 0` or `distance > 400` | `false` |

### Building and Running the Desktop C Tests

From `c-prac/distance-classifier/`:

```bash
gcc -Wall -Wextra -std=c11 proximity.c test_proximity.c -o test
./test

gcc -Wall -Wextra -std=c11 proximity.c main.c -o main
./main
```

---

## Proposed Shared Telemetry Contract (Version 1)

Each emitted telemetry record represents one numeric measurement using a sensor-neutral schema:

```json
{
  "schema_version": 1,
  "device_id": "node-01",
  "boot_id": "session-001",
  "sequence": 42,
  "uptime_ms": 21000,
  "sensor_id": "pot-01",
  "sensor_type": "potentiometer",
  "metric": "raw_adc",
  "value": 620,
  "unit": "count",
  "quality": "ok",
  "derived_state": null
}
```

### Core Contract Rules
- **Honest metric labeling:** Raw potentiometer counts use `"metric": "raw_adc"` and `"unit": "count"`. If mapped to a simulated distance for classifier testing, label the metric explicitly (e.g., `"simulated_distance"`).
- **Explicit fault representation:** Invalid or unavailable readings use `"value": null` (or documented fault semantics) and a non-`ok` `"quality"` rather than silently substituting `0`.
- **Three independent health dimensions:**
  1. **Measurement quality:** Whether the sensor reading itself is valid (`quality`, `derived_state`).
  2. **Device-to-backend freshness:** `NO_DATA`, `ONLINE`, `STALE`, or `OFFLINE` computed from the backend's `received_at` timestamp.
  3. **Browser-to-backend connectivity:** Whether the dashboard WebSocket connection is active.

---

## Implementation Roadmap

- [x] **Milestone A — Preserve Completed Work:** Checkpoint portable C module, unit tests, Uno + potentiometer integration, and documented ultrasonic experiment status.
- [ ] **Milestone B — Finalize Common Telemetry Format:** Lock field names, metric/unit pairs, quality semantics, and sequence behavior.
- [ ] **Milestone C — Emit JSON over Serial:** Output one parseable JSON telemetry record per line from the working Uno + potentiometer setup.
- [ ] **Milestone D — Validate Captured Records with Python:** Build `tools/validate_telemetry.py` and verify captured valid/fault samples in `docs/examples/telemetry-samples.jsonl`.
- [ ] **Milestone E — Build FastAPI Locally:** Implement `GET /api/health`, `POST /api/telemetry`, and latest-reading retrieval with Pydantic validation.
- [ ] **Milestone F — Add Persistence:** Persist accepted readings across restarts and support bounded recent-history queries.
- [ ] **Milestone G — Connect a Real Producer:** Stream live records via a local Serial-to-HTTP bridge or directly from an ESP32 over Wi-Fi.
- [ ] **Milestone H — Build the Local Dashboard:** Display sensor cards, measurement quality, device freshness, WebSocket status, and recent history.
- [ ] **Milestone I — Add Second Supported Adapter:** Integrate a second verified sensor reusing the same telemetry schema, backend, and dashboard.
- [ ] **Milestone J — Deploy:** Deploy FastAPI and the React dashboard to Render with durable storage and authenticated ingestion.
- [ ] **Milestone K — Release Version 1:** Complete end-to-end documentation, wiring guides, test results, and tagged release.
