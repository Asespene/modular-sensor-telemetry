#include "RainTrack.h"


//noisy readings, not the ground truth. Whatever its giving us we must confirm to be true before updating to records
RainSensorData classifyState(int reading) {
    RainSensorData data;

    switch (reading) {
        case 1:
            data.identifier = NO_RAIN;
            data.isRain = 1;
            break;
        case 0: 
            data.identifier = RAINING;
            data.isRain = 0;
            break;
        default:
            data.identifier = ERROR;
            break;
    }

    return data;
}


void updateHistory(RainSensorData* data, SensorHistory* record) {
    //check if the struct we are pointing is not null otherwise program can't runb return;
    if (!data || !record) {
        return;
    }
    //check if reading error, drop it immediately
    if (data->identifier == ERROR) {
        record->errorCount++;
        return;
    }

    //initialization gaurd clause, its set to ERROR first. So at the 2nd CYCLE we update

    if (record->prevState == ERROR) {
        record->prevState = data->identifier;
        return;
    }

    //current state rain case
    if (data->identifier == RAINING) {
        //the moment it is raining the dry counter resets to 0
        record->consecutiveDry = 0;
        //increment rain 
        record->rainCount++;

        //if it was DRY -> RAIN this is a transition
        if (record->prevState != RAINING) {
            record->transitionCount++;
        } 

        record->prevState = data->identifier;
    } 
    // not raining case
    else if (data->identifier == NO_RAIN) {
        //we dont count consec NO_RAINING signal as transitions
        record->consecutiveDry++;

        if (record->consecutiveDry >= 3) {
            //
            if (record->prevState == RAINING) {
                record->transitionCount++;
                record->prevState = NO_RAIN;
            }
        }
    }

}