#include <Arduino.h>

extern "C" {
  #include "proximity.h"
}


//schema table i need to initialie
/* 
schema_version
device_id
sequence
uptime_ms
sensor_id
sensor_type
metric
value
*/

//schema table example
typedef struct {
  int schema_version;
  const char* device_id;
  unsigned long uptime_ms;
  const char* sensor_id;
  const char* sensor_type;
  const char* metric;
  int value;
  const char* unit;
  const char* quality;
  unsigned long sequence;
} TelemetryRecord;

bool transformToJson(const TelemetryRecord* record, char* buffer, size_t bufferSize);

//instantiate a current record struct as a hard coded test
static TelemetryRecord currentRecord;

void setup() {
  Serial.begin(9600);

  delay(1500);
  
  //hardcode test data for hardware:
  currentRecord.schema_version = 1;
  currentRecord.device_id = "node-01";
  currentRecord.sensor_id = "pot-01";
  currentRecord.sensor_type = "potentiometer";
  currentRecord.metric = "raw_adc";
  currentRecord.unit = "count";
  currentRecord.sequence = 0;
}

void loop() {
  //live sensor data being read
  currentRecord.value = analogRead(A0);
  //returns the elapsed number of time in milliseconds when the Arduino board began running
  currentRecord.uptime_ms = millis();
  currentRecord.quality = "ok";

  char jsonBuffer[256];
  bool writeStatus = transformToJson(&currentRecord, jsonBuffer, sizeof(jsonBuffer));
  
  if (writeStatus) {
    Serial.println(jsonBuffer);
    currentRecord.sequence++;
  }


  delay(1000);


  /*
  int distanceValue = map(currentRecord.value, 0, 1023, -1000, 1000);

  SensorData data = classifyDistance(distanceValue);
  static SensorHistory liveRecords = {};

  updateHistory(&data, &liveRecords);

  static size_t counter = 0;


  
  Serial.print("Data #: ");
  Serial.println(counter);

  Serial.print("Distance: ");
  Serial.println(data.distance);

  Serial.print("STATE: ");
  Serial.println(enumToString(data.identifier));

  Serial.print("Valid Reading: ");
  Serial.println(liveRecords.validReadings);

  Serial.print("Invalid Reading: ");
  Serial.println(liveRecords.invalidReadings);

  Serial.print("Transition Counts: ");
  Serial.println(liveRecords.transitionsCount);


  Serial.println();
  */
}


bool transformToJson(const TelemetryRecord* record, char* buffer, size_t bufferSize) {
  if (record == NULL || buffer == NULL || bufferSize == 0) {
    return false;
  }

  if (!record->quality) {
    return false;
  }


  int writeStatus = 0;

  //check quality to determine if the value is "ok" or "null"
  //if both string is identical then return 0
  if (strcmp(record->quality, "ok") == 0) {
    writeStatus = snprintf(buffer, bufferSize,
      "{\"schema_version\":%d,\"device_id\":\"%s\",\"sequence\":%lu,\"uptime_ms\":%lu,\"sensor_id\":\"%s\",\"sensor_type\":\"%s\",\"metric\":\"%s\",\"value\":%d,\"unit\":\"%s\",\"quality\":\"%s\"}",
      record->schema_version,
      record->device_id,
      record->sequence,
      record->uptime_ms,
      record->sensor_id,
      record->sensor_type,
      record->metric,
      record->value,
      record->unit,
      record->quality
    );
  } else if (strcmp(record->quality, "unavailable") == 0) 
  {
    writeStatus = snprintf(buffer, bufferSize,
      "{\"schema_version\":%d,\"device_id\":\"%s\",\"sequence\":%lu,\"uptime_ms\":%lu,\"sensor_id\":\"%s\",\"sensor_type\":\"%s\",\"metric\":\"%s\",\"value\":null,\"unit\":\"%s\",\"quality\":\"%s\"}",
      record->schema_version,
      record->device_id,
      record->sequence,
      record->uptime_ms,
      record->sensor_id,
      record->sensor_type,
      record->metric,
      record->unit,
      record->quality
    );
  } else {
    return false;
  }

  if (writeStatus < 0 || static_cast<size_t>(writeStatus) >= bufferSize) {
    return false;
  } else {
    return true;
  }
}
