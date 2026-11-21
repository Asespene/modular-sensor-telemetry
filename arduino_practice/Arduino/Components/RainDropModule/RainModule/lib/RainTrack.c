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

#define EEPROM_MAGIC 0x524E // 'RN' magic bytes to check if EEPROM has valid data
#define EEPROM_ADDR_MAGIC 0
#define EEPROM_ADDR_DATA  2

bool saveHistory(const SensorHistory* record) {
    if (!record) return false;
    uint16_t magic = EEPROM_MAGIC;
    eeprom_update_word((uint16_t*)EEPROM_ADDR_MAGIC, magic);
    eeprom_update_block((const void*)record, (void*)EEPROM_ADDR_DATA, sizeof(SensorHistory));
    return true;
}

bool loadHistory(SensorHistory* record) {
    if (!record) return false;
    uint16_t magic = eeprom_read_word((const uint16_t*)EEPROM_ADDR_MAGIC);
    if (magic != EEPROM_MAGIC) {
        // First run: initialize clean history
        record->transitionCount = 0;
        record->errorCount = 0;
        record->rainCount = 0;
        record->prevState = ERROR;
        record->consecutiveDry = 0;
        return false;
    }
    eeprom_read_block((void*)record, (const void*)EEPROM_ADDR_DATA, sizeof(SensorHistory));
    return true;
}
