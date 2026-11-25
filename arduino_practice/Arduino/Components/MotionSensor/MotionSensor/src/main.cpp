#include <Arduino.h>

constexpr uint8_t MotionSensorPin = 10;
constexpr uint8_t ledPins[] = {9, 8, 7};

void setAllLeds(uint8_t state) {
    for (uint8_t pin : ledPins) {
        digitalWrite(pin, state);
    }
}


int currentMotionState = LOW;
int prevMotionState = LOW;


//cases of a motion sensor if HIGH motion is detetced

// LOW -> HIGH 

void setup() {
    Serial.begin(9600);

    //the pin takes in sensor data and it is powered by the VCC
    pinMode(MotionSensorPin, INPUT);

    for (uint8_t pin: ledPins) {
        pinMode(pin, OUTPUT);
    }
    delay(500);


}

//the current time from the start of the program
unsigned long lastPrintTime = 0;
//the time i want each time a print occurs
const unsigned long INTERVAL_PRINTING = 1000;

void loop() {
    // Main firmware loop

    unsigned long now = millis();

    currentMotionState = digitalRead(MotionSensorPin);

    //cases for motion sensing, this case is only for movement detetced which is if its going from LOW -> HIGH
   
    //movement case, going from LOW to HIGH
    if (currentMotionState == HIGH && prevMotionState == LOW) {
        Serial.println("New Movement is detected!");
        setAllLeds(HIGH);

        lastPrintTime = now;
    }
    //stopped moving case, going from HIGH to LOW
    else if (currentMotionState == LOW && prevMotionState == HIGH) {
        Serial.println("Movement is ending!");
        setAllLeds(LOW);

        lastPrintTime = now;

    }
    else if (now - lastPrintTime >= INTERVAL_PRINTING) {
        lastPrintTime = now;
        if (currentMotionState == HIGH && prevMotionState == HIGH) {
            Serial.println("Still Moving!");
            setAllLeds(HIGH);
        }
         //continious movement HIGH -> HIGH
        else if (currentMotionState == LOW && prevMotionState == LOW) {
            Serial.println("Idling!");
            setAllLeds(LOW);
        } 
    }
   
    prevMotionState = currentMotionState;

    
}
