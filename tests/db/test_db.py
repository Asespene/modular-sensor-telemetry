from backend.storage import init_db, insert_telemetry, get_latest_record
from pathlib import Path

#helper function for initializing record dict for testing!
def make_record(**override) -> dict:
    #if no paramaters this is the initial dict returned otherwise customize it by passing values you want
    base = {
        "schema_version": 1,
        "device_id": "node-01",
        "sequence": 0,
        "uptime_ms": 1500,
        "sensor_id": "pot-01",
        "sensor_type": "potentiometer",
        "metric": "raw_adc",
        "unit": "count",
        "quality": "ok",
        "value": 331,
        "received_at": "2026-11-24T22:00:00+00:00",
    }

    base.update(override)
    return base



def test_insert_fetch_record(tmp_path: Path) -> None:
    #create a tmp path to a testing db file
    db_path = tmp_path / "test_telemetry.db"

    init_db(db_path)

    #createa a testing data to use for the insert
    record = make_record()

    
    #the inserted record should be at index row 1
    latestRow = insert_telemetry(record, db_path)

    assert latestRow == 1

    latestDict = get_latest_record("node-01", "pot-01", db_path)

    #check if the latest dictionary or record we just inputted is the same dict
    assert latestDict == record
    #check if the returned dict failed
    assert latestDict is not None

    #check what type is the key value
    assert type(latestDict['value']) is int

    #query an unknown db
    unknownDict = get_latest_record("node-02", "pot-02", db_path)

    assert unknownDict is None

    #prove order by id beats high sequence or uptime
    newRecord1 = make_record(sequence=10, uptime_ms=15000, value=800)
    newRecord2 = make_record(sequence=0, uptime_ms=100, value=34)

    insert_telemetry(newRecord1, db_path)
    insert_telemetry(newRecord2, db_path)

    latestDict = get_latest_record("node-01", "pot-01", db_path)
    #despite the first new record having a bigger uptime or sequence value it all comes down to the id number
    assert latestDict['value'] == 34



def test_insert_fetch_unavailable_record(tmp_path: Path) -> None:

    db_path = tmp_path / "test_telemetry.db"

    init_db(db_path)

    available_record = make_record()
    unavailable_record = make_record(quality="unavailable", value=None)

    firstRecord = insert_telemetry(unavailable_record, db_path)

    assert firstRecord == 1

    latestDict = get_latest_record("node-01", "pot-01", db_path)

    assert latestDict['quality'] == "unavailable"

    #print(repr(latestDict['value']))
    assert latestDict['value'] is None

    #add a second record

    secondRecord = insert_telemetry(available_record, db_path)

    latestDict = get_latest_record("node-01", "pot-01", db_path)

    #must be the second record in the dict
    assert latestDict['quality'] == 'ok'
    assert latestDict['value'] is not None

    insert_telemetry(available_record, db_path)
    insert_telemetry(unavailable_record, db_path)

    latestDict = get_latest_record("node-01", "pot-01", db_path)

    assert latestDict['quality'] == "unavailable"
    assert latestDict['value'] is None




def test_isolate_different_sensors(tmp_path: Path) -> None:
    db_path = tmp_path / "test_telemetry.db"

    init_db(db_path)

    sensor1 = make_record()
    sensor2 = make_record(sensor_id="pot-02", quality="unavailable", value=None)

    #different device_id test
    sensor3 = make_record(device_id="node-02", sensor_id="pot-01", quality="unavailable", value=None)

    
    insert_telemetry(sensor1, db_path)
    insert_telemetry(sensor2, db_path)
    insert_telemetry(sensor3, db_path)

    #fetch the first record sensor data
    sensor1Record = get_latest_record("node-01", "pot-01", db_path)
    sensor2Record = get_latest_record("node-01", "pot-02", db_path)
    sensor3Record = get_latest_record("node-02", "pot-01", db_path)

    #check if the first sensor record is the first pot
    assert sensor1Record['quality'] == "ok"

    #vice versa with sensor2
    assert sensor2Record['quality'] == "unavailable"

    #check if each record is actually distinct due to the difference in sensor_id
    assert sensor1Record == sensor1
    assert sensor2Record == sensor2


    assert sensor3Record == sensor3
    #sensor3 which has the same sensor id but has different device has quality unavailable
    #sensor1 has quality has ok, so different device should mean they are not the same and we have 3 distinct rows
    assert sensor3Record['quality'] != sensor1Record['quality']


def test_unknown_device_or_sensors(tmp_path: Path) -> None:
    db_path = tmp_path / "test_telemetry.db"

    init_db(db_path)

    record = make_record()

    insert_telemetry(record, db_path)

    latestDict = get_latest_record("unknown_device", "unknown_sensor", db_path)

    #since we have an unknown device or sensor id it should return none
    assert latestDict is None


def test_persistence_across_reopen(tmp_path: Path) -> None:
    db_path = tmp_path / "test_telemtry.db"

    init_db(db_path)

    record = make_record()

    insert_telemetry(record, db_path)

    init_db(db_path)

    assert db_path.exists() is True

    latestDict = get_latest_record("node-01", "pot-01", db_path)

    assert record == latestDict