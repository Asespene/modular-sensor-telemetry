import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.validation import validate_record


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