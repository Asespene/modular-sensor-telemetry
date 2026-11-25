# MotionSensor (HC-SR501 PIR)

Arduino / PlatformIO practice module for reading a PIR motion sensor (`HC-SR501`) with non-blocking `millis()` timing, edge/transition detection, and LED indicators.

## Current Setup

### Pinout (`src/main.cpp`)
| Component | Arduino Pin | Mode | Notes |
| :--- | :---: | :--- | :--- |
| PIR `OUT` | `10` | `INPUT` | Sensor is powered via `VCC` (5V) and `GND` |
| LED 1–3 | `9`, `8`, `7` | `OUTPUT` | Use a 220Ω–330Ω current-limiting resistor per LED |

### HC-SR501 Hardware Notes
* **Jumper (`H` vs `L`):**
  * **`H` (Repeatable Trigger — middle + inner pin):** Keeps `OUT` `HIGH` continuously while motion continues by resetting the hold timer. Best for *"still moving"* tracking.
  * **`L` (Single Trigger — middle + outer pin):** Forces `OUT` `LOW` after one hold cycle + ~2.5–3s lockout before retriggering.
* **Time Delay knob (left):** Anti-clockwise = minimum (~2–3s); clockwise = up to ~5 minutes.
* **Sensitivity / Range knob (right):** Adjusts detection distance (~3m–7m).
* **Orientation:** The two internal IR elements align parallel to the 3-pin header / knobs. Mount horizontally with pins/knobs on the top or bottom so people walk **left ↔ right** across the dome.
* **Limitations:** Tuned for walking-speed heat changes (~0.3–5 Hz), ~110°–120° cone, blocked by glass, and needs ~30–60s warm-up after power-on.

---

## Things to Expand On Later

### 1. Warm-Up State & Finite State Machine (`enum class`)
* Add an explicit `WARMING_UP` state for the first 30–60 seconds after boot (e.g., slow LED blink) before entering `IDLE` / `ACTIVE` to ignore startup false positives.
* Replace raw `HIGH`/`LOW` comparisons with a clean state machine (`WARMING_UP`, `IDLE`, `ACTIVE`).

### 2. Motion Duration Tracking
* Record `motionStartTime = millis()` on `LOW → HIGH` and compute `millis() - motionStartTime` on `HIGH → LOW` to log how long each movement episode lasted.
* Optional: add a software grace period (e.g., wait 5s of uninterrupted `LOW` before ending a session) so brief pauses don't split one session into two.

### 3. EEPROM Persistence & Serial Commands
* Use `#include <EEPROM.h>` (`EEPROM.put()` / `EEPROM.get()`) to persist:
  * Total motion event count (e.g., room visitor logger or desk-session counter)
  * Total active duration across power cycles
* **Wear rule:** Only write to EEPROM on state transitions (e.g., `HIGH → LOW`) or on a slow periodic interval—never on every `loop()` pass (~100k write-cycle rating on AVR).
* Add simple Serial commands via `Serial.available()` (e.g., `'s'` to print stats, `'r'` to reset EEPROM).

### 4. Hardware Interrupts & Low-Power Mode
* Move `MotionSensorPin` to an external interrupt pin (`2` or `3` on Arduino Uno) and use `attachInterrupt(..., CHANGE)` so the MCU reacts without polling.
* Pair with AVR sleep modes (`<avr/sleep.h>`) to wake from sleep only when motion occurs.

### 5. Reusable `MotionSensor` Class (Modular Telemetry)
* Extract sensor logic into a reusable class (`include/MotionSensor.h` & `src/MotionSensor.cpp`) with methods like `begin()`, `update()`, `justStarted()`, `justEnded()`, `isActive()`, and `activeDurationMs()`.
* Emit structured telemetry over Serial (CSV or JSON lines) so a host script or dashboard can log and graph events alongside other sensors.

### 6. Multi-Sensor Upgrades
* For **fast objects** or **doorway In/Out people-counting** (where PIR's ~3s lockout and wide cone fall short), pair or swap with:
  * Dual **IR break-beam** sensors at waist height (A → B = enter, B → A = exit)
  * **Ultrasonic (`HC-SR04`)** or **ToF Laser (`VL53L0X`)** for exact distance measurement
  * **mmWave Radar** for stationary presence / breathing detection
