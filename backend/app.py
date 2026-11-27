from datetime import datetime, timezone


from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from contextlib import asynccontextmanager

from backend.validation import validate_record
from backend.storage import DEFAULT_DB_PATH, init_db, insert_telemetry, get_latest_record

DB_PATH = DEFAULT_DB_PATH


@asynccontextmanager
#assigns a function as a manager for our backend, it will start  before we open up our server to ensure db is initialized and it will start again once we shutdown the server to clean up anything
#before yield is the initial setup and after yield is the cleanup, otherwise it pauses in the middle and allows the server to do its work
#takes our app instance
async def lifespan(app: FastAPI):
    init_db(DB_PATH)

    yield
    

#function call for our manager function once this is seen it runs the loc before yield
app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


#grabbing the raw JSON file of data, validate, the insert into our db
@app.post("/telemetry")
async def writeTelemetryRecord(request: Request):
    try:
        telemetryRecord = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON Format")

    errors = validate_record(telemetryRecord)

    #if errors is not empty meaning it contains errors
    if (errors):
        return JSONResponse(status_code=422, content={"detail": "Validation Failed!", "errors": errors})

    #the validated fields from the request sent at this time
    #if no error ecountered these are all the fields that passed
    accepted_record = {
        **telemetryRecord, 
        "received_at": datetime.now(timezone.utc).isoformat(),
    }

    #insert the validated and accepted record and of course the index of the row we just inserted
    latestRow = insert_telemetry(accepted_record, DB_PATH)

    
    return JSONResponse(status_code=201, content={"row_id": latestRow, "accepted_record": accepted_record})


#read door to our backend.
#fetch the latest record row of the specific sensor/device
@app.get("/devices/{device_id}/sensors/{sensor_id}/latest")
async def fetchLatestTelemtry(device_id: str, sensor_id: str) -> dict:
    latestRecord = get_latest_record(device_id, sensor_id, DB_PATH)

    if (not latestRecord):
        raise HTTPException(status_code=404, detail="Record Data Not Found!")

    return latestRecord

