#include <Arduino.h>

#define DO_PIN 10
#define POWER_PIN 9



void setup() {
  Serial.begin(9600);

  pinMode(DO_PIN, INPUT);
  pinMode(POWER_PIN, OUTPUT);
}

void loop() {
  // Your code here

  //power on our sensor and ensure its at a stable state
  digitalWrite(POWER_PIN, HIGH);
  delay(10);

  //reads the value of DO_PIN if 1 then HIGH(NO RAIN) otherwise 0 means LOW(RAIN)
  int isRain = digitalRead(DO_PIN);


}
