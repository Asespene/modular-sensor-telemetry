from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from backend.validation import validate_record

app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/telemetry")
async def readTelemetry(request: Request):
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

    return JSONResponse(status_code=201, content=accepted_record)


    
