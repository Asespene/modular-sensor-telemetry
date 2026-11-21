#ifndef RAIN_TRACK_H
#define RAIN_TRACK_H


#include <stdio.h>
#include <stdbool.h>
#include <avr/eeprom.h>

typedef enum {
    ERROR,
    RAINING,
    NO_RAIN,
} SensorState;

typedef struct {
    int isRain;
    SensorState identifier;
} RainSensorData;

typedef struct {
    int transitionCount;
    int errorCount;
    int rainCount;

    SensorState prevState;

    int consecutiveDry;
} SensorHistory;


#ifdef __cplusplus
extern "C" {
#endif

RainSensorData classifyState(int reading);

void updateHistory(RainSensorData* data, SensorHistory* record);

//save the history record outside of RAM and in EEPROM which is like a local storage for arduino
bool saveHistory(const SensorHistory* record);
bool loadHistory(SensorHistory* record);

#ifdef __cplusplus
}
#endif

#endif


