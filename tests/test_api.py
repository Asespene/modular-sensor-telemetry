from pathlib import Path
from fastapi.testclient import TestClient

import json

from backend import app as app_module

#initialize a raw payload data to use for testing our endpoint call operations
def make_payload(**override) -> dict:
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
    }

    base.update(override)
    return base


def test_get_latest_empty_db(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "api-test.db"

    #allows us to use a api_test.db rather than our main one telemetry.db for testing since we don't want to use our main db for testing
    #use the functions in app.py directed towards our test db, so at app_module which is app.py, we change the value of DB_PATH which is used in our functions with our testing db for tests
    monkeypatch.setattr(app_module, "DB_PATH", db_file)

    #allows us to start the app.py program in a testing scope, paired with the loc above. We run the app.py with a temp db. app_module.app is the FastAPI class instance which is the server and the client represents a testing instance where we can call api operations
    #since it allows us to create a testing scope for our api endpoints at app.py
    with TestClient(app_module.app) as client:
        response = client.get("/devices/node-01/sensors/pot-01/latest")

        assert response.status_code == 404


#unknown devices/sensors telemetry fetch
#tests a populated db with an invalid endpoint path for device/sensors since it tells us that our fetch endpoint works
def test_fetch_latest_unknown(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "api-test.db"

    monkeypatch.setattr(app_module, "DB_PATH", db_file)


    with TestClient(app_module.app) as client:
        client.post("/telemetry", json=make_payload())

        response = client.get("/devices/unknown-device/sensors/unknown-sensors/latest")

        #check if not found is the code since we tried requesting for an unknown device/sensors id
        assert response.status_code == 404


#tests invalid contract and broken json 
def test_contract_violation_and_broken_requests(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "api-test.db"

    monkeypatch.setattr(app_module, "DB_PATH", db_file)

    with TestClient(app_module.app) as client:
        #test telemetry contract violation, in this case out of bound value score
        response = client.post("/telemetry", json=make_payload(value=1024))
        #invalid contract, violates the ADC_MAX 
        assert response.status_code == 422

        #check if the response object contains errors
        assert len(response.json()['errors']) > 0
        
        #tests broken json format payload
        response = client.post("/telemetry", content="{bad", headers={"Content-Type": "application/json"})
        #broken JSON format, should be 400
        assert response.status_code == 400

        #test fetching a record, prove that the post requests failed so there would be no record
        response = client.get("/devices/node-01/sensors/pot-01/latest")

        assert response.status_code == 404



def test_post_get_valid_unavailable(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "api-test.db"

    monkeypatch.setattr(app_module, "DB_PATH", db_file)

    with TestClient(app_module.app) as client:
        #tests a valid post requests
        response = client.post("/telemetry", json=make_payload(quality="ok", value=0))
        #since this is a valid request it should return 201
        assert response.status_code == 201

        #verify that this post request was valid by fetching it
        response = client.get("/devices/node-01/sensors/pot-01/latest")

        #ensure that we fetched successfully
        assert response.status_code == 200

        #turn the response object body into a json file since we want to check and assert the contents of the payload that was inserted via posts requests
        data = response.json()

        assert data['quality'] == "ok"
        assert data['value'] == 0


        #now do this for the unavailable payload

        #first post test is unavailable but mismatch in value
        response = client.post("/telemetry", json=make_payload(quality="unavailable", value=1))
        #should be an error since its quality is unavailable but it has a value
        assert response.status_code == 422

        response = client.post("/telemetry", json=make_payload(quality="unavailable", value=None))

        #now this should be a valid unavailable post
        assert response.status_code == 201

        #lets fetch this unavailable record and check if it was successfully inserted into our db and can be fetched
        response = client.get("/devices/node-01/sensors/pot-01/latest")
        assert response.status_code == 200

        data = response.json()

        assert data['quality'] == "unavailable"
        assert data['value'] is None


#do a post request with 1 client instance then check the insertion occured with another client instance since we want to ensure that there is persistence across restart and different client instance
def test_persistence_across_restart(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "api-test.db"

    monkeypatch.setattr(app_module, "DB_PATH", db_file)

    with TestClient(app_module.app) as client1:
        response = client1.post("/telemetry", json=make_payload(value=100))

        assert response.status_code == 201

    with TestClient(app_module.app) as client2:
        response = client2.get("/devices/node-01/sensors/pot-01/latest")

        assert response.status_code == 200

        assert response.json()['value'] == 100


def test_uno_live_capture(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "api-test.db"

    fixture_path = Path(__file__).resolve().parent / "fixtures" / "uno-live-capture.ndjson"

    monkeypatch.setattr(app_module, "DB_PATH", db_file)

    with TestClient(app_module.app) as client:
        sent_count = 0
        last_record = None
        with open(fixture_path, "r", encoding="utf-8") as f:
            for line in f:
                #if its a blank line continue
                if (not line.strip()):
                    continue

                #any non-empty lines we parse and place inside as a json file(dict)
                record = json.loads(line)
                sent_count += 1

                #each record should be posted
                response = client.post("/telemetry", json=record)

                assert response.status_code == 201

                fetchLatestResponse = client.get("/devices/node-01/sensors/pot-01/latest")
                latestRecord = fetchLatestResponse.json()
                last_record = latestRecord

            #check if each line was sent 
            assert sent_count == 25

            #check and validate the lastRecord is the following values
            assert last_record['uptime_ms'] == 28561
            assert last_record['sequence'] == 24
            assert last_record['value'] == 1023




            


