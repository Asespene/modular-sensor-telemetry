#include <Arduino.h>
#include "lib/RainTrack.h"

#define DO_PIN 10
#define POWER_PIN 9

SensorHistory history;

void setup() {
  Serial.begin(9600);

  pinMode(DO_PIN, INPUT);
  pinMode(POWER_PIN, OUTPUT);

  if (loadHistory(&history)) {
    Serial.println("Loaded saved history from EEPROM:");
  } else {
    Serial.println("No saved EEPROM data found. Starting fresh:");
  }
  Serial.print("Rain count: ");
  Serial.print(history.rainCount);
  Serial.print(" | Transitions: ");
  Serial.println(history.transitionCount);
}

void loop() {
  // Power on sensor and wait 10ms to stabilize
  digitalWrite(POWER_PIN, HIGH);
  delay(10);

  // Read DO_PIN: 1 = HIGH (NO RAIN), 0 = LOW (RAIN)
  int isRain = digitalRead(DO_PIN);

  // Power off sensor between readings to prevent corrosion
  digitalWrite(POWER_PIN, LOW);

  // Classify and update history
  RainSensorData reading = classifyState(isRain);
  updateHistory(&reading, &history);

  // Save updated history to EEPROM (eeprom_update only writes if bytes changed)
  saveHistory(&history);

  // Print live status
  Serial.print("State: ");
  Serial.print(reading.identifier == RAINING ? "RAINING" : "NO_RAIN");
  Serial.print(" | RainTicks: ");
  Serial.print(history.rainCount);
  Serial.print(" | Transitions: ");
  Serial.print(history.transitionCount);
  Serial.print(" | DryStreak: ");
  Serial.println(history.consecutiveDry);

  delay(2000); // Check every 2 seconds
}

