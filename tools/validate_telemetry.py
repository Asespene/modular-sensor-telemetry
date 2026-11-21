import json
import math
import sys


#check if our JSON record contains these keys, these are needed for a valid telemtry record
REQUIRED_FIELDS = [
    "schema_version",
    "device_id",
    "sequence",
    "uptime_ms",
    "sensor_id",
    "sensor_type",
    "metric",
    "unit",
    "quality",
    "value",
]

#check if each keys contain these certain values since our key values must be these.
SUPPORTED_SCHEMA_VERSION = 1
SUPPORTED_SENSOR_TYPE = "potentiometer"
SUPPORTED_METRIC = "raw_adc"
SUPPORTED_UNIT = "count"
ALLOWED_QUALITIES = {"ok", "unavailable"}
ADC_MIN = 0
ADC_MAX = 1023

#make sure bool value is not seen or processed as an int
#needs to return to ensure value is an int and not a bool
def is_strict_int(value): 
    #if value is an integer and not a bool then return true otherwise return false
    validInteger = isinstance(value, int) and not isinstance(value, bool)

    return validInteger

def describe_value(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return f"boolean {json.dumps(value)}"
    if isinstance(value, int):
        return f"integer {value}"
    if isinstance(value, float):
        return f"number {value}"
    if isinstance(value, str):
        return f"string {json.dumps(value)}"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__

#takes in a telemetry record, validate it and returns any errors in a list. If no error, return empty
def validate_record(record) -> list[str]:
    errors = []

    #check if the record is a JSON object, otherwise known as containing key value pairs(dictionary)
    if (not isinstance(record, dict)):
        errors.append(f"record must be a JSON object; received {describe_value(record)}.")
        return errors

    #check each required fields
    for fields in REQUIRED_FIELDS:
        if fields not in record:
            errors.append(f"{fields} is missing.")
    #if we are missing some required fields then our error list has to be not empty if its not return the error list!
    if (errors): return errors

    #check each supported key values
    #check if schema_version is a integer
    if (not is_strict_int(record['schema_version'])):
        errors.append(f"schema_version must be an integer; received {describe_value(record['schema_version'])}.")
    else:
        #is an integer but check if its supported
        if (record['schema_version'] != SUPPORTED_SCHEMA_VERSION):
            errors.append(f"schema_version must be {SUPPORTED_SCHEMA_VERSION}; received {record['schema_version']}.")

    #check device_id
    if (not isinstance(record['device_id'], str)):
        errors.append(f"device_id must be a string; received {describe_value(record['device_id'])}.")
    else:
        if (record['device_id'].strip() == ""):
            errors.append("device_id must be a non-empty string.")

    #check sequence
    if (not is_strict_int(record['sequence'])):
        errors.append(f"sequence must be an integer; received {describe_value(record['sequence'])}.")
    else:
        if (record['sequence'] < 0):
            errors.append(f"sequence must be >= 0; received {record['sequence']}.")

    #check uptime_ms
    if (not is_strict_int(record['uptime_ms'])):
        errors.append(f"uptime_ms must be an integer; received {describe_value(record['uptime_ms'])}.")
    else:
        if (record['uptime_ms'] < 0):
            errors.append(f"uptime_ms must be >= 0; received {record['uptime_ms']}.")

    #check sensor_id
    if (not isinstance(record['sensor_id'], str)):
        errors.append(f"sensor_id must be a string; received {describe_value(record['sensor_id'])}.")
    else:
        if (record['sensor_id'].strip() == ""):
            errors.append("sensor_id must be a non-empty string.")

    #check sensor type
    if (not isinstance(record['sensor_type'], str)):
        errors.append(f"sensor_type must be a string; received {describe_value(record['sensor_type'])}.")
    else:
        if (record['sensor_type'] != SUPPORTED_SENSOR_TYPE):
            errors.append(f"sensor_type must be '{SUPPORTED_SENSOR_TYPE}'; received {json.dumps(record['sensor_type'])}.")

    #check metric
    if (not isinstance(record['metric'], str)):
        errors.append(f"metric must be a string; received {describe_value(record['metric'])}.")
    else:
        if (record['metric'] != SUPPORTED_METRIC):
            errors.append(f"metric must be '{SUPPORTED_METRIC}'; received {json.dumps(record['metric'])}.")

    #check unit
    if (not isinstance(record['unit'], str)):
        errors.append(f"unit must be a string; received {describe_value(record['unit'])}.")
    else:
        if (record['unit'] != SUPPORTED_UNIT):
            errors.append(f"unit must be '{SUPPORTED_UNIT}'; received {json.dumps(record['unit'])}.")

    #check quality
    if (not isinstance(record['quality'], str)):
        errors.append(f"quality must be a string; received {describe_value(record['quality'])}.")
    else:
        if (record['quality'] not in ALLOWED_QUALITIES):
            errors.append(f"quality must be one of {sorted(ALLOWED_QUALITIES)}; received {json.dumps(record['quality'])}.")

    #check the cases between quality and value 
    if (record['quality'] == "ok"):
        #check if value is None
        if (record['value'] is None):
            errors.append("value must be numeric for quality 'ok'; received null.")
        else:
            is_number = is_strict_int(record['value']) or isinstance(record['value'], float)
            #check if value is an int/float and not a bool
            if (not is_number):
                errors.append(f"value must be numeric for quality 'ok'; received {describe_value(record['value'])}.")
            elif (not math.isfinite(record['value']) or record['value'] < ADC_MIN or record['value'] > ADC_MAX):
                #make sure it's finite and within range
                errors.append(f"value must be between {ADC_MIN} and {ADC_MAX} for quality 'ok'; received {record['value']}.")
    elif (record['quality'] == "unavailable"):
        #if quality is unavailable then value must be None
        if (record['value'] is not None):
            errors.append(f"value must be null for quality 'unavailable'; received {describe_value(record['value'])}.")

    return errors

def process_file(filepath) -> tuple[int, int]:
    #count of each records
    total_count = 0
    failed_count = 0

    #createa a file object as f that is read and utf-8
    with open(filepath, "r", encoding="utf-8") as f:
        #iterate through the file line by line, since we are processing ann ndJson file which has a delimitter each line a \n
        for lineNum, line in enumerate(f, start=1):
            clean_line = line.strip()

            #if the line is empty or blank move along
            if (clean_line == ""):
                continue
            
            total_count += 1

            try:
                #turn each non-empty line we are iterating to a dictionary, since our validate telemtry function only takes in dict. JSON -> DICT -> validate_telemtry(dict)
                record = json.loads(line)
                #since the function we are using at try can raise a JSONDecodeError exception, our catch or exception block must catch it and display the specific error
            except json.JSONDecodeError as e:
                failed_count += 1
                print(f"Line {lineNum}: invalid JSON ({e.msg}).")
                continue

            listErrors = validate_record(record)

            #if has value, this means our list of Error has errors so failed
            if (listErrors):
                failed_count += 1

                for err in listErrors:
                    print(f"Line {lineNum}: {err}")

    return total_count, failed_count


def main() -> int:
    if (len(sys.argv) != 2):
        print("Usage: python tools/validate_telemetry.py <path-to-ndjson-file>", file=sys.stderr)
        return 2

    filepath = sys.argv[1]
    try:
        total_count, failed_count = process_file(filepath)
    except OSError as e:
        print(f"Error reading file '{filepath}': {e}", file=sys.stderr)
        return 2

    passed_count = total_count - failed_count

    print(f"\nChecked {total_count} records: {passed_count} passed, {failed_count} failed.")  

    if (failed_count == 0):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())